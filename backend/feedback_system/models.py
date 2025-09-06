from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class FeedbackTag(models.Model):
    """Predefined tags for categorizing feedback."""
    CATEGORY_CHOICES = [
        ('content', 'Content'),
        ('venue', 'Venue'),
        ('organization', 'Organization'),
        ('technical', 'Technical'),
        ('catering', 'Catering'),
        ('networking', 'Networking'),
        ('speaker', 'Speaker'),
        ('general', 'General'),
    ]
    
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    icon = models.CharField(max_length=10, default='🏷️')
    description = models.TextField(blank=True)
    is_positive = models.BooleanField(default=True)  # True for positive, False for negative
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['name', 'category']
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.icon} {self.name} ({self.category})"


class EventFeedback(models.Model):
    """Main feedback model for events."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE, related_name='feedback_responses')
    invitation = models.ForeignKey('invitations.Invitation', on_delete=models.CASCADE, null=True, blank=True)
    
    # Respondent info
    respondent_name = models.CharField(max_length=255, blank=True)
    respondent_email = models.EmailField()
    is_anonymous = models.BooleanField(default=False)
    
    # Overall ratings (1-5 scale)
    overall_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Overall event rating (1-5 stars)"
    )
    venue_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="Venue rating (1-5 stars)"
    )
    content_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="Content quality rating (1-5 stars)"
    )
    organization_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="Event organization rating (1-5 stars)"
    )
    
    # Net Promoter Score (0-10)
    nps_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        null=True, blank=True,
        help_text="How likely are you to recommend this event? (0-10)"
    )
    
    # Text feedback
    what_went_well = models.TextField(
        blank=True,
        help_text="What did you enjoy most about the event?"
    )
    what_needs_improvement = models.TextField(
        blank=True,
        help_text="What could be improved for future events?"
    )
    additional_comments = models.TextField(
        blank=True,
        help_text="Any additional feedback or suggestions?"
    )
    
    # Recommendation and future engagement
    would_recommend = models.BooleanField(null=True, blank=True)
    would_attend_future = models.BooleanField(null=True, blank=True)
    interested_topics = models.TextField(
        blank=True,
        help_text="What topics would you like to see in future events?"
    )
    
    # Tags
    tags = models.ManyToManyField(FeedbackTag, blank=True)
    
    # Metadata
    submission_source = models.CharField(
        max_length=50,
        choices=[
            ('email', 'Email Survey'),
            ('ticket', 'Ticket Page'),
            ('qr_code', 'QR Code Scan'),
            ('web_portal', 'Web Portal'),
            ('manual', 'Manual Entry'),
        ],
        default='email'
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Gamification tracking
    gamification_processed = models.BooleanField(default=False)
    points_awarded = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['event', 'respondent_email']
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"Feedback for {self.event.name} from {self.respondent_email}"
    
    @property
    def average_rating(self):
        """Calculate average of all non-null ratings."""
        ratings = [
            r for r in [
                self.overall_rating,
                self.venue_rating,
                self.content_rating,
                self.organization_rating
            ] if r is not None
        ]
        return sum(ratings) / len(ratings) if ratings else None
    
    @property
    def nps_category(self):
        """Categorize NPS score as Detractor, Passive, or Promoter."""
        if self.nps_score is None:
            return None
        elif self.nps_score <= 6:
            return 'Detractor'
        elif self.nps_score <= 8:
            return 'Passive'
        else:
            return 'Promoter'


class FeedbackAnalytics(models.Model):
    """Aggregated analytics for events."""
    event = models.OneToOneField('events.Event', on_delete=models.CASCADE, related_name='feedback_analytics')
    
    # Response stats
    total_responses = models.IntegerField(default=0)
    response_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)  # Percentage
    
    # Rating averages
    avg_overall_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    avg_venue_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    avg_content_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    avg_organization_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    
    # NPS stats
    avg_nps_score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    nps_detractors = models.IntegerField(default=0)
    nps_passives = models.IntegerField(default=0)
    nps_promoters = models.IntegerField(default=0)
    net_promoter_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Recommendation stats
    would_recommend_count = models.IntegerField(default=0)
    would_attend_future_count = models.IntegerField(default=0)
    
    # Most common tags
    top_positive_tags = models.JSONField(default=list, blank=True)
    top_negative_tags = models.JSONField(default=list, blank=True)
    
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Analytics for {self.event.name}"
    
    def calculate_nps(self):
        """Calculate Net Promoter Score."""
        total = self.nps_detractors + self.nps_passives + self.nps_promoters
        if total == 0:
            return None
        
        promoter_percentage = (self.nps_promoters / total) * 100
        detractor_percentage = (self.nps_detractors / total) * 100
        return promoter_percentage - detractor_percentage