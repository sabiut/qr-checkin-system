import json
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Message, Announcement, ForumThread, ForumPost, QAQuestion
from .serializers import MessageSerializer, UserBasicSerializer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.event_id = self.scope['url_route']['kwargs']['event_id']
        self.room_group_name = f'chat_{self.event_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection',
            'message': 'Connected to chat'
        }))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'chat_message':
                await self.handle_chat_message(text_data_json)
            elif message_type == 'message_read':
                await self.handle_message_read(text_data_json)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))

    async def handle_chat_message(self, data):
        user = self.scope['user']
        if not user.is_authenticated:
            return
        
        content = data.get('message', '').strip()
        recipient_id = data.get('recipient_id')
        
        if not content or not recipient_id:
            return
        
        # Create message in database
        message = await self.create_message(user, recipient_id, content)
        
        if message:
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': await self.serialize_message(message),
                    'sender_id': user.id
                }
            )

    async def handle_message_read(self, data):
        user = self.scope['user']
        if not user.is_authenticated:
            return
        
        message_id = data.get('message_id')
        if message_id:
            await self.mark_message_read(user, message_id)

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender_id': event['sender_id']
        }))

    @database_sync_to_async
    def create_message(self, sender, recipient_id, content):
        try:
            from events.models import Event
            recipient = User.objects.get(id=recipient_id)
            event = Event.objects.get(id=self.event_id)
            
            message = Message.objects.create(
                sender=sender,
                recipient=recipient,
                event=event,
                content=content
            )
            return message
        except (User.DoesNotExist, Event.DoesNotExist):
            return None

    @database_sync_to_async
    def serialize_message(self, message):
        serializer = MessageSerializer(message)
        return serializer.data

    @database_sync_to_async
    def mark_message_read(self, user, message_id):
        try:
            message = Message.objects.get(id=message_id, recipient=user)
            message.mark_as_read()
        except Message.DoesNotExist:
            pass


class AnnouncementConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.event_id = self.scope['url_route']['kwargs']['event_id']
        self.room_group_name = f'announcements_{self.event_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if data.get('type') == 'announcement_read':
                await self.handle_announcement_read(data)
        except json.JSONDecodeError:
            pass

    async def handle_announcement_read(self, data):
        user = self.scope['user']
        if not user.is_authenticated:
            return
        
        announcement_id = data.get('announcement_id')
        if announcement_id:
            await self.mark_announcement_read(user, announcement_id)

    async def announcement_message(self, event):
        # Send announcement to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'announcement',
            'announcement': event['announcement']
        }))

    @database_sync_to_async
    def mark_announcement_read(self, user, announcement_id):
        try:
            from .models import AnnouncementRead
            announcement = Announcement.objects.get(id=announcement_id)
            AnnouncementRead.objects.get_or_create(
                user=user,
                announcement=announcement
            )
        except Announcement.DoesNotExist:
            pass


class ForumConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.thread_id = self.scope['url_route']['kwargs']['thread_id']
        self.room_group_name = f'forum_{self.thread_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if data.get('type') == 'new_post':
                await self.handle_new_post(data)
        except json.JSONDecodeError:
            pass

    async def handle_new_post(self, data):
        user = self.scope['user']
        if not user.is_authenticated:
            return
        
        content = data.get('content', '').strip()
        if not content:
            return
        
        post = await self.create_forum_post(user, content)
        if post:
            # Broadcast new post to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'forum_post',
                    'post': await self.serialize_post(post)
                }
            )

    async def forum_post(self, event):
        # Send new post to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'new_post',
            'post': event['post']
        }))

    @database_sync_to_async
    def create_forum_post(self, author, content):
        try:
            thread = ForumThread.objects.get(id=self.thread_id)
            post = ForumPost.objects.create(
                thread=thread,
                author=author,
                content=content
            )
            return post
        except ForumThread.DoesNotExist:
            return None

    @database_sync_to_async
    def serialize_post(self, post):
        from .serializers import ForumPostSerializer
        serializer = ForumPostSerializer(post)
        return serializer.data


class QAConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.event_id = self.scope['url_route']['kwargs']['event_id']
        self.room_group_name = f'qa_{self.event_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'upvote_question':
                await self.handle_upvote(data)
            elif message_type == 'new_answer':
                await self.handle_new_answer(data)
        except json.JSONDecodeError:
            pass

    async def handle_upvote(self, data):
        user = self.scope['user']
        if not user.is_authenticated:
            return
        
        question_id = data.get('question_id')
        if question_id:
            updated_question = await self.upvote_question(user, question_id)
            if updated_question:
                # Broadcast upvote update
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'question_updated',
                        'question_id': question_id,
                        'upvotes': updated_question['upvotes']
                    }
                )

    async def question_updated(self, event):
        # Send question update to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'question_updated',
            'question_id': event['question_id'],
            'upvotes': event['upvotes']
        }))

    @database_sync_to_async
    def upvote_question(self, user, question_id):
        try:
            question = QAQuestion.objects.get(id=question_id)
            if question.author != user:  # Can't upvote own question
                question.upvotes += 1
                question.save()
                return {'upvotes': question.upvotes}
        except QAQuestion.DoesNotExist:
            pass
        return None
