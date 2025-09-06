from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from attendance.models import Attendance
from .models import AttendeeProfile, UserBadge, Achievement
from .services import BadgeService, LeaderboardService
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_attendee_profile(sender, instance, created, **kwargs):
    """Create gamification profile when user is created"""
    if created:
        AttendeeProfile.objects.create(user=instance)
        logger.info(f"Created gamification profile for user: {instance.username}")


@receiver(post_save, sender=Attendance)
def handle_attendance_gamification(sender, instance, created, **kwargs):
    """Handle gamification updates when user checks in"""
    # Only process if has_attended is True and gamification hasn't been processed yet
    if instance.has_attended and not instance.gamification_processed:
        logger.info(f"Processing gamification for attendance: {instance}")
        
        # Mark as processed to avoid double-processing
        instance.gamification_processed = True
        
        # Try to find user by email
        user = None
        if instance.invitation.guest_email:
            try:
                user = User.objects.get(email=instance.invitation.guest_email)
            except User.DoesNotExist:
                # If no user account exists, skip gamification for now
                # Gamification will be available once they create an account
                logger.info(f"No user account found for email {instance.invitation.guest_email}")
                return
        
        if not user:
            logger.warning(f"No user or email for invitation {instance.invitation.id}")
            return
        
        # Get or create attendee profile
        profile, created = AttendeeProfile.objects.get_or_create(user=user)
        
        event = instance.invitation.event
        event_date = event.date
        
        # Update streak
        profile.update_streak(event_date)
        
        # Add base attendance points
        points_earned = 10  # Base points for attendance
        
        # Bonus points for early check-in
        event_start = instance.invitation.event.get_start_datetime()
        check_in_time = instance.check_in_time
        
        if event_start and check_in_time:
            minutes_early = (event_start - check_in_time).total_seconds() / 60
            if minutes_early >= 30:
                points_earned += 5  # Bonus for being 30+ minutes early
            elif minutes_early >= 15:
                points_earned += 3  # Bonus for being 15+ minutes early
        
        # Streak bonus points
        if profile.current_streak >= 7:
            points_earned += 10  # Weekly streak bonus
        elif profile.current_streak >= 3:
            points_earned += 5   # 3-day streak bonus
        
        profile.add_points(points_earned)
        profile.total_events_attended += 1
        profile.save()
        
        # Check for new badges
        badge_service = BadgeService()
        newly_earned_badges = badge_service.check_and_award_badges(user, event, instance)
        
        # Create achievements for significant milestones
        create_achievements(user, event, profile, newly_earned_badges)
        
        # Update leaderboards
        leaderboard_service = LeaderboardService()
        leaderboard_service.update_user_rankings(user)
        
        logger.info(f"Gamification processed for {profile.user.username}: +{points_earned} points, streak: {profile.current_streak}")
        
        # Save the attendance record to mark gamification as processed
        # Use update_fields to avoid infinite recursion
        Attendance.objects.filter(id=instance.id).update(gamification_processed=True)


def create_achievements(user, event, profile, new_badges):
    """Create achievement records for milestones"""
    achievements_to_create = []
    
    # Streak achievements
    if profile.current_streak in [3, 7, 14, 30]:
        achievements_to_create.append({
            'title': f'{profile.current_streak}-Day Streak!',
            'description': f'Attended {profile.current_streak} events in a row',
            'icon': '🔥',
            'data': {'streak': profile.current_streak}
        })
    
    # Attendance milestones
    if profile.total_events_attended in [1, 5, 10, 25, 50, 100]:
        achievements_to_create.append({
            'title': f'{profile.total_events_attended} Events Attended!',
            'description': f'Reached {profile.total_events_attended} total events',
            'icon': '🎯',
            'data': {'total_events': profile.total_events_attended}
        })
    
    # Level up achievements
    if profile.total_points in [200, 500, 1000]:
        achievements_to_create.append({
            'title': f'Level Up: {profile.level}!',
            'description': f'Reached {profile.level} level with {profile.total_points} points',
            'icon': '⭐',
            'data': {'level': profile.level, 'points': profile.total_points}
        })
    
    # Badge achievements
    for badge in new_badges:
        achievements_to_create.append({
            'title': f'Badge Earned: {badge.name}!',
            'description': badge.description,
            'icon': badge.icon,
            'data': {'badge_id': badge.id, 'badge_name': badge.name}
        })
    
    # Create achievement records
    for achievement_data in achievements_to_create:
        Achievement.objects.create(
            user=user,
            event=event,
            **achievement_data
        )
        logger.info(f"Achievement created for {user.username}: {achievement_data['title']}")