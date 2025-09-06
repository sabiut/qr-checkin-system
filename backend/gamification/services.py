from django.db.models import Count, Q, Sum, Max
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta, date
from .models import Badge, UserBadge, AttendeeProfile, LeaderboardEntry
from attendance.models import Attendance
import logging

logger = logging.getLogger(__name__)


class BadgeService:
    """Service for managing badge logic and awards"""
    
    def check_and_award_badges(self, user, event, attendance):
        """Check if user qualifies for any new badges and award them"""
        newly_earned_badges = []
        
        # Get all active badges that user hasn't earned yet
        available_badges = Badge.objects.filter(
            is_active=True
        ).exclude(
            userbadge__user=user
        )
        
        for badge in available_badges:
            if self.meets_badge_criteria(user, badge, event, attendance):
                user_badge, created = UserBadge.objects.get_or_create(
                    user=user,
                    badge=badge,
                    defaults={'event': event}
                )
                
                if created:
                    newly_earned_badges.append(badge)
                    # Award points for earning badge
                    profile = user.gamification_profile
                    profile.add_points(badge.points_reward)
                    logger.info(f"Badge '{badge.name}' awarded to {user.username}")
        
        return newly_earned_badges
    
    def meets_badge_criteria(self, user, badge, event, attendance):
        """Check if user meets specific badge criteria"""
        criteria = badge.criteria
        profile = user.gamification_profile
        
        try:
            if badge.badge_type == 'attendance':
                return self._check_attendance_criteria(user, criteria, profile)
            elif badge.badge_type == 'punctuality':
                return self._check_punctuality_criteria(user, criteria, event, attendance)
            elif badge.badge_type == 'streak':
                return self._check_streak_criteria(user, criteria, profile)
            elif badge.badge_type == 'networking':
                return self._check_networking_criteria(user, criteria, profile)
            elif badge.badge_type == 'special':
                return self._check_special_criteria(user, criteria, event)
        except Exception as e:
            logger.error(f"Error checking badge criteria for {badge.name}: {e}")
            return False
        
        return False
    
    def _check_attendance_criteria(self, user, criteria, profile):
        """Check attendance-based badge criteria"""
        required_events = criteria.get('events_required', 0)
        time_period = criteria.get('time_period', 'all_time')  # 'week', 'month', 'year', 'all_time'
        
        if time_period == 'all_time':
            return profile.total_events_attended >= required_events
        else:
            # Count events in specific time period
            now = timezone.now()
            if time_period == 'week':
                start_date = now - timedelta(days=7)
            elif time_period == 'month':
                start_date = now - timedelta(days=30)
            elif time_period == 'year':
                start_date = now - timedelta(days=365)
            else:
                return False
            
            attendance_count = Attendance.objects.filter(
                invitation__guest_email=user.email,
                has_attended=True,
                check_in_time__gte=start_date
            ).count()
            
            return attendance_count >= required_events
    
    def _check_punctuality_criteria(self, user, criteria, event, attendance):
        """Check punctuality-based badge criteria"""
        max_minutes_early = criteria.get('max_minutes_early', 0)
        min_minutes_early = criteria.get('min_minutes_early', 0)
        consecutive_required = criteria.get('consecutive_required', 1)
        
        # Check current attendance punctuality
        event_start = event.get_start_datetime()
        if not event_start:
            return False
        
        minutes_early = (event_start - attendance.check_in_time).total_seconds() / 60
        
        if not (min_minutes_early <= minutes_early <= max_minutes_early):
            return False
        
        # If consecutive punctuality required, check previous events
        if consecutive_required > 1:
            # This would require more complex logic to track punctuality history
            # For now, just award if current check-in meets criteria
            pass
        
        return True
    
    def _check_streak_criteria(self, user, criteria, profile):
        """Check streak-based badge criteria"""
        required_streak = criteria.get('streak_required', 0)
        streak_type = criteria.get('streak_type', 'current')  # 'current' or 'longest'
        
        if streak_type == 'current':
            return profile.current_streak >= required_streak
        else:
            return profile.longest_streak >= required_streak
    
    def _check_networking_criteria(self, user, criteria, profile):
        """Check networking-based badge criteria"""
        # This would require additional data about networking activities
        # For now, base it on number of events attended
        events_for_networking = criteria.get('events_for_networking', 10)
        return profile.total_events_attended >= events_for_networking
    
    def _check_special_criteria(self, user, criteria, event):
        """Check special event-specific badge criteria"""
        # VIP badge, event-specific badges, etc.
        event_type = criteria.get('event_type')
        if event_type and hasattr(event, 'event_type'):
            return event.event_type == event_type
        return False
    
    def check_feedback_badges(self, user, feedback_instance):
        """Check and award feedback-related badges"""
        newly_earned_badges = []
        
        try:
            profile = AttendeeProfile.objects.get(user=user)
            
            # Get feedback count for this user
            from feedback_system.models import EventFeedback
            feedback_count = EventFeedback.objects.filter(
                respondent_email=user.email,
                gamification_processed=True
            ).count()
            
            # Feedback milestone badges
            feedback_milestones = [
                (1, 'feedback_first', 'First Feedback', 'Submitted your first event feedback'),
                (5, 'feedback_veteran', 'Feedback Veteran', 'Provided feedback for 5 events'),
                (10, 'feedback_expert', 'Feedback Expert', 'Provided feedback for 10 events'),
                (25, 'feedback_champion', 'Feedback Champion', 'Provided feedback for 25 events'),
            ]
            
            for count, badge_slug, title, description in feedback_milestones:
                if feedback_count == count:
                    badge, created = Badge.objects.get_or_create(
                        name=title,
                        badge_type='feedback',
                        defaults={
                            'description': description,
                            'icon': '📝',
                            'criteria': {'feedback_count': count},
                            'is_active': True
                        }
                    )
                    
                    earned_badge, created = UserBadge.objects.get_or_create(
                        user=user,
                        badge=badge,
                        defaults={'earned_at': timezone.now()}
                    )
                    
                    if created:
                        newly_earned_badges.append(earned_badge)
            
            # Quality feedback badges based on feedback content
            if hasattr(feedback_instance, 'overall_rating') and feedback_instance.overall_rating:
                # High rating badge
                if feedback_instance.overall_rating >= 4:
                    badge, created = Badge.objects.get_or_create(
                        name='Positive Reviewer',
                        badge_type='feedback',
                        defaults={
                            'description': 'Consistently gives positive feedback',
                            'icon': '⭐',
                            'criteria': {'positive_feedback': True},
                            'is_active': True
                        }
                    )
                    
                    earned_badge, created = UserBadge.objects.get_or_create(
                        user=user,
                        badge=badge,
                        defaults={'earned_at': timezone.now()}
                    )
                    
                    if created:
                        newly_earned_badges.append(earned_badge)
            
            # Detailed feedback badge
            detailed_feedback = (
                (feedback_instance.what_went_well and len(feedback_instance.what_went_well.strip()) > 50) or
                (feedback_instance.what_needs_improvement and len(feedback_instance.what_needs_improvement.strip()) > 50) or
                (feedback_instance.additional_comments and len(feedback_instance.additional_comments.strip()) > 50)
            )
            
            if detailed_feedback:
                badge, created = Badge.objects.get_or_create(
                    name='Detailed Reviewer',
                    badge_type='feedback',
                    defaults={
                        'description': 'Provides comprehensive feedback with detailed comments',
                        'icon': '📋',
                        'criteria': {'detailed_feedback': True},
                        'is_active': True
                    }
                )
                
                earned_badge, created = UserBadge.objects.get_or_create(
                    user=user,
                    badge=badge,
                    defaults={'earned_at': timezone.now()}
                )
                
                if created:
                    newly_earned_badges.append(earned_badge)
        
        except Exception as e:
            logger.error(f"Error checking feedback badges for user {user.id}: {str(e)}")
        
        return newly_earned_badges


