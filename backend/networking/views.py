from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta, date
import logging

from .models import NetworkingProfile, Connection, NetworkingInteraction, EventNetworkingSettings
from .serializers import (
    NetworkingProfileSerializer, NetworkingProfileCreateSerializer,
    AttendeeDirectorySerializer, ConnectionSerializer, ConnectionCreateSerializer,
    NetworkingInteractionSerializer, QRContactSerializer, EventNetworkingSettingsSerializer,
    NetworkingStatsSerializer
)
from events.models import Event

logger = logging.getLogger(__name__)


class NetworkingProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for managing networking profiles"""
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return NetworkingProfileCreateSerializer
        return NetworkingProfileSerializer
    
    def get_queryset(self):
        return NetworkingProfile.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # Ensure one profile per user
        if NetworkingProfile.objects.filter(user=self.request.user).exists():
            raise serializers.ValidationError("User already has a networking profile")
        serializer.save()
    
    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        """Get or create current user's networking profile"""
        profile, created = NetworkingProfile.objects.get_or_create(
            user=request.user,
            defaults={
                'company': getattr(request.user, 'company', ''),
                'visible_in_directory': True,
                'allow_contact_sharing': True
            }
        )
        
        serializer = self.get_serializer(profile)
        return Response(serializer.data)


class AttendeeDirectoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for browsing attendee directory"""
    serializer_class = AttendeeDirectorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        event_id = self.request.query_params.get('event')
        if not event_id:
            return NetworkingProfile.objects.none()
        
        # Get event and check networking is enabled
        event = get_object_or_404(Event, id=event_id)
        settings = getattr(event, 'networking_settings', None)
        
        if not settings or not settings.enable_attendee_directory:
            return NetworkingProfile.objects.none()
        
        # Get attendees who are visible and invited to this event
        # Note: Show all invited users, not just those who have attended, 
        # to enable messaging between all event invitees
        queryset = NetworkingProfile.objects.filter(
            visible_in_directory=True,
            user__invitations__event=event
        ).select_related('user').distinct()
        
        # Apply filters
        company = self.request.query_params.get('company')
        industry = self.request.query_params.get('industry')
        interests = self.request.query_params.getlist('interests')
        
        if company and settings.allow_company_filter:
            queryset = queryset.filter(company__icontains=company)
        
        if industry and settings.allow_industry_filter:
            queryset = queryset.filter(industry__icontains=industry)
        
        if interests and settings.allow_interest_filter:
            # Filter by interests (JSON field contains any of the specified interests)
            interest_query = Q()
            for interest in interests:
                interest_query |= Q(interests__icontains=interest)
            queryset = queryset.filter(interest_query)
        
        # Exclude current user
        queryset = queryset.exclude(user=self.request.user)
        
        return queryset


class ConnectionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing networking connections"""
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ConnectionCreateSerializer
        return ConnectionSerializer
    
    def get_queryset(self):
        user = self.request.user
        event_id = self.request.query_params.get('event')
        
        # Get connections where user is either from_user or to_user
        queryset = Connection.objects.filter(
            Q(from_user=user) | Q(to_user=user)
        ).select_related('from_user', 'to_user', 'event')
        
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        
        return queryset.distinct()
    
    @action(detail=False, methods=['post'])
    def scan_qr(self, request):
        """Create connection via QR code scan"""
        serializer = QRContactSerializer(data=request.data)
        if serializer.is_valid():
            try:
                connection = serializer.create_connection(request.user)
                
                # Log the interaction
                NetworkingInteraction.objects.create(
                    user=request.user,
                    target_user=connection.to_user,
                    event=connection.event,
                    interaction_type='qr_scan',
                    interaction_data={'connection_id': str(connection.id)}
                )
                
                response_data = ConnectionSerializer(connection).data
                response_data['message'] = f"Connected with {connection.to_user.get_full_name() or connection.to_user.username}!"
                
                logger.info(f"QR connection created: {connection.from_user.username} → {connection.to_user.username}")
                return Response(response_data, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                logger.error(f"QR scan connection failed: {str(e)}")
                return Response({'error': 'Connection failed. You may already be connected.'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def my_connections(self, request):
        """Get user's connections with stats"""
        event_id = request.query_params.get('event')
        connections = self.get_queryset()
        
        if event_id:
            connections = connections.filter(event_id=event_id)
        
        # Get connection stats
        total_connections = connections.count()
        recent_connections = connections.filter(
            connected_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        connection_methods = connections.values('connection_method').annotate(
            count=Count('connection_method')
        )
        
        serializer = self.get_serializer(connections, many=True)
        
        return Response({
            'connections': serializer.data,
            'stats': {
                'total': total_connections,
                'recent': recent_connections,
                'methods': {item['connection_method']: item['count'] for item in connection_methods}
            }
        })


class NetworkingInteractionViewSet(viewsets.ModelViewSet):
    """ViewSet for tracking networking interactions"""
    serializer_class = NetworkingInteractionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return NetworkingInteraction.objects.filter(user=self.request.user)


class EventNetworkingSettingsViewSet(viewsets.ModelViewSet):
    """ViewSet for managing event networking settings"""
    serializer_class = EventNetworkingSettingsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return EventNetworkingSettings.objects.all()
        # Users can only manage settings for their own events
        return EventNetworkingSettings.objects.filter(event__owner=user)


class NetworkingStatsViewSet(viewsets.ViewSet):
    """ViewSet for networking statistics and analytics"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get networking dashboard stats"""
        user = request.user
        event_id = request.query_params.get('event')
        
        # Base queries
        connections_query = Connection.objects.filter(
            Q(from_user=user) | Q(to_user=user)
        )
        
        if event_id:
            connections_query = connections_query.filter(event_id=event_id)
        
        # Calculate stats
        total_connections = connections_query.count()
        today = timezone.now().date()
        new_connections_today = connections_query.filter(connected_at__date=today).count()
        
        # Most active events
        event_connections = connections_query.values('event__name').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # Connection methods breakdown
        method_breakdown = connections_query.values('connection_method').annotate(
            count=Count('connection_method')
        )
        
        # Points earned from networking
        networking_points = sum(connections_query.values_list('points_awarded', flat=True))
        
        return Response({
            'total_connections': total_connections,
            'new_connections_today': new_connections_today,
            'most_active_events': list(event_connections),
            'connection_methods': {item['connection_method']: item['count'] for item in method_breakdown},
            'points_earned': networking_points,
        })
