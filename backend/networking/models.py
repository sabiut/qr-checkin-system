from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from events.models import Event
import uuid


class NetworkingProfile(models.Model):
    """Extended user profile for networking features"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='networking_profile')
    
    # Basic networking info
    bio = models.TextField(max_length=500, blank=True, help_text="Brief professional bio")
    company = models.CharField(max_length=200, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    
    # Contact preferences
    phone_number = models.CharField(max_length=20, blank=True)
    linkedin_url = models.URLField(blank=True)
    twitter_handle = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    
    # Networking preferences
    interests = models.JSONField(default=list, help_text="List of professional interests")
    looking_for = models.JSONField(default=list, help_text="What they're looking to connect about")
    
    # Privacy settings
    allow_contact_sharing = models.BooleanField(default=True)
    visible_in_directory = models.BooleanField(default=True)
    share_email = models.BooleanField(default=True)
    share_phone = models.BooleanField(default=False)
    share_social = models.BooleanField(default=True)
    
    # Networking QR code
    networking_qr_token = models.UUIDField(default=uuid.uuid4, unique=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['user__first_name', 'user__last_name']
    
    def __str__(self):
        return f"Networking Profile - {self.user.get_full_name() or self.user.username}"
    
    def get_shareable_info(self):
        """Get contact info based on privacy settings"""
        info = {
            'name': self.user.get_full_name() or self.user.username,
            'company': self.company,
            'job_title': self.job_title,
            'industry': self.industry,
            'bio': self.bio,
            'interests': self.interests,
            'looking_for': self.looking_for,
        }
        
        if self.share_email:
            info['email'] = self.user.email
        if self.share_phone and self.phone_number:
            info['phone'] = self.phone_number
        if self.share_social:
            if self.linkedin_url:
                info['linkedin'] = self.linkedin_url
            if self.twitter_handle:
                info['twitter'] = self.twitter_handle
            if self.website:
                info['website'] = self.website
        
        return info


class ConnectionStatus(models.TextChoices):
    """Status choices for connections"""
    PENDING = 'pending', 'Pending'
    ACCEPTED = 'accepted', 'Accepted'
    BLOCKED = 'blocked', 'Blocked'


class ConnectionMethod(models.TextChoices):
    """Method choices for how connections were made"""
    QR_SCAN = 'qr_scan', 'QR Code Scan'
    DIRECTORY = 'directory', 'Attendee Directory'
    MANUAL = 'manual', 'Manual Add'
    MUTUAL = 'mutual', 'Mutual Connection'


class Connection(models.Model):
    """Represents a networking connection between two users at an event"""
    CONNECTION_METHODS = [
        ('qr_scan', 'QR Code Scan'),
        ('directory', 'Attendee Directory'),
        ('manual', 'Manual Add'),
        ('mutual', 'Mutual Connection'),
    ]
    
    CONNECTION_STATUS = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('blocked', 'Blocked'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Connection participants
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connections_made')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connections_received')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='networking_connections')
    
    # Connection details
    connection_method = models.CharField(max_length=20, choices=ConnectionMethod.choices, default=ConnectionMethod.QR_SCAN)
    status = models.CharField(max_length=20, choices=ConnectionStatus.choices, default=ConnectionStatus.ACCEPTED)
    
    # Meeting context
    meeting_location = models.CharField(max_length=200, blank=True, help_text="Where they met at the event")
    notes_from_user = models.TextField(blank=True, help_text="Private notes from initiating user")
    notes_to_user = models.TextField(blank=True, help_text="Private notes from receiving user")
    
    # Gamification tracking
    points_awarded = models.IntegerField(default=0)
    gamification_processed = models.BooleanField(default=False)
    
    # Timestamps
    connected_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['from_user', 'to_user', 'event']
        ordering = ['-connected_at']
        indexes = [
            models.Index(fields=['from_user', 'event', 'status']),
            models.Index(fields=['to_user', 'event', 'status']),
            models.Index(fields=['event', 'connected_at']),
            models.Index(fields=['status', 'connected_at']),
        ]
    
    def __str__(self):
        return f"{self.from_user.username} → {self.to_user.username} at {self.event.name}"
    
    def create_reverse_connection(self):
        """Create the reciprocal connection"""
        reverse_connection, created = Connection.objects.get_or_create(
            from_user=self.to_user,
            to_user=self.from_user,
            event=self.event,
            defaults={
                'connection_method': 'mutual',
                'status': self.status,
                'meeting_location': self.meeting_location,
                'connected_at': self.connected_at,
            }
        )
        return reverse_connection, created


class NetworkingInteraction(models.Model):
    """Track networking interactions and engagement"""
    INTERACTION_TYPES = [
        ('profile_view', 'Profile View'),
        ('qr_scan', 'QR Code Scan'),
        ('contact_share', 'Contact Share'),
        ('directory_search', 'Directory Search'),
        ('connection_request', 'Connection Request'),
        ('message_sent', 'Message Sent'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='networking_interactions')
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='networking_interactions_received')
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    
    interaction_type = models.CharField(max_length=30, choices=INTERACTION_TYPES)
    interaction_data = models.JSONField(default=dict, help_text="Additional interaction context")
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'event', 'timestamp']),
            models.Index(fields=['event', 'interaction_type', 'timestamp']),
        ]
    
    def __str__(self):
        if self.target_user:
            return f"{self.user.username} - {self.interaction_type} - {self.target_user.username}"
        return f"{self.user.username} - {self.interaction_type}"


class EventNetworkingSettings(models.Model):
    """Networking settings for specific events"""
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='networking_settings')
    
    # Feature toggles
    enable_networking = models.BooleanField(default=True)
    enable_attendee_directory = models.BooleanField(default=True)
    enable_qr_exchange = models.BooleanField(default=True)
    enable_contact_export = models.BooleanField(default=True)
    
    # Directory settings
    allow_industry_filter = models.BooleanField(default=True)
    allow_interest_filter = models.BooleanField(default=True)
    allow_company_filter = models.BooleanField(default=True)
    
    # Privacy settings
    require_mutual_consent = models.BooleanField(default=False)
    allow_anonymous_browsing = models.BooleanField(default=True)
    
    # Gamification settings
    networking_points_enabled = models.BooleanField(default=True)
    points_per_connection = models.IntegerField(default=5)
    max_daily_networking_points = models.IntegerField(default=100)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Networking Settings - {self.event.name}"