class LeaderboardService:
    """Service for managing leaderboards and rankings"""
    
    def get_leaderboard(self, period='monthly', limit=10):
        """Get leaderboard for specified period"""
        now = timezone.now()
        
        if period == 'daily':
            start_date = now.date()
        elif period == 'weekly':
            start_date = now.date() - timedelta(days=7)
        elif period == 'monthly':
            start_date = now.date() - timedelta(days=30)
        elif period == 'yearly':
            start_date = now.date() - timedelta(days=365)
        else:  # all_time
            start_date = None
        
        # Get user profiles with aggregated stats
        profiles = AttendeeProfile.objects.select_related('user')
        
        if start_date:
            # Filter for time period and calculate period-specific stats
            leaderboard_data = []
            for profile in profiles:
                attendance_count = Attendance.objects.filter(
                    invitation__guest_email=profile.user.email,
                    has_attended=True,
                    check_in_time__date__gte=start_date
                ).count()
                
                badges_count = UserBadge.objects.filter(
                    user=profile.user,
                    earned_at__date__gte=start_date
                ).count()
                
                if attendance_count > 0:  # Only include users with activity
                    leaderboard_data.append({
                        'user': profile.user,
                        'profile': profile,
                        'events_attended': attendance_count,
                        'badges_earned': badges_count,
                        'current_streak': profile.current_streak,
                        'total_points': profile.total_points
                    })
            
            # Sort by events attended, then by points, then by streak
            leaderboard_data.sort(
                key=lambda x: (x['events_attended'], x['total_points'], x['current_streak']),
                reverse=True
            )
            
            return leaderboard_data[:limit]
        else:
            # All-time leaderboard
            return profiles.order_by('-total_points', '-current_streak', '-total_events_attended')[:limit]
    
    def get_user_rank(self, user, period='monthly'):
        """Get user's current rank in specified leaderboard"""
        # Check if user is valid and authenticated
        if not user or not hasattr(user, 'id') or not user.is_authenticated:
            return None
            
        leaderboard = self.get_leaderboard(period, limit=1000)  # Get larger sample
        
        for index, entry in enumerate(leaderboard):
            if isinstance(entry, dict):
                if entry['user'] == user:
                    return index + 1
            else:  # AttendeeProfile object
                if entry.user == user:
                    return index + 1
        
        return None
    
    def update_user_rankings(self, user):
        """Update leaderboard entries for user across different periods"""
        periods = ['daily', 'weekly', 'monthly', 'yearly']
        today = date.today()
        
        for period in periods:
            # Calculate period-specific stats
            if period == 'daily':
                period_date = today
                start_date = today
            elif period == 'weekly':
                period_date = today - timedelta(days=today.weekday())  # Start of week
                start_date = period_date
            elif period == 'monthly':
                period_date = today.replace(day=1)  # Start of month
                start_date = period_date
            elif period == 'yearly':
                period_date = today.replace(month=1, day=1)  # Start of year
                start_date = period_date
            
            # Get user stats for period
            attendance_count = Attendance.objects.filter(
                invitation__guest_email=user.email,
                has_attended=True,
                check_in_time__date__gte=start_date
            ).count()
            
            badges_count = UserBadge.objects.filter(
                user=user,
                earned_at__date__gte=start_date
            ).count()
            
            profile = user.gamification_profile
            
            # Create or update leaderboard entry
            entry, created = LeaderboardEntry.objects.update_or_create(
                user=user,
                period=period,
                period_date=period_date,
                defaults={
                    'events_attended': attendance_count,
                    'badges_earned': badges_count,
                    'current_streak': profile.current_streak,
                    'points_earned': profile.total_points,
                    'rank': 0  # Will be calculated separately
                }
            )
        
        # Recalculate rankings for all periods
        self._recalculate_rankings()
    
    def _recalculate_rankings(self):
        """Recalculate rankings for all leaderboard entries"""
        periods = ['daily', 'weekly', 'monthly', 'yearly']
        
        for period in periods:
            entries = LeaderboardEntry.objects.filter(
                period=period,
                period_date=date.today()  # Only current period
            ).order_by('-events_attended', '-points_earned', '-current_streak')
            
            for rank, entry in enumerate(entries, 1):
                entry.rank = rank
                entry.save(update_fields=['rank'])


class GamificationStatsService:
    """Service for getting gamification statistics"""
    
    def get_user_stats(self, user):
        """Get comprehensive stats for a user"""
        # Check if user is valid and authenticated
        if not user or not hasattr(user, 'id') or not user.is_authenticated:
            return None
            
        try:
            profile = user.gamification_profile
        except AttendeeProfile.DoesNotExist:
            # Create profile if it doesn't exist
            profile = AttendeeProfile.objects.create(user=user)
        
        badges = UserBadge.objects.filter(user=user).select_related('badge')
        recent_achievements = user.achievements.all()[:5]
        
        # Get next badge to work towards
        next_badge = self._get_next_badge_suggestion(user, profile)
        
        leaderboard_service = LeaderboardService()
        monthly_rank = leaderboard_service.get_user_rank(user, 'monthly')
        
        return {
            'profile': profile,
            'badges': badges,
            'badge_count': badges.count(),
            'recent_achievements': recent_achievements,
            'next_badge': next_badge,
            'monthly_rank': monthly_rank,
            'level_progress': self._calculate_level_progress(profile)
        }
    
    def _get_next_badge_suggestion(self, user, profile):
        """Suggest next badge user could work towards"""
        available_badges = Badge.objects.filter(
            is_active=True
        ).exclude(
            userbadge__user=user
        ).order_by('points_reward')
        
        # Find the "easiest" badge to achieve next
        for badge in available_badges:
            progress = self._calculate_badge_progress(user, badge, profile)
            if progress > 0:  # User has made some progress
                return {
                    'badge': badge,
                    'progress': progress
                }
        
        return available_badges.first() if available_badges.exists() else None
    
    def _calculate_badge_progress(self, user, badge, profile):
        """Calculate user's progress towards a specific badge (0-100%)"""
        criteria = badge.criteria
        
        if badge.badge_type == 'attendance':
            required = criteria.get('events_required', 1)
            current = profile.total_events_attended
            return min(100, (current / required) * 100)
        elif badge.badge_type == 'streak':
            required = criteria.get('streak_required', 1)
            current = profile.current_streak
            return min(100, (current / required) * 100)
        
        return 0
    
    def _calculate_level_progress(self, profile):
        """Calculate progress to next level"""
        current_points = profile.total_points
        
        if profile.level == 'Bronze':
            next_level_points = 200
        elif profile.level == 'Silver':
            next_level_points = 500
        elif profile.level == 'Gold':
            next_level_points = 1000
        else:  # Platinum
            return 100  # Max level
        
        if current_points >= next_level_points:
            return 100
        
        # Calculate progress within current level
        if profile.level == 'Bronze':
            level_start_points = 0
        elif profile.level == 'Silver':
            level_start_points = 200
        else:  # Gold
            level_start_points = 500
        
        level_points_range = next_level_points - level_start_points
        current_level_points = current_points - level_start_points
        
        return (current_level_points / level_points_range) * 100