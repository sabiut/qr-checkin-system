from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth.models import User
from django.db.models import Q, Count, Max, Prefetch
from django.utils import timezone
# Force reload to clear cache

from .models import (
    Message, Announcement, AnnouncementRead, ForumThread, ForumPost,
    QAQuestion, QAAnswer, IcebreakerActivity, IcebreakerResponse,
    NotificationPreference
)
from .serializers import (
    MessageSerializer, AnnouncementSerializer, ForumThreadSerializer,
    ForumPostSerializer, QAQuestionSerializer, QAAnswerSerializer,
    IcebreakerActivitySerializer, IcebreakerResponseSerializer,
    NotificationPreferenceSerializer, UserBasicSerializer
)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(
            Q(sender=user) | Q(recipient=user)
        ).select_related('sender', 'recipient', 'event').order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def conversations(self, request):
        user = request.user
        event_id = request.query_params.get('event_id')
        
        # Get unique conversations with latest message and unread counts
        conversations = []
        seen_users = set()
        
        # Filter by event if provided
        messages_query = Message.objects.filter(
            Q(sender=user) | Q(recipient=user)
        )
        if event_id:
            messages_query = messages_query.filter(event_id=event_id)
        
        messages = messages_query.select_related('sender', 'recipient').order_by('-created_at')
        
        for message in messages:
            other_user = message.recipient if message.sender == user else message.sender
            
            if other_user.id not in seen_users:
                seen_users.add(other_user.id)
                
                # Get unread count for this conversation
                unread_query = Message.objects.filter(
                    sender=other_user,
                    recipient=user,
                    read_at__isnull=True
                )
                if event_id:
                    unread_query = unread_query.filter(event_id=event_id)
                unread_count = unread_query.count()
                
                conversations.append({
                    'user': UserBasicSerializer(other_user).data,
                    'latest_message': MessageSerializer(message, context={'request': request}).data,
                    'unread_count': unread_count
                })
        
        return Response(conversations)
    
    @action(detail=False, methods=['get'])
    def with_user(self, request):
        other_user_id = request.query_params.get('user_id')
        event_id = request.query_params.get('event_id')
        
        if not other_user_id:
            return Response({'error': 'user_id parameter required'}, status=400)
        
        try:
            other_user = User.objects.get(id=other_user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)
        
        messages_query = Message.objects.filter(
            Q(sender=request.user, recipient=other_user) |
            Q(sender=other_user, recipient=request.user)
        )
        
        if event_id:
            messages_query = messages_query.filter(event_id=event_id)
            
        messages = messages_query.select_related('sender', 'recipient').order_by('-created_at')
        
        # Mark messages as read
        Message.objects.filter(
            sender=other_user,
            recipient=request.user,
            read_at__isnull=True
        ).update(read_at=timezone.now(), status='read')
        
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = MessageSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        message = self.get_object()
        if message.recipient == request.user:
            message.mark_as_read()
            return Response({'status': 'marked as read'})
        return Response({'error': 'Not authorized'}, status=403)
    
    @action(detail=False, methods=['get'])
    def event_attendees(self, request):
        """Get all users invited to an event for messaging purposes"""
        event_id = request.query_params.get('event_id')
        if not event_id:
            return Response({'error': 'event_id parameter required'}, status=400)
        
        from events.models import Event
        from invitations.models import Invitation
        from django.db import connection
        
        # Use raw SQL to avoid any ORM quirks with select_related
        attendees = []
        seen_emails = set()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT guest_email, guest_name 
                    FROM invitations_invitation 
                    WHERE event_id = %s 
                    AND guest_email IS NOT NULL 
                    AND guest_email != %s
                    AND guest_email != ''
                """, [event_id, request.user.email])
                
                invitation_rows = cursor.fetchall()
        except Exception as e:
            # Fallback to simple queryset approach without any optimizations
            try:
                invitation_data = list(Invitation.objects.filter(
                    event_id=event_id
                ).exclude(
                    guest_email=request.user.email
                ).values('guest_email', 'guest_name'))
                invitation_rows = [(row['guest_email'], row['guest_name']) for row in invitation_data]
            except Exception as e2:
                return Response({'error': f'Database error: {str(e2)}'}, status=500)
        
        for guest_email, guest_name in invitation_rows:
            # Skip duplicates
            if guest_email in seen_emails:
                continue
            seen_emails.add(guest_email)
            
            # Try to find associated user account
            try:
                user = User.objects.get(email=guest_email)
                attendees.append({
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'full_name': user.get_full_name() or guest_name,
                    'has_account': True
                })
            except User.DoesNotExist:
                # Guest without account - still show them
                attendees.append({
                    'id': None,
                    'username': guest_email.split('@')[0],  # Use email prefix as username
                    'email': guest_email,
                    'full_name': guest_name,
                    'has_account': False
                })
        
        return Response(attendees)

class AnnouncementViewSet(viewsets.ModelViewSet):
    serializer_class = AnnouncementSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'priority']
    ordering = ['-priority', '-created_at']
    
    def get_queryset(self):
        user = self.request.user
        event_id = self.request.query_params.get('event_id')
        
        queryset = Announcement.objects.filter(
            is_published=True
        )
        
        # Filter by specific event if provided
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        else:
            # Otherwise filter by events user is invited to
            queryset = queryset.filter(
                event__invitations__guest_email=user.email
            )
        
        queryset = queryset.select_related('author', 'event').prefetch_related('reads').distinct()
        
        # Filter by priority if specified
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by type if specified
        announcement_type = self.request.query_params.get('type')
        if announcement_type:
            queryset = queryset.filter(announcement_type=announcement_type)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        announcement = self.get_object()
        AnnouncementRead.objects.get_or_create(
            user=request.user,
            announcement=announcement
        )
        
        # Increment view count
        announcement.view_count += 1
        announcement.save(update_fields=['view_count'])
        
        return Response({'status': 'marked as read'})
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        user = request.user
        unread_announcements = self.get_queryset().exclude(
            reads__user=user
        )
        
        page = self.paginate_queryset(unread_announcements)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(unread_announcements, many=True)
        return Response(serializer.data)

# Simplified versions of other viewsets
class ForumThreadViewSet(viewsets.ModelViewSet):
    serializer_class = ForumThreadSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        event_id = self.request.query_params.get('event_id')
        queryset = ForumThread.objects.filter(is_hidden=False)
        
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        
        return queryset.select_related('author', 'event').order_by('-is_pinned', '-last_activity')

class ForumPostViewSet(viewsets.ModelViewSet):
    serializer_class = ForumPostSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ForumPost.objects.filter(is_hidden=False)

class QAQuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QAQuestionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        event_id = self.request.query_params.get('event_id')
        queryset = QAQuestion.objects.all()
        
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        
        return queryset.select_related('author', 'event').prefetch_related('answers__author').order_by('-upvotes', '-created_at')

class QAAnswerViewSet(viewsets.ModelViewSet):
    serializer_class = QAAnswerSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return QAAnswer.objects.all()

class IcebreakerActivityViewSet(viewsets.ModelViewSet):
    serializer_class = IcebreakerActivitySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'response_count', 'view_count']
    ordering = ['-is_featured', '-created_at']

    def get_queryset(self):
        user = self.request.user
        event_id = self.request.query_params.get('event_id')

        queryset = IcebreakerActivity.objects.filter(is_active=True)

        # Filter by specific event if provided
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        else:
            # Otherwise filter by events user is invited to
            queryset = queryset.filter(
                event__invitations__guest_email=user.email
            )

        queryset = queryset.select_related('creator', 'event').prefetch_related(
            Prefetch('responses', queryset=IcebreakerResponse.objects.select_related('user'))
        ).distinct()

        # Filter by activity type if specified
        activity_type = self.request.query_params.get('type')
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)

        # Filter by featured activities
        if self.request.query_params.get('featured') == 'true':
            queryset = queryset.filter(is_featured=True)

        # Filter by time - upcoming activities
        if self.request.query_params.get('upcoming') == 'true':
            now = timezone.now()
            queryset = queryset.filter(
                Q(starts_at__gt=now) | Q(starts_at__isnull=True)
            )

        return queryset

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        # Increment view count
        instance.view_count += 1
        instance.save(update_fields=['view_count'])

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def responses(self, request, pk=None):
        activity = self.get_object()
        responses = activity.responses.filter(is_public=True).select_related('user').order_by('-created_at')

        page = self.paginate_queryset(responses)
        if page is not None:
            serializer = IcebreakerResponseSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = IcebreakerResponseSerializer(responses, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        activity = self.get_object()

        # Check if activity is still active and within time bounds
        now = timezone.now()
        if activity.ends_at and now > activity.ends_at:
            return Response({'error': 'This activity has ended'}, status=400)

        if activity.starts_at and now < activity.starts_at:
            return Response({'error': 'This activity has not started yet'}, status=400)

        # Create response with activity context
        serializer = IcebreakerResponseSerializer(
            data={**request.data, 'activity': activity.id},
            context={'request': request}
        )

        if serializer.is_valid():
            response = serializer.save()

            # Update activity response count
            activity.response_count = activity.responses.count()
            activity.save(update_fields=['response_count'])

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def my_responses(self, request):
        user = request.user
        event_id = request.query_params.get('event_id')

        responses = IcebreakerResponse.objects.filter(user=user)
        if event_id:
            responses = responses.filter(activity__event_id=event_id)

        responses = responses.select_related('user', 'activity').order_by('-created_at')

        page = self.paginate_queryset(responses)
        if page is not None:
            serializer = IcebreakerResponseSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = IcebreakerResponseSerializer(responses, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get', 'post'], permission_classes=[])
    def guest_response(self, request):
        """Public endpoint for guest responses using token"""
        token = request.query_params.get('token') or request.data.get('token')

        if not token:
            return Response({'error': 'Token required'}, status=400)

        try:
            activity = IcebreakerActivity.objects.get(guest_response_token=token, is_active=True)
        except IcebreakerActivity.DoesNotExist:
            return Response({'error': 'Invalid or expired token'}, status=404)

        if request.method == 'GET':
            # Return activity details for guest response page
            serializer = IcebreakerActivitySerializer(activity, context={'request': request})
            return Response(serializer.data)

        elif request.method == 'POST':
            # Handle guest response submission
            guest_email = request.data.get('guest_email')
            guest_name = request.data.get('guest_name', '')
            response_data = request.data.get('response_data', {})

            if not guest_email:
                return Response({'error': 'Guest email required'}, status=400)

            # Check if guest already responded (unless multiple responses allowed)
            if not activity.allow_multiple_responses:
                existing_response = IcebreakerResponse.objects.filter(
                    activity=activity,
                    guest_email=guest_email,
                    is_guest_response=True
                ).first()
                if existing_response:
                    return Response({'error': 'You have already responded to this activity'}, status=400)

            # Check time bounds
            now = timezone.now()
            if activity.ends_at and now > activity.ends_at:
                return Response({'error': 'This activity has ended'}, status=400)
            if activity.starts_at and now < activity.starts_at:
                return Response({'error': 'This activity has not started yet'}, status=400)

            # Create guest response
            response = IcebreakerResponse.objects.create(
                activity=activity,
                guest_email=guest_email,
                guest_name=guest_name,
                response_data=response_data,
                is_guest_response=True,
                is_public=not activity.anonymous_responses,
                points_earned=0  # Guests don't earn points
            )

            # Update activity response count
            activity.response_count = activity.responses.count()
            activity.save(update_fields=['response_count'])

            serializer = IcebreakerResponseSerializer(response, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

class IcebreakerResponseViewSet(viewsets.ModelViewSet):
    serializer_class = IcebreakerResponseSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        activity_id = self.request.query_params.get('activity_id')

        queryset = IcebreakerResponse.objects.filter(is_public=True)

        if activity_id:
            queryset = queryset.filter(activity_id=activity_id)

        return queryset.select_related('user', 'activity').order_by('-created_at')

    def list(self, request, *args, **kwargs):
        # Only show public responses unless it's the user's own response
        queryset = self.get_queryset()
        user = request.user

        # Include user's own responses even if private
        own_responses = IcebreakerResponse.objects.filter(user=user)
        activity_id = request.query_params.get('activity_id')
        if activity_id:
            own_responses = own_responses.filter(activity_id=activity_id)

        # Combine public responses and user's own responses
        combined_queryset = (queryset.union(own_responses)
                           .select_related('user', 'activity')
                           .order_by('-created_at'))

        page = self.paginate_queryset(combined_queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(combined_queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        # This is handled through the activity respond endpoint
        pass

class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        obj, created = NotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return obj
    
    def list(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
