from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from events.models import Event
from .models import Connection, NetworkingProfile, EventNetworkingSettings
from gamification.models import AttendeeProfile, Achievement
from gamification.services import GamificationStatsService
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Event)
def create_event_networking_settings(sender, instance, created, **kwargs):
    """Automatically create networking settings when a new event is created"""
    if created:
        EventNetworkingSettings.objects.create(
            event=instance,
            enable_networking=True,
            enable_qr_exchange=True,
            enable_attendee_directory=True,
            enable_contact_export=True,
            allow_industry_filter=True,
            allow_interest_filter=True,
            allow_company_filter=True,
            networking_points_enabled=True
        )
        logger.info(f"Created networking settings for event: {instance.name}")


@receiver(post_save, sender=User)
def create_networking_profile(sender, instance, created, **kwargs):
    """Create networking profile when user is created"""
    if created:
        NetworkingProfile.objects.create(
            user=instance,
            company=getattr(instance, 'company', ''),
            visible_in_directory=True,
            allow_contact_sharing=True
        )
        logger.info(f"Created networking profile for user: {instance.username}")


@receiver(post_save, sender=Connection)
def handle_networking_gamification(sender, instance, created, **kwargs):
    """Award gamification points for networking connections"""
    if created and not instance.gamification_processed:
        logger.info(f"Processing gamification for connection: {instance}")
        
        # Mark as processed to avoid double-processing
        instance.gamification_processed = True
        
        # Get networking settings for the event
        try:
            settings = instance.event.networking_settings
            if not settings.networking_points_enabled:
                logger.info(f"Networking points disabled for event {instance.event.name}")
                return
            
            points_to_award = settings.points_per_connection
            max_daily_points = settings.max_daily_networking_points
        except:
            # Default settings if not configured
            points_to_award = 5
            max_daily_points = 100
        
        # Process gamification for both users
        users_to_process = [instance.from_user, instance.to_user]
        
        for user in users_to_process:
            try:
                # Get or create attendee profile
                profile, created = AttendeeProfile.objects.get_or_create(user=user)
                
                # Check daily points limit
                from datetime import date
                today = date.today()
                daily_connections = Connection.objects.filter(
                    from_user=user,
                    connected_at__date=today,
                    gamification_processed=True
                ).count()
                
                daily_points_earned = daily_connections * points_to_award
                
                if daily_points_earned >= max_daily_points:
                    logger.info(f"User {user.username} has reached daily networking points limit")
                    continue
                
                # Award points
                profile.add_points(points_to_award)
                profile.save()
                
                # Create networking achievements
                create_networking_achievements(user, instance.event, profile, instance)
                
                logger.info(f"Networking gamification processed for {user.username}: +{points_to_award} points")
                
            except Exception as e:
                logger.error(f"Failed to process networking gamification for {user.username}: {str(e)}")
        
        # Store points awarded and mark as processed
        instance.points_awarded = points_to_award
        
        # Save the connection to mark gamification as processed
        # Use update_fields to avoid infinite recursion
        Connection.objects.filter(id=instance.id).update(
            gamification_processed=True, 
            points_awarded=points_to_award
        )


def create_networking_achievements(user, event, profile, connection):
    """Create achievement records for networking milestones"""
    achievements_to_create = []
    
    # Count total connections for this user
    total_connections = Connection.objects.filter(
        from_user=user,
        gamification_processed=True
    ).count()
    
    # First connection achievement
    if total_connections == 1:
        achievements_to_create.append({
            'title': 'First Connection!',
            'description': 'Made your first networking connection',
            'icon': 'handshake',
            'data': {'connection_id': str(connection.id), 'method': connection.connection_method}
        })
    
    # Connection milestone achievements
    elif total_connections in [5, 10, 25, 50, 100]:
        achievements_to_create.append({
            'title': f'{total_connections} Connections!',
            'description': f'Built a network of {total_connections} professional connections',
            'icon': '🌐',
            'data': {'total_connections': total_connections}
        })
    
    # QR Scanning achievements
    if connection.connection_method == 'qr_scan':
        qr_connections = Connection.objects.filter(
            from_user=user,
            connection_method='qr_scan',
            gamification_processed=True
        ).count()
        
        if qr_connections in [5, 20, 50]:
            achievements_to_create.append({
                'title': f'QR Scanner Pro!',
                'description': f'Connected with {qr_connections} people via QR code',
                'icon': 'mobile',
                'data': {'qr_connections': qr_connections}
            })
    
    # Event-specific networking achievements
    event_connections = Connection.objects.filter(
        from_user=user,
        event=event,
        gamification_processed=True
    ).count()
    
    if event_connections >= 10:
        achievements_to_create.append({
            'title': 'Event Networker!',
            'description': f'Made {event_connections} connections at {event.name}',
            'icon': '⭐',
            'data': {'event_connections': event_connections, 'event_name': event.name}
        })
    
    # Super Connector achievement (connecting with people from different companies)
    if total_connections >= 20:
        # Count unique companies connected to
        unique_companies = Connection.objects.filter(
            from_user=user,
            gamification_processed=True,
            to_user__networking_profile__company__isnull=False
        ).exclude(
            to_user__networking_profile__company=''
        ).values_list('to_user__networking_profile__company', flat=True).distinct().count()
        
        if unique_companies >= 10:
            achievements_to_create.append({
                'title': 'Super Connector!',
                'description': f'Connected with professionals from {unique_companies} different companies',
                'icon': '🏢',
                'data': {'unique_companies': unique_companies}
            })
    
    # Create achievement records
    for achievement_data in achievements_to_create:
        Achievement.objects.create(
            user=user,
            event=event,
            **achievement_data
        )
        logger.info(f"Networking achievement created for {user.username}: {achievement_data['title']}")
