from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db.models import Count, Q
from .models import (
    AttendeeProfile, Badge, UserBadge, Achievement, LeaderboardEntry
)
from .serializers import (
    AttendeeProfileSerializer, BadgeSerializer, UserBadgeSerializer,
    AchievementSerializer, UserStatsSerializer, LeaderboardSerializer
)
from .services import GamificationStatsService, LeaderboardService


class UserStatsView(generics.RetrieveAPIView):
    """Get comprehensive gamification stats for the current user"""
    serializer_class = UserStatsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        service = GamificationStatsService()
        return service.get_user_stats(self.request.user)


class UserBadgesView(generics.ListAPIView):
    """List all badges earned by the current user"""
    serializer_class = UserBadgeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserBadge.objects.filter(
            user=self.request.user
        ).select_related('badge', 'event').order_by('-earned_at')


class UserAchievementsView(generics.ListAPIView):
    """List all achievements earned by the current user"""
    serializer_class = AchievementSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Achievement.objects.filter(
            user=self.request.user
        ).select_related('event').order_by('-achieved_at')


class AvailableBadgesView(generics.ListAPIView):
    """List all available badges that can be earned"""
    serializer_class = BadgeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Badge.objects.filter(is_active=True).order_by('badge_type', 'name')


class LeaderboardView(generics.GenericAPIView):
    """Get leaderboard for specified period"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, period='monthly'):
        """Get leaderboard data"""
        valid_periods = ['daily', 'weekly', 'monthly', 'yearly', 'all_time']
        
        if period not in valid_periods:
            return Response(
                {'error': f'Invalid period. Must be one of: {", ".join(valid_periods)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        service = LeaderboardService()
        leaderboard_data = service.get_leaderboard(period, limit=50)
        user_rank = service.get_user_rank(request.user, period)
        
        # Convert to serializable format
        if leaderboard_data and isinstance(leaderboard_data[0], dict):
            # Period-specific leaderboard
            entries = []
            for entry in leaderboard_data:
                entries.append({
                    'rank': len(entries) + 1,
                    'user': entry['user'],
                    'events_attended': entry['events_attended'],
                    'points_earned': entry['total_points'],
                    'current_streak': entry['current_streak'],
                    'badges_earned': entry['badges_earned']
                })
        else:
            # All-time leaderboard (AttendeeProfile objects)
            entries = []
            for rank, profile in enumerate(leaderboard_data, 1):
                badges_count = profile.user.earned_badges.count()
                entries.append({
                    'rank': rank,
                    'user': profile.user,
                    'events_attended': profile.total_events_attended,
                    'points_earned': profile.total_points,
                    'current_streak': profile.current_streak,
                    'badges_earned': badges_count
                })
        
        response_data = {
            'period': period,
            'entries': entries,
            'user_rank': user_rank,
            'total_participants': len(entries)
        }
        
        serializer = LeaderboardSerializer(response_data)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_progress_view(request):
    """Get user's progress towards next level and badges"""
    try:
        profile = request.user.gamification_profile
    except AttendeeProfile.DoesNotExist:
        profile = AttendeeProfile.objects.create(user=request.user)
    
    service = GamificationStatsService()
    level_progress = service._calculate_level_progress(profile)
    
    # Get progress towards available badges
    available_badges = Badge.objects.filter(is_active=True).exclude(
        userbadge__user=request.user
    )[:5]  # Top 5 available badges
    
    badge_progress = []
    for badge in available_badges:
        progress = service._calculate_badge_progress(request.user, badge, profile)
        if progress > 0:
            badge_progress.append({
                'badge': BadgeSerializer(badge).data,
                'progress': progress
            })
    
    # Sort by progress (highest first)
    badge_progress.sort(key=lambda x: x['progress'], reverse=True)
    
    return Response({
        'level': profile.level,
        'level_progress': level_progress,
        'current_points': profile.total_points,
        'next_level_points': {
            'Bronze': 200,
            'Silver': 500,
            'Gold': 1000,
            'Platinum': 1000  # Max level
        }.get(profile.level, 1000),
        'badge_progress': badge_progress[:3]  # Top 3 badges to work towards
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def global_stats_view(request):
    """Get global gamification statistics"""
    total_profiles = AttendeeProfile.objects.count()
    total_badges_earned = UserBadge.objects.count()
    total_achievements = Achievement.objects.count()
    
    # Level distribution
    level_distribution = AttendeeProfile.objects.values('level').annotate(
        count=Count('level')
    ).order_by('level')
    
    # Most popular badges
    popular_badges = Badge.objects.annotate(
        earned_count=Count('userbadge')
    ).filter(earned_count__gt=0).order_by('-earned_count')[:5]
    
    # Top streaks
    top_streaks = AttendeeProfile.objects.filter(
        current_streak__gt=0
    ).order_by('-current_streak')[:3]
    
    return Response({
        'total_participants': total_profiles,
        'total_badges_earned': total_badges_earned,
        'total_achievements': total_achievements,
        'level_distribution': list(level_distribution),
        'popular_badges': BadgeSerializer(popular_badges, many=True).data,
        'top_current_streaks': AttendeeProfileSerializer(top_streaks, many=True).data
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def simulate_check_in_view(request):
    """Simulate a check-in for testing gamification (development only)"""
    from django.conf import settings
    
    if not settings.DEBUG:
        return Response(
            {'error': 'This endpoint is only available in debug mode'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # This is a development endpoint to test gamification
    # In production, gamification is triggered by actual check-ins
    
    try:
        profile, created = AttendeeProfile.objects.get_or_create(
            user=request.user
        )
        
        # Simulate attendance
        from datetime import date
        profile.update_streak(date.today())
        profile.add_points(10)  # Base attendance points
        profile.total_events_attended += 1
        profile.save()
        
        # Check for badges
        from .services import BadgeService
        badge_service = BadgeService()
        # Note: This won't work fully without actual event/attendance objects
        # But it will update streaks and points
        
        return Response({
            'message': 'Check-in simulated successfully',
            'profile': AttendeeProfileSerializer(profile).data
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )