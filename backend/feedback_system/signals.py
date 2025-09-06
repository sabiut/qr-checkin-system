from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import EventFeedback
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=EventFeedback)
def handle_feedback_gamification(sender, instance, created, **kwargs):
    """Award gamification points for feedback submission."""
    if created and not instance.gamification_processed:
        logger.info(f"Processing gamification for feedback: {instance.id}")
        
        try:
            # Find user by email
            user = None
            if instance.respondent_email:
                try:
                    user = User.objects.get(email=instance.respondent_email)
                except User.DoesNotExist:
                    logger.info(f"No user account found for email {instance.respondent_email}")
                    return
            
            if not user:
                logger.warning(f"No user for feedback {instance.id}")
                return
            
            # Import here to avoid circular imports
            from gamification.models import AttendeeProfile
            
            # Get or create attendee profile
            profile, created = AttendeeProfile.objects.get_or_create(user=user)
            
            # Base points for feedback submission
            points_earned = 15  # More than attendance to encourage feedback
            
            # Bonus points for detailed feedback
            if instance.what_went_well and len(instance.what_went_well.strip()) > 50:
                points_earned += 5
            if instance.what_needs_improvement and len(instance.what_needs_improvement.strip()) > 50:
                points_earned += 5
            if instance.additional_comments and len(instance.additional_comments.strip()) > 50:
                points_earned += 5
            
            # Bonus for high rating
            if instance.overall_rating >= 4:
                points_earned += 3
            
            # Bonus for NPS promoter
            if instance.nps_score and instance.nps_score >= 9:
                points_earned += 5
            
            # Bonus for would recommend
            if instance.would_recommend:
                points_earned += 3
            
            # Add points to profile
            profile.add_points(points_earned)
            profile.save()
            
            # Update feedback record
            instance.points_awarded = points_earned
            instance.gamification_processed = True
            instance.save(update_fields=['points_awarded', 'gamification_processed'])
            
            # Check for feedback-related badges
            from gamification.services import BadgeService
            badge_service = BadgeService()
            newly_earned_badges = badge_service.check_feedback_badges(user, instance)
            
            # Create achievements
            from gamification.models import Achievement
            
            # Feedback submission achievement
            Achievement.objects.create(
                user=user,
                event=instance.event,
                title='Feedback Submitted! 📝',
                description=f'Provided valuable feedback for {instance.event.name}',
                icon='📝',
                data={'points_earned': points_earned, 'feedback_id': str(instance.id)}
            )
            
            # Detailed feedback achievement
            if points_earned >= 25:  # Got bonuses for detailed feedback
                Achievement.objects.create(
                    user=user,
                    event=instance.event,
                    title='Detailed Reviewer! 🔍',
                    description='Provided comprehensive feedback with detailed comments',
                    icon='🔍',
                    data={'detailed_feedback': True}
                )
            
            # Promoter achievement
            if instance.nps_score and instance.nps_score >= 9:
                Achievement.objects.create(
                    user=user,
                    event=instance.event,
                    title='Event Promoter! 🌟',
                    description='Rated as a promoter - would recommend this event to others',
                    icon='🌟',
                    data={'nps_score': instance.nps_score}
                )
            
            logger.info(f"Gamification processed for feedback {instance.id}: +{points_earned} points")
            
        except Exception as e:
            logger.error(f"Failed to process gamification for feedback {instance.id}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())