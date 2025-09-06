from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta
import logging

from .models import FeedbackTag, EventFeedback, FeedbackAnalytics
from .serializers import (
    FeedbackTagSerializer, EventFeedbackSerializer, 
    EventFeedbackCreateSerializer, FeedbackAnalyticsSerializer,
    QuickFeedbackSerializer, FeedbackSummarySerializer
)
from events.models import Event
from invitations.models import Invitation

logger = logging.getLogger(__name__)


class FeedbackTagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for feedback tags."""
    queryset = FeedbackTag.objects.all()
    serializer_class = FeedbackTagSerializer
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get tags organized by category."""
        categories = {}
        for tag in FeedbackTag.objects.all():
            if tag.category not in categories:
                categories[tag.category] = []
            categories[tag.category].append(FeedbackTagSerializer(tag).data)
        return Response(categories)


class EventFeedbackViewSet(viewsets.ModelViewSet):
    """ViewSet for event feedback."""
    queryset = EventFeedback.objects.all()
    serializer_class = EventFeedbackSerializer
    
    def get_permissions(self):
        """
        - Allow anyone to submit feedback (create)
        - Require authentication to view/edit feedback
        """
        if self.action == 'create' or self.action == 'quick_feedback':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """Use appropriate serializer for different actions."""
        if self.action == 'create':
            return EventFeedbackCreateSerializer
        return EventFeedbackSerializer
    
    def get_queryset(self):
        """Filter feedback based on user permissions."""
        user = self.request.user
        
        if not user.is_authenticated:
            return EventFeedback.objects.none()
        
        # Staff can see all feedback
        if user.is_staff:
            queryset = EventFeedback.objects.all()
        else:
            # Users can only see feedback for events they own
            queryset = EventFeedback.objects.filter(event__owner=user)
        
        # Filter by event if provided
        event_id = self.request.query_params.get('event_id')
        if event_id:
            queryset = queryset.filter(event_id=event_id)
            
        return queryset.select_related('event', 'invitation').prefetch_related('tags')
    
    def perform_create(self, serializer):
        """Handle feedback creation with gamification."""
        # Capture IP and user agent for analytics
        request = self.request
        ip_address = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        feedback = serializer.save(
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"Feedback submitted for event {feedback.event.name} by {feedback.respondent_email}")
        
        # Trigger analytics update
        self.update_analytics(feedback.event)
        
        return feedback
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def update_analytics(self, event):
        """Update or create analytics for the event."""
        try:
            analytics, created = FeedbackAnalytics.objects.get_or_create(event=event)
            
            feedback_qs = EventFeedback.objects.filter(event=event)
            
            # Update basic stats
            analytics.total_responses = feedback_qs.count()
            
            # Calculate response rate (feedback count / total invitations)
            total_invitations = event.invitations.count()
            if total_invitations > 0:
                analytics.response_rate = (analytics.total_responses / total_invitations) * 100
            
            # Calculate rating averages
            analytics.avg_overall_rating = feedback_qs.aggregate(
                avg=Avg('overall_rating')
            )['avg']
            analytics.avg_venue_rating = feedback_qs.aggregate(
                avg=Avg('venue_rating')
            )['avg']
            analytics.avg_content_rating = feedback_qs.aggregate(
                avg=Avg('content_rating')
            )['avg']
            analytics.avg_organization_rating = feedback_qs.aggregate(
                avg=Avg('organization_rating')
            )['avg']
            
            # Calculate NPS stats
            nps_feedback = feedback_qs.filter(nps_score__isnull=False)
            if nps_feedback.exists():
                analytics.avg_nps_score = nps_feedback.aggregate(avg=Avg('nps_score'))['avg']
                analytics.nps_detractors = nps_feedback.filter(nps_score__lte=6).count()
                analytics.nps_passives = nps_feedback.filter(nps_score__in=[7, 8]).count()
                analytics.nps_promoters = nps_feedback.filter(nps_score__gte=9).count()
                analytics.net_promoter_score = analytics.calculate_nps()
            
            # Count recommendations
            analytics.would_recommend_count = feedback_qs.filter(would_recommend=True).count()
            analytics.would_attend_future_count = feedback_qs.filter(would_attend_future=True).count()
            
            # Top tags analysis
            positive_tags = []
            negative_tags = []
            
            for feedback in feedback_qs.prefetch_related('tags'):
                for tag in feedback.tags.all():
                    tag_data = {'name': tag.name, 'icon': tag.icon}
                    if tag.is_positive:
                        positive_tags.append(tag_data)
                    else:
                        negative_tags.append(tag_data)
            
            # Count and get top tags
            from collections import Counter
            analytics.top_positive_tags = [
                {'name': name, 'count': count} 
                for name, count in Counter(tag['name'] for tag in positive_tags).most_common(5)
            ]
            analytics.top_negative_tags = [
                {'name': name, 'count': count} 
                for name, count in Counter(tag['name'] for tag in negative_tags).most_common(5)
            ]
            
            analytics.save()
            logger.info(f"Analytics updated for event {event.name}")
            
        except Exception as e:
            logger.error(f"Failed to update analytics for event {event.name}: {str(e)}")
    
    @action(detail=False, methods=['post'])
    def quick_feedback(self, request):
        """Quick feedback submission via QR code or simple form."""
        serializer = QuickFeedbackSerializer(data=request.data)
        if serializer.is_valid():
            try:
                feedback = serializer.save()
                logger.info(f"Quick feedback submitted for event {feedback.event.name}")
                return Response({
                    'message': 'Thank you for your feedback!',
                    'feedback_id': feedback.id
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({
                    'error': 'Failed to submit feedback. You may have already provided feedback for this event.'
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get analytics for events the user owns."""
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        event_id = request.query_params.get('event_id')
        if event_id:
            try:
                event = Event.objects.get(id=event_id)
                if not user.is_staff and event.owner != user:
                    return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
                
                analytics, created = FeedbackAnalytics.objects.get_or_create(event=event)
                serializer = FeedbackAnalyticsSerializer(analytics)
                return Response(serializer.data)
            except Event.DoesNotExist:
                return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Return analytics for all user's events
        if user.is_staff:
            events = Event.objects.all()
        else:
            events = Event.objects.filter(owner=user)
        
        analytics_data = []
        for event in events:
            analytics, created = FeedbackAnalytics.objects.get_or_create(event=event)
            analytics_data.append(FeedbackAnalyticsSerializer(analytics).data)
        
        return Response(analytics_data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get feedback summary for dashboard."""
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Get events with feedback in the last 30 days
        recent_date = timezone.now() - timedelta(days=30)
        
        if user.is_staff:
            events = Event.objects.all()
        else:
            events = Event.objects.filter(owner=user)
        
        events_with_feedback = events.filter(
            feedback_responses__submitted_at__gte=recent_date
        ).distinct()
        
        summary_data = []
        for event in events_with_feedback:
            feedback_qs = EventFeedback.objects.filter(event=event)
            total_feedback = feedback_qs.count()
            
            if total_feedback > 0:
                avg_rating = feedback_qs.aggregate(avg=Avg('overall_rating'))['avg']
                total_invitations = event.invitations.count()
                response_rate = (total_feedback / total_invitations * 100) if total_invitations > 0 else 0
                
                # NPS calculation
                nps_scores = feedback_qs.filter(nps_score__isnull=False)
                nps = None
                if nps_scores.exists():
                    detractors = nps_scores.filter(nps_score__lte=6).count()
                    promoters = nps_scores.filter(nps_score__gte=9).count()
                    total_nps = nps_scores.count()
                    if total_nps > 0:
                        nps = ((promoters - detractors) / total_nps) * 100
                
                summary_data.append({
                    'event_name': event.name,
                    'total_feedback': total_feedback,
                    'average_rating': round(avg_rating, 2) if avg_rating else None,
                    'response_rate': round(response_rate, 2),
                    'nps_score': round(nps, 2) if nps is not None else None,
                })
        
        return Response(summary_data)