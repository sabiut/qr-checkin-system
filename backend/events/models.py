from django.db import models
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)

class Event(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=255)
    max_attendees = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
        
    # We'll rely on the serializer instead of these properties to avoid 500 errors
    # These are kept for reference but not used directly in the serializer
    
    @property
    def attendee_count(self):
        try:
            return self.invitations.filter(
                attendance__isnull=False,
                attendance__has_attended=True
            ).count()
        except Exception as e:
            logger.error(f"Error calculating attendee_count for event {self.pk}: {str(e)}")
            return 0
    
    @property
    def is_full(self):
        try:
            if self.max_attendees:
                return self.attendee_count >= self.max_attendees
            return False
        except Exception as e:
            logger.error(f"Error calculating is_full for event {self.pk}: {str(e)}")
            return False