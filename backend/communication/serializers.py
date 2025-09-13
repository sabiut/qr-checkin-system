from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import Message, Announcement, ForumThread, ForumPost, QAQuestion, QAAnswer, IcebreakerActivity, IcebreakerResponse, NotificationPreference

class UserBasicSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'full_name']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username

class MessageSerializer(serializers.ModelSerializer):
    sender = UserBasicSerializer(read_only=True)
    recipient = UserBasicSerializer(read_only=True)
    recipient_id = serializers.IntegerField(write_only=True, required=False)
    recipient_email = serializers.EmailField(write_only=True, required=False)
    is_from_current_user = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()
    recipient_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'recipient', 'recipient_id', 'recipient_email', 'recipient_name', 
                  'event', 'content', 'status', 'created_at', 'is_from_current_user', 'time_ago']
        read_only_fields = ['id', 'sender', 'status', 'created_at', 'recipient_name']
    
    def get_is_from_current_user(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.sender == request.user
        return False
    
    def get_time_ago(self, obj):
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff < timedelta(minutes=1):
            return "just now"
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes}m ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours}h ago"
        elif diff < timedelta(days=7):
            days = diff.days
            return f"{days}d ago"
        else:
            return obj.created_at.strftime("%b %d, %Y")
    
    def get_recipient_name(self, obj):
        """Get recipient name from user or invitation"""
        if obj.recipient:
            return obj.recipient.get_full_name() or obj.recipient.username
        elif obj.recipient_invitation:
            return obj.recipient_invitation.guest_name
        return obj.recipient_email or "Unknown"
    
    def create(self, validated_data):
        from invitations.models import Invitation
        from .email_utils import send_message_email_to_guest
        
        validated_data['sender'] = self.context['request'].user
        recipient_id = validated_data.pop('recipient_id', None)
        recipient_email = validated_data.pop('recipient_email', None)
        
        # Try to send to a user with an account
        if recipient_id:
            try:
                validated_data['recipient'] = User.objects.get(id=recipient_id)
            except User.DoesNotExist:
                raise serializers.ValidationError("Recipient user not found")
        
        # Otherwise send to guest via email
        elif recipient_email:
            # Check if there's an invitation for this email and event
            event = validated_data.get('event')
            if event:
                try:
                    invitation = Invitation.objects.get(
                        guest_email=recipient_email,
                        event=event
                    )
                    validated_data['recipient_invitation'] = invitation
                    validated_data['recipient_email'] = recipient_email
                    validated_data['status'] = 'email_sent'
                    
                    # Create the message
                    message = super().create(validated_data)
                    
                    # Send email notification
                    email_sent = send_message_email_to_guest(
                        invitation=invitation,
                        sender=validated_data['sender'],
                        message_content=validated_data['content'],
                        event=event
                    )
                    
                    if email_sent:
                        print(f"Message saved to DB and email sent to {recipient_email}")
                    else:
                        print(f"Message saved to DB but email failed to {recipient_email}")
                    
                    return message
                    
                except Invitation.DoesNotExist:
                    raise serializers.ValidationError("No invitation found for this email address")
            else:
                raise serializers.ValidationError("Event is required for guest messaging")
        else:
            raise serializers.ValidationError("Either recipient_id or recipient_email is required")
        
        return super().create(validated_data)

class AnnouncementSerializer(serializers.ModelSerializer):
    author = UserBasicSerializer(read_only=True)
    time_ago = serializers.SerializerMethodField()
    is_read = serializers.SerializerMethodField()
    
    class Meta:
        model = Announcement
        fields = ['id', 'event', 'author', 'title', 'content', 'priority', 'announcement_type', 
                  'created_at', 'time_ago', 'is_read']
        read_only_fields = ['id', 'author', 'created_at']
    
    def create(self, validated_data):
        from .email_utils import send_announcement_to_all_invitees
        
        validated_data['author'] = self.context['request'].user
        validated_data['is_published'] = True  # Auto-publish when created via API
        
        # Create the announcement
        announcement = super().create(validated_data)
        
        # Send email notifications to all invitees
        try:
            sent_count = send_announcement_to_all_invitees(announcement, announcement.event)
            print(f"Announcement emails sent to {sent_count} invitees")
        except Exception as e:
            print(f"Failed to send announcement emails: {str(e)}")
            # Don't fail the announcement creation if email fails
        
        return announcement
    
    def get_time_ago(self, obj):
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff < timedelta(minutes=1):
            return "just now"
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes}m ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours}h ago"
        elif diff < timedelta(days=7):
            days = diff.days
            return f"{days}d ago"
        else:
            return obj.created_at.strftime("%b %d, %Y")
    
    def get_is_read(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.reads.filter(user=request.user).exists()
        return False

class ForumThreadSerializer(serializers.ModelSerializer):
    author = UserBasicSerializer(read_only=True)
    reply_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ForumThread
        fields = ['id', 'event', 'author', 'title', 'content', 'category', 'is_pinned', 'reply_count', 'created_at']
        read_only_fields = ['id', 'author', 'is_pinned', 'reply_count']
    
    def get_reply_count(self, obj):
        return obj.posts.count()
    
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)

class ForumPostSerializer(serializers.ModelSerializer):
    author = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = ForumPost
        fields = ['id', 'thread', 'author', 'content', 'created_at']
        read_only_fields = ['id', 'author']
    
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)

class QAAnswerSerializer(serializers.ModelSerializer):
    author = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = QAAnswer
        fields = ['id', 'question', 'author', 'answer', 'is_official', 'created_at']
        read_only_fields = ['id', 'author']
    
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)

class QAQuestionSerializer(serializers.ModelSerializer):
    author = UserBasicSerializer(read_only=True)
    answers = serializers.SerializerMethodField()
    
    class Meta:
        model = QAQuestion
        fields = ['id', 'event', 'author', 'question', 'session_name', 'status', 'upvotes', 'is_anonymous', 'created_at', 'answers']
        read_only_fields = ['id', 'author', 'upvotes', 'answers']
    
    def get_answers(self, obj):
        answers = obj.answers.all().order_by('-is_official', '-created_at')
        return QAAnswerSerializer(answers, many=True, context=self.context).data
    
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)

class IcebreakerActivitySerializer(serializers.ModelSerializer):
    creator = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = IcebreakerActivity
        fields = ['id', 'event', 'creator', 'title', 'description', 'activity_type', 'created_at']
        read_only_fields = ['id', 'creator']

class IcebreakerResponseSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = IcebreakerResponse
        fields = ['id', 'activity', 'user', 'response_data', 'created_at']
        read_only_fields = ['id', 'user']

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = ['notify_direct_messages', 'notify_announcements', 'notify_forum_replies']
