from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import BasePermission
from django.http import HttpRequest
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class GuestTokenPermission(BasePermission):
    """
    Custom permission class for guest token validation.
    Validates the guest response token without requiring authentication.
    """

    def has_permission(self, request: HttpRequest, view) -> bool:
        if request.method == 'GET':
            return True  # Allow GET requests to view activity details

        # For POST requests, validate the token exists and is valid
        token = request.query_params.get('token') or request.data.get('token')
        if not token:
            logger.warning(f"Guest response attempt without token from IP: {request.META.get('REMOTE_ADDR')}")
            return False

        try:
            # Check if token corresponds to an active activity
            from .models import IcebreakerActivity
            activity = IcebreakerActivity.objects.get(guest_response_token=token, is_active=True)
            # Store activity in request for later use to avoid duplicate queries
            request._guest_activity = activity
            return True
        except IcebreakerActivity.DoesNotExist:
            logger.warning(f"Invalid guest token attempted from IP: {request.META.get('REMOTE_ADDR')}")
            return False
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth.models import User
from django.db.models import Q, Count, Max, Prefetch
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
# Force reload to clear cache

from .models import (
    Message, Announcement, AnnouncementRead, ForumThread, ForumPost,
    QAQuestion, QAAnswer, IcebreakerActivity, IcebreakerResponse,
    NotificationPreference, UserGamificationProfile, ResponseReaction,
    IcebreakerAchievement, UserIcebreakerAchievement
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

            if other_user and other_user.id not in seen_users:
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
        # Get activity directly, bypassing queryset filtering
        try:
            activity = IcebreakerActivity.objects.get(id=pk)
        except IcebreakerActivity.DoesNotExist:
            return Response({'error': 'Activity not found'}, status=404)

        # Check if user is the event creator (same access control as leaderboard)
        if activity.event.owner != request.user:
            return Response({'error': 'Only event creators can view responses'}, status=403)

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

        # Only check start time if it's more than 1 day in the future (allow testing)
        if activity.starts_at and (activity.starts_at - now).days > 1:
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

    @action(detail=False, methods=['get', 'post'], permission_classes=[GuestTokenPermission])
    def guest_response(self, request: HttpRequest) -> Response:
        """
        Public endpoint for guest responses using token.
        Secured with custom permission class and token validation.
        """
        token = request.query_params.get('token') or request.data.get('token')

        if not token:
            logger.warning(f"Guest response attempt without token from IP: {request.META.get('REMOTE_ADDR')}")
            return Response({'error': 'Token required'}, status=400)

        # Use cached activity from permission class to avoid duplicate queries
        activity = getattr(request, '_guest_activity', None)
        if not activity:
            try:
                activity = IcebreakerActivity.objects.get(guest_response_token=token, is_active=True)
            except IcebreakerActivity.DoesNotExist:
                logger.warning(f"Invalid guest token {token[:8]}... from IP: {request.META.get('REMOTE_ADDR')}")
                return Response({'error': 'Invalid or expired token'}, status=404)

        if request.method == 'GET':
            # Return activity details for guest response page
            serializer = IcebreakerActivitySerializer(activity, context={'request': request})
            return Response(serializer.data)

        elif request.method == 'POST':
            # Handle guest response submission with validation
            guest_email = request.data.get('guest_email', '').strip()
            guest_name = request.data.get('guest_name', '').strip()
            response_data = request.data.get('response_data', {})

            # Validate required fields
            if not guest_name:
                logger.info(f"Guest response missing name for activity {activity.id}")
                return Response({'error': 'Guest name required'}, status=400)

            if len(guest_name) > 100:  # Reasonable limit
                return Response({'error': 'Guest name too long (max 100 characters)'}, status=400)

            if not response_data:
                return Response({'error': 'Response data required'}, status=400)

            # Check if guest already responded (unless multiple responses allowed)
            if not activity.allow_multiple_responses:
                existing_response = IcebreakerResponse.objects.filter(
                    activity=activity,
                    guest_name=guest_name,
                    is_guest_response=True
                ).first()
                if existing_response:
                    return Response({'error': 'You have already responded to this activity'}, status=400)

            # Check time bounds
            now = timezone.now()
            if activity.ends_at and now > activity.ends_at:
                return Response({'error': 'This activity has ended'}, status=400)
            # Only check start time if it's more than 1 day in the future (allow testing)
            if activity.starts_at and (activity.starts_at - now).days > 1:
                return Response({'error': 'This activity has not started yet'}, status=400)

            # Create guest response
            response = IcebreakerResponse.objects.create(
                activity=activity,
                guest_email=guest_email or '',
                guest_name=guest_name,
                response_data=response_data,
                is_guest_response=True,
                is_public=not activity.anonymous_responses,
            )

            # Calculate points and create/update gamification profile for guest
            response.calculate_points()

            # Update activity response count
            activity.response_count = activity.responses.count()
            activity.save(update_fields=['response_count'])

            logger.info(f"Guest response submitted successfully for activity {activity.id} by {guest_name}")
            serializer = IcebreakerResponseSerializer(response, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Auto-generate icebreaker activities from templates"""
        from events.models import Event
        from .icebreaker_templates import (
            get_template_pack, get_smart_pack, calculate_schedule_dates
        )
        from .email_utils import send_icebreaker_invitations

        event_id = request.data.get('event_id')
        pack_type = request.data.get('pack_type', 'smart_pack')
        auto_schedule = request.data.get('auto_schedule', True)
        auto_send = request.data.get('auto_send', False)
        preview_only = request.data.get('preview_only', False)

        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=404)

        # Check permission
        if event.owner != request.user:
            return Response({'error': 'Only event owner can generate icebreakers'}, status=403)

        # Get appropriate template pack
        if pack_type == 'smart_pack':
            templates = get_smart_pack(event)
        else:
            templates = get_template_pack(pack_type)

        # Calculate schedule dates if auto-scheduling
        if auto_schedule:
            templates = calculate_schedule_dates(event.date, templates)

        # If preview only, return the templates without creating
        if preview_only:
            return Response({
                'preview': True,
                'activities': templates,
                'count': len(templates)
            })

        # Create activities
        created_activities = []
        with transaction.atomic():
            for template in templates:
                # Remove schedule info from template before creating
                schedule_info = template.pop('schedule_days_before', None)
                starts_at = template.pop('starts_at', None)

                activity = IcebreakerActivity.objects.create(
                    event=event,
                    creator=request.user,
                    title=template['title'],
                    description=template['description'],
                    activity_type=template['activity_type'],
                    activity_data=template['activity_data'],
                    points_reward=template.get('points_reward', 10),
                    is_featured=template.get('is_featured', False),
                    is_active=True,
                    starts_at=starts_at,
                    anonymous_responses=False,
                    allow_multiple_responses=False,
                    send_email_on_create=False  # We'll handle this manually
                )
                created_activities.append(activity)

        # Send email for the first activity if auto_send is enabled
        if auto_send and created_activities:
            # Send the first icebreaker immediately
            first_activity = created_activities[0]
            try:
                send_icebreaker_invitations(first_activity)
                first_activity.email_sent = True
                first_activity.email_sent_at = timezone.now()
                first_activity.save(update_fields=['email_sent', 'email_sent_at'])
            except Exception as e:
                # Log error but don't fail the whole operation
                print(f"Failed to send icebreaker email: {e}")

        # Serialize created activities
        serialized_activities = [
            IcebreakerActivitySerializer(activity, context={'request': request}).data
            for activity in created_activities
        ]

        return Response({
            'created': len(created_activities),
            'activities': serialized_activities,
            'auto_sent': auto_send and len(created_activities) > 0
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def template_packs(self, request):
        """Get available template pack options"""
        packs = [
            {
                'id': 'smart_pack',
                'name': '✨ Smart Pack',
                'description': 'AI-powered selection based on your event type',
                'icon': '🤖'
            },
            {
                'id': 'corporate',
                'name': '🏢 Corporate',
                'description': 'Professional icebreakers for business events',
                'icon': '💼'
            },
            {
                'id': 'social',
                'name': '🎉 Social',
                'description': 'Fun activities for parties and social gatherings',
                'icon': '🎊'
            },
            {
                'id': 'conference',
                'name': '🎤 Conference',
                'description': 'Engage attendees at conferences and summits',
                'icon': '📊'
            },
            {
                'id': 'networking',
                'name': '🤝 Networking',
                'description': 'Foster connections at networking events',
                'icon': '🔗'
            },
            {
                'id': 'team_building',
                'name': '👥 Team Building',
                'description': 'Strengthen team bonds and collaboration',
                'icon': '🎯'
            }
        ]
        return Response(packs)

    @action(detail=False, methods=['get'])
    def leaderboard(self, request):
        """Get leaderboard for icebreaker activities"""
        event_id = request.query_params.get('event_id')

        if not event_id:
            return Response({'error': 'event_id parameter required'}, status=400)

        # Check if user is the event creator
        try:
            from events.models import Event
            event = Event.objects.get(id=event_id)
            if event.owner != request.user:
                return Response({'error': 'Only event creators can view leaderboards'}, status=403)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=404)

        # Get all user profiles for this event, ordered by points
        profiles = UserGamificationProfile.objects.filter(
            event_id=event_id
        ).select_related('user').order_by('-total_points', '-longest_streak')

        leaderboard_data = []
        for rank, profile in enumerate(profiles, 1):
            if profile.user:
                # Authenticated user
                user_data = {
                    'id': profile.user.id,
                    'username': profile.user.username,
                    'full_name': profile.user.get_full_name(),
                    'first_name': profile.user.first_name,
                    'last_name': profile.user.last_name,
                }
            else:
                # Guest user
                user_data = {
                    'id': f'guest_{profile.id}',
                    'username': profile.guest_email or f'guest_{profile.id}',
                    'full_name': profile.guest_name or profile.guest_email or 'Guest User',
                    'first_name': profile.guest_name.split(' ')[0] if profile.guest_name else 'Guest',
                    'last_name': profile.guest_name.split(' ', 1)[1] if profile.guest_name and ' ' in profile.guest_name else '',
                }

            leaderboard_data.append({
                'rank': rank,
                'user': user_data,
                'total_points': profile.total_points,
                'base_points': profile.base_points,
                'bonus_points': profile.bonus_points,
                'activities_completed': profile.activities_completed,
                'current_streak': profile.current_streak,
                'longest_streak': profile.longest_streak,
                'likes_received': profile.likes_received,
                'lucky_bonus_count': profile.lucky_bonus_count,
                'average_response_time': profile.average_response_time,
            })

        return Response({
            'leaderboard': leaderboard_data,
            'total_participants': len(leaderboard_data)
        })

    @action(detail=False, methods=['get'])
    def user_stats(self, request):
        """Get current user's gamification stats"""
        event_id = request.query_params.get('event_id')

        if not event_id:
            return Response({'error': 'event_id parameter required'}, status=400)

        # Check if user is the event creator
        try:
            from events.models import Event
            event = Event.objects.get(id=event_id)
            if event.owner != request.user:
                return Response({'error': 'Only event creators can view user statistics'}, status=403)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=404)

        try:
            profile = UserGamificationProfile.objects.get(
                user=request.user,
                event_id=event_id
            )

            # Get user's rank
            higher_ranked = UserGamificationProfile.objects.filter(
                event_id=event_id,
                total_points__gt=profile.total_points
            ).count()
            rank = higher_ranked + 1

            return Response({
                'rank': rank,
                'total_points': profile.total_points,
                'base_points': profile.base_points,
                'bonus_points': profile.bonus_points,
                'activities_completed': profile.activities_completed,
                'current_streak': profile.current_streak,
                'longest_streak': profile.longest_streak,
                'likes_received': profile.likes_received,
                'likes_given': profile.likes_given,
                'lucky_bonus_count': profile.lucky_bonus_count,
                'total_lucky_points': profile.total_lucky_points,
                'average_response_time': profile.average_response_time,
                'streak_multiplier': profile.get_streak_multiplier(),
            })
        except UserGamificationProfile.DoesNotExist:
            return Response({
                'rank': 0,
                'total_points': 0,
                'message': 'No activity yet'
            })

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

    @action(detail=True, methods=['post'])
    def react(self, request, pk=None):
        """Add a reaction to an icebreaker response"""
        response = self.get_object()
        reaction_type = request.data.get('reaction_type', 'like')

        # Valid reaction types
        valid_reactions = [choice[0] for choice in ResponseReaction.REACTION_TYPES]
        if reaction_type not in valid_reactions:
            return Response({'error': 'Invalid reaction type'}, status=400)

        # Get or create/update the reaction
        reaction, created = ResponseReaction.objects.get_or_create(
            response=response,
            user=request.user,
            defaults={'reaction_type': reaction_type}
        )

        if not created:
            # Update existing reaction
            if reaction.reaction_type == reaction_type:
                # Same reaction - remove it (toggle off)
                reaction.delete()
                response.like_count = response.reactions.count()
                response.save(update_fields=['like_count'])
                return Response({'message': 'Reaction removed'})
            else:
                # Different reaction - update it
                reaction.reaction_type = reaction_type
                reaction.save()

        # Update response like count and recalculate points
        old_like_count = response.like_count
        response.like_count = response.reactions.count()

        # Recalculate points with new social engagement
        response.calculate_points(save=True)
        response.save(update_fields=['like_count'])

        # Update user's gamification profile
        if response.user and response.user != request.user:
            profile, _ = UserGamificationProfile.objects.get_or_create(
                user=response.user,
                event=response.activity.event
            )
            profile.likes_received = profile.likes_received - old_like_count + response.like_count
            profile.save(update_fields=['likes_received'])

        # Update reactor's profile
        reactor_profile, _ = UserGamificationProfile.objects.get_or_create(
            user=request.user,
            event=response.activity.event
        )
        reactor_profile.likes_given += 1
        reactor_profile.save(update_fields=['likes_given'])

        return Response({
            'message': 'Reaction added',
            'reaction_type': reaction_type,
            'total_reactions': response.like_count,
            'points_earned': response.points_earned
        })

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
