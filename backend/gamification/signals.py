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
            'icon': 'fire',
            'data': {'streak': profile.current_streak}
        })
    
    # Attendance milestones
    if profile.total_events_attended in [1, 5, 10, 25, 50, 100]:
        achievements_to_create.append({
            'title': f'{profile.total_events_attended} Events Attended!',
            'description': f'Reached {profile.total_events_attended} total events',
            'icon': 'target',
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


@receiver(post_save, sender='feedback_system.EventFeedback')
def handle_feedback_gamification(sender, instance, created, **kwargs):
    """Award gamification points for feedback submission."""
    if created and not instance.gamification_processed:
        logger.info(f"Processing gamification for feedback: {instance}")
        
        # Mark as processed to avoid double-processing
        instance.gamification_processed = True
        
        # Try to find user by email or create guest profile
        user = None
        guest_email = instance.respondent_email
        
        try:
            # Try to find existing user with this email
            user = User.objects.get(email=guest_email)
            logger.info(f"Found existing user for email {guest_email}")
        except User.DoesNotExist:
            # For guests, we can still track points using guest email in a simple way
            # We'll award points but store them differently for guests
            logger.info(f"No user account found for email {guest_email}, processing as guest")
        
        # Calculate base feedback points
        points_earned = 15  # Base points for feedback submission
        
        # Bonus points for detailed feedback
        if hasattr(instance, 'what_went_well') and instance.what_went_well and len(instance.what_went_well.strip()) > 30:
            points_earned += 5
        
        if hasattr(instance, 'what_needs_improvement') and instance.what_needs_improvement and len(instance.what_needs_improvement.strip()) > 30:
            points_earned += 5
        
        if hasattr(instance, 'additional_comments') and instance.additional_comments and len(instance.additional_comments.strip()) > 30:
            points_earned += 3
        
        # Bonus for high ratings
        if hasattr(instance, 'overall_rating') and instance.overall_rating:
            if instance.overall_rating >= 4:
                points_earned += 3
        
        # Bonus for NPS score
        if hasattr(instance, 'nps_score') and instance.nps_score is not None:
            if instance.nps_score >= 9:  # Promoter
                points_earned += 5
            elif instance.nps_score >= 7:  # Passive
                points_earned += 2
        
        # Store points in the feedback record for tracking
        instance.points_awarded = points_earned
        
        # If user exists, update their profile
        if user:
            # Get or create attendee profile
            profile, created = AttendeeProfile.objects.get_or_create(user=user)
            
            # Add points to user profile
            profile.add_points(points_earned)
            profile.save()
            
            # Check for feedback badges
            badge_service = BadgeService()
            newly_earned_badges = badge_service.check_feedback_badges(user, instance)
            
            # Create achievements for feedback milestones
            create_feedback_achievements(user, instance.event, profile, newly_earned_badges, points_earned)
            
            # Update leaderboards
            leaderboard_service = LeaderboardService()
            leaderboard_service.update_user_rankings(user)
            
            logger.info(f"Gamification processed for user {user.username}: +{points_earned} points for feedback")
        else:
            # For guests, just log the points (could be stored in a separate guest points table in the future)
            logger.info(f"Gamification processed for guest {guest_email}: +{points_earned} points for feedback (guest)")
        
        # Save the feedback record to mark gamification as processed and store points
        # Use update_fields to avoid infinite recursion
        sender.objects.filter(id=instance.id).update(
            gamification_processed=True, 
            points_awarded=points_earned
        )


def create_feedback_achievements(user, event, profile, new_badges, points_earned):
    """Create achievement records for feedback milestones"""
    achievements_to_create = []
    
    # First feedback achievement
    from feedback_system.models import EventFeedback
    feedback_count = EventFeedback.objects.filter(
        respondent_email=user.email,
        gamification_processed=True
    ).count()
    
    if feedback_count == 1:
        achievements_to_create.append({
            'title': 'First Feedback!',
            'description': 'Submitted your first event feedback',
            'icon': 'note',
            'data': {'points_earned': points_earned, 'feedback_count': 1}
        })
    elif feedback_count in [5, 10, 25]:
        achievements_to_create.append({
            'title': f'{feedback_count} Feedback Submissions!',
            'description': f'Provided feedback for {feedback_count} events',
            'icon': 'clipboard',
            'data': {'points_earned': points_earned, 'feedback_count': feedback_count}
        })
    
    # High-quality feedback achievement (if earned lots of bonus points)
    if points_earned >= 25:  # Base 15 + lots of bonuses
        achievements_to_create.append({
            'title': 'Quality Reviewer!',
            'description': 'Provided comprehensive and detailed feedback',
            'icon': '⭐',
            'data': {'points_earned': points_earned, 'detailed_feedback': True}
        })
    
    # Badge achievements
    for badge in new_badges:
        achievements_to_create.append({
            'title': f'Badge Earned: {badge.badge.name}!',
            'description': badge.badge.description,
            'icon': badge.badge.icon,
            'data': {'badge_id': badge.badge.id, 'badge_name': badge.badge.name}
        })
    
    # Create achievement records
    for achievement_data in achievements_to_create:
        Achievement.objects.create(
            user=user,
            event=event,
            **achievement_data
        )
        logger.info(f"Feedback achievement created for {user.username}: {achievement_data['title']}")