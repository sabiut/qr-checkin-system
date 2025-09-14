from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from events.models import Event
import uuid


class Message(models.Model):
    """Direct messages between connected users"""
    MESSAGE_STATUS = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('email_sent', 'Email Sent'),  # For guests without accounts
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages', null=True, blank=True)
    recipient_email = models.EmailField(null=True, blank=True, help_text="Email for guests without accounts")
    recipient_invitation = models.ForeignKey('invitations.Invitation', on_delete=models.CASCADE, null=True, blank=True, related_name='messages')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='event_messages', null=True, blank=True)
    
    content = models.TextField()
    status = models.CharField(max_length=20, choices=MESSAGE_STATUS, default='sent')
    
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Message from {self.sender.username} to {self.recipient.username}'
    
    def mark_as_read(self):
        if not self.read_at:
            self.read_at = timezone.now()
            self.status = 'read'
            self.save(update_fields=['read_at', 'status'])


class Announcement(models.Model):
    """Event announcements from organizers"""
    ANNOUNCEMENT_TYPES = [
        ('general', 'General'),
        ('schedule', 'Schedule Update'),
        ('urgent', 'Urgent'),
        ('reminder', 'Reminder'),
        ('venue', 'Venue Information'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='announcements')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcements_created')
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    announcement_type = models.CharField(max_length=20, choices=ANNOUNCEMENT_TYPES, default='general')
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='normal')
    
    # Scheduling
    is_scheduled = models.BooleanField(default=False)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    
    # Targeting
    target_all = models.BooleanField(default=True)
    target_attendees = models.ManyToManyField(User, blank=True, related_name='targeted_announcements')
    
    # Push notification settings
    send_push = models.BooleanField(default=True)
    send_email = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Tracking
    is_published = models.BooleanField(default=False)
    view_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.event.name}"


class AnnouncementRead(models.Model):
    """Track which users have read announcements"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='reads')
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'announcement']


class ForumThread(models.Model):
    """Discussion threads for events"""
    THREAD_CATEGORIES = [
        ('general', 'General Discussion'),
        ('networking', 'Networking'),
        ('logistics', 'Logistics & Travel'),
        ('content', 'Session Content'),
        ('social', 'Social Activities'),
        ('feedback', 'Feedback & Suggestions'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='forum_threads')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_threads')
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=20, choices=THREAD_CATEGORIES, default='general')
    
    # Thread status
    is_pinned = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    
    # Engagement metrics
    view_count = models.IntegerField(default=0)
    reply_count = models.IntegerField(default=0)
    like_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_pinned', '-last_activity']
    
    def __str__(self):
        return f"{self.title} - {self.event.name}"
    
    def update_activity(self):
        self.last_activity = timezone.now()
        self.save()


class ForumPost(models.Model):
    """Replies to forum threads"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thread = models.ForeignKey(ForumThread, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_posts')
    
    content = models.TextField()
    parent_post = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    
    # Moderation
    is_hidden = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)
    
    # Engagement
    like_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Reply by {self.author.username} on {self.thread.title}"
    
    def save(self, *args, **kwargs):
        is_new = not self.pk
        super().save(*args, **kwargs)
        if is_new:
            self.thread.reply_count += 1
            self.thread.update_activity()


class QAQuestion(models.Model):
    """Questions for speakers/organizers"""
    QUESTION_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('answered', 'Answered'),
        ('rejected', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='qa_questions')
    session_name = models.CharField(max_length=200, blank=True, help_text="Specific session/speaker if applicable")
    
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='qa_questions')
    question = models.TextField()
    status = models.CharField(max_length=20, choices=QUESTION_STATUS, default='pending')
    
    # Voting
    upvotes = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    
    # Anonymous option
    is_anonymous = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    answered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-upvotes', '-created_at']
    
    def __str__(self):
        author_name = "Anonymous" if self.is_anonymous else self.author.username
        return f"Q by {author_name}: {self.question[:50]}..."


class QAAnswer(models.Model):
    """Answers to Q&A questions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(QAQuestion, on_delete=models.CASCADE, related_name='answers')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='qa_answers')
    
    answer = models.TextField()
    is_official = models.BooleanField(default=False, help_text="Is this from speaker/organizer?")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_official', 'created_at']
    
    def __str__(self):
        return f"Answer by {self.author.username}"
    
    def save(self, *args, **kwargs):
        is_new = not self.pk
        super().save(*args, **kwargs)
        if is_new and self.is_official:
            self.question.status = 'answered'
            self.question.answered_at = timezone.now()
            self.question.save()




class NotificationPreference(models.Model):
    """User notification preferences"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Message notifications
    notify_direct_messages = models.BooleanField(default=True)
    notify_message_email = models.BooleanField(default=False)
    
    # Announcement notifications
    notify_announcements = models.BooleanField(default=True)
    notify_urgent_only = models.BooleanField(default=False)
    
    # Forum notifications
    notify_forum_replies = models.BooleanField(default=True)
    notify_forum_mentions = models.BooleanField(default=True)
    
    # Q&A notifications
    notify_qa_answers = models.BooleanField(default=True)
    
    # Push notification tokens
    fcm_token = models.TextField(blank=True, help_text="Firebase Cloud Messaging token")
    device_type = models.CharField(max_length=20, blank=True, choices=[('ios', 'iOS'), ('android', 'Android'), ('web', 'Web')])
    
    # Quiet hours
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Notification preferences for {self.user.username}"


class IcebreakerActivity(models.Model):
    """Pre-event icebreaker activities to encourage engagement"""

    # Extended activity types (keeping existing ones and adding new ones)
    ACTIVITY_TYPES = [
        ('poll', 'Poll'),
        ('quiz', 'Quiz'),
        ('question', 'Question'),
        ('challenge', 'Challenge'),
        ('introduction', 'Introduction'),
        ('prediction', 'Event Prediction'),
        ('skill_sharing', 'Skill Sharing'),
        ('goal_setting', 'Goal Setting'),
        ('fun_fact', 'Fun Fact Sharing'),
        ('networking_challenge', 'Networking Challenge'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE, related_name='icebreaker_activities')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_icebreakers')

    # Core fields (matching existing migration)
    title = models.CharField(max_length=200)
    description = models.TextField()
    activity_type = models.CharField(
        max_length=20,
        choices=ACTIVITY_TYPES,
        default='question'
    )
    activity_data = models.JSONField(
        default=dict,
        help_text='Poll options, quiz questions, etc.'
    )
    is_active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    points_reward = models.IntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)

    # Additional fields (these will need a migration)
    is_featured = models.BooleanField(default=False, help_text="Show prominently in the app")
    allow_multiple_responses = models.BooleanField(default=False)
    anonymous_responses = models.BooleanField(default=False)
    response_count = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    # Guest response system
    guest_response_token = models.CharField(max_length=64, unique=True, null=True, blank=True,
                                          help_text="Unique token for guest access")
    email_sent = models.BooleanField(default=False, help_text="Whether invitation emails were sent")
    email_sent_at = models.DateTimeField(null=True, blank=True, help_text="When invitation emails were sent")
    send_email_on_create = models.BooleanField(default=True, help_text="Send emails to invitees when activity is created")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.event.name}"

    def save(self, *args, **kwargs):
        """Generate guest response token on creation"""
        if not self.guest_response_token:
            import secrets
            self.guest_response_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def get_guest_response_url(self, request=None):
        """Get the public URL for guest responses"""
        from django.conf import settings

        if request:
            base_url = f"{request.scheme}://{request.get_host()}"
        else:
            # Use BASE_URL which is already configured in production as https://eventqr.app
            base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
            # BASE_URL points to backend, but we need frontend URL for React routes
            # In production, BASE_URL is set to https://eventqr.app which is correct
            # In dev, we need to use localhost:5173 for frontend
            if 'localhost:8000' in base_url or '127.0.0.1:8000' in base_url:
                base_url = 'http://localhost:5173'

        return f"{base_url}/icebreaker/{self.guest_response_token}"

    def is_currently_active(self):
        """Check if activity is currently active"""
        now = timezone.now()
        return (self.is_active and
                self.starts_at and self.ends_at and
                self.starts_at <= now <= self.ends_at)

    def days_until_start(self):
        """Days until activity starts"""
        if not self.starts_at or self.starts_at <= timezone.now():
            return 0
        return (self.starts_at - timezone.now()).days


class IcebreakerResponse(models.Model):
    """User responses to icebreaker activities"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    activity = models.ForeignKey(IcebreakerActivity, on_delete=models.CASCADE, related_name='responses')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='icebreaker_responses', null=True, blank=True)

    # Core fields (matching existing migration)
    response_data = models.JSONField(default=dict)
    is_public = models.BooleanField(default=True)
    points_earned = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    # Additional fields (these will need a migration)
    like_count = models.IntegerField(default=0)
    reply_count = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    # Guest response fields
    guest_email = models.EmailField(null=True, blank=True, help_text="Email for guest responses")
    guest_name = models.CharField(max_length=100, null=True, blank=True, help_text="Name for guest responses")
    is_guest_response = models.BooleanField(default=False, help_text="Whether this is a guest response")

    # Enhanced gamification fields
    base_points = models.IntegerField(default=0, help_text="Base points for activity type")
    speed_bonus = models.IntegerField(default=0, help_text="Bonus points for quick response")
    quality_bonus = models.IntegerField(default=0, help_text="Bonus points for quality response")
    social_bonus = models.IntegerField(default=0, help_text="Bonus points from likes/engagement")
    streak_multiplier = models.FloatField(default=1.0, help_text="Streak bonus multiplier")
    lucky_multiplier = models.FloatField(default=1.0, help_text="Random lucky bonus multiplier")
    response_time_seconds = models.IntegerField(null=True, blank=True, help_text="Time taken to respond in seconds")
    quality_score = models.FloatField(default=0.0, help_text="AI-generated quality score (0-10)")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        if self.is_guest_response:
            return f"{self.guest_name or self.guest_email} (guest) - {self.activity.title}"
        return f"{self.user.username} - {self.activity.title}"

    # Helper properties for easier access to response data
    @property
    def text_response(self):
        return self.response_data.get('text', '')

    @property
    def selected_option(self):
        return self.response_data.get('selected_option', '')

    def calculate_points(self, save=True):
        """Calculate total points with all bonuses and multipliers"""
        import random
        from datetime import timedelta

        # Get or create gamification profile for both users and guests
        if self.is_guest_response:
            # Handle guest responses
            profile, created = UserGamificationProfile.objects.get_or_create(
                guest_email=self.guest_email,
                event=self.activity.event,
                defaults={
                    'guest_name': self.guest_name,
                }
            )
        else:
            # Handle authenticated user responses
            if not self.user:
                self.points_earned = 0
                if save:
                    self.save(update_fields=['points_earned'])
                return 0

            profile, created = UserGamificationProfile.objects.get_or_create(
                user=self.user,
                event=self.activity.event
            )

        # 1. Base points from activity type
        activity_type_points = {
            'poll': 10,
            'quiz': 25,
            'question': 15,
            'challenge': 15,
            'introduction': 20,
            'prediction': 12,
            'skill_sharing': 18,
            'goal_setting': 16,
            'fun_fact': 14,
            'networking_challenge': 20,
        }
        self.base_points = activity_type_points.get(self.activity.activity_type, 10)

        # 2. Speed bonus (within 10 minutes of activity start)
        self.speed_bonus = 0
        if self.response_time_seconds and self.response_time_seconds <= 600:  # 10 minutes
            self.speed_bonus = 5

        # 3. Quality bonus (based on response length/detail for text responses)
        self.quality_bonus = 0
        if self.activity.activity_type in ['question', 'challenge', 'introduction']:
            text = self.text_response.strip()
            if len(text) > 100:  # Detailed response
                self.quality_bonus = 5
            elif len(text) > 50:  # Moderate response
                self.quality_bonus = 3

        # 4. Social bonus (based on engagement this response already has)
        self.social_bonus = min(self.like_count * 2, 20)  # Max 20 bonus points from likes

        # 5. Streak multiplier
        self.streak_multiplier = profile.get_streak_multiplier()

        # 6. Lucky multiplier (10% chance of 2x-5x)
        self.lucky_multiplier = 1.0
        if random.random() < 0.1:  # 10% chance
            self.lucky_multiplier = random.uniform(2.0, 5.0)
            profile.lucky_bonus_count += 1

        # Calculate total points
        subtotal = self.base_points + self.speed_bonus + self.quality_bonus + self.social_bonus
        total_with_streak = subtotal * self.streak_multiplier
        final_total = total_with_streak * self.lucky_multiplier

        self.points_earned = int(final_total)

        # Update user profile
        if created or profile.activities_completed == 0:
            # First activity
            profile.update_streak()

        profile.total_points += self.points_earned
        profile.base_points += self.base_points
        profile.bonus_points += (self.points_earned - self.base_points)
        profile.activities_completed += 1

        if self.lucky_multiplier > 1.0:
            profile.total_lucky_points += int(final_total - total_with_streak)

        profile.save()

        if save:
            self.save(update_fields=[
                'points_earned', 'base_points', 'speed_bonus', 'quality_bonus',
                'social_bonus', 'streak_multiplier', 'lucky_multiplier'
            ])

        return self.points_earned


class IcebreakerResponseLike(models.Model):
    """Track likes on icebreaker responses"""

    response = models.ForeignKey(IcebreakerResponse, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['response', 'user']

    def __str__(self):
        return f"{self.user.username} likes {self.response.activity.title}"


class IcebreakerResponseReply(models.Model):
    """Replies to icebreaker responses for discussion"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    response = models.ForeignKey(IcebreakerResponse, on_delete=models.CASCADE, related_name='replies')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name_plural = "Icebreaker Response Replies"

    def __str__(self):
        return f"Reply by {self.user.username} on {self.response.activity.title}"


class UserGamificationProfile(models.Model):
    """Track user's gamification data and achievements for icebreakers"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='icebreaker_profile', null=True, blank=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='user_profiles')

    # Guest identification fields
    guest_email = models.EmailField(null=True, blank=True, help_text="Email for guest users")
    guest_name = models.CharField(max_length=200, null=True, blank=True, help_text="Name for guest users")

    # Points tracking
    total_points = models.IntegerField(default=0)
    base_points = models.IntegerField(default=0)
    bonus_points = models.IntegerField(default=0)

    # Streak tracking
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)

    # Speed stats
    average_response_time = models.FloatField(default=0.0, help_text="Average response time in seconds")
    fastest_response_time = models.IntegerField(null=True, blank=True, help_text="Fastest response in seconds")

    # Engagement stats
    activities_completed = models.IntegerField(default=0)
    likes_received = models.IntegerField(default=0)
    likes_given = models.IntegerField(default=0)
    replies_received = models.IntegerField(default=0)
    replies_given = models.IntegerField(default=0)

    # Lucky multiplier tracking
    lucky_bonus_count = models.IntegerField(default=0)
    total_lucky_points = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Ensure unique profiles for authenticated users and guests
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'event'],
                condition=models.Q(user__isnull=False),
                name='unique_user_event'
            ),
            models.UniqueConstraint(
                fields=['guest_email', 'event'],
                condition=models.Q(guest_email__isnull=False),
                name='unique_guest_email_event'
            ),
        ]
        ordering = ['-total_points']

    def __str__(self):
        if self.user:
            return f"{self.user.username} - {self.event.name} ({self.total_points} pts)"
        else:
            name = self.guest_name or self.guest_email or "Guest"
            return f"{name} (guest) - {self.event.name} ({self.total_points} pts)"

    def update_streak(self, activity_date=None):
        """Update user's streak based on activity participation"""
        from datetime import date, timedelta

        activity_date = activity_date or date.today()

        if not self.last_activity_date:
            # First activity
            self.current_streak = 1
            self.longest_streak = 1
        elif self.last_activity_date == activity_date:
            # Same day, no change to streak
            return
        elif self.last_activity_date == activity_date - timedelta(days=1):
            # Consecutive day
            self.current_streak += 1
            self.longest_streak = max(self.longest_streak, self.current_streak)
        else:
            # Streak broken
            self.current_streak = 1

        self.last_activity_date = activity_date
        self.save(update_fields=['current_streak', 'longest_streak', 'last_activity_date'])

    def get_streak_multiplier(self):
        """Calculate streak multiplier based on current streak"""
        if self.current_streak >= 7:
            return 2.0  # Double points for 7+ day streak
        elif self.current_streak >= 5:
            return 1.8  # 80% bonus for 5-6 day streak
        elif self.current_streak >= 3:
            return 1.5  # 50% bonus for 3-4 day streak
        else:
            return 1.0  # No bonus


class IcebreakerAchievement(models.Model):
    """Define icebreaker achievements users can unlock"""

    ACHIEVEMENT_TYPES = [
        ('streak', 'Streak Achievement'),
        ('speed', 'Speed Achievement'),
        ('social', 'Social Achievement'),
        ('participation', 'Participation Achievement'),
        ('quality', 'Quality Achievement'),
        ('lucky', 'Lucky Achievement'),
    ]

    ACHIEVEMENT_TIERS = [
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    achievement_type = models.CharField(max_length=20, choices=ACHIEVEMENT_TYPES)
    tier = models.CharField(max_length=20, choices=ACHIEVEMENT_TIERS, default='bronze')

    # Requirements
    required_value = models.IntegerField(help_text="Value needed to unlock (streak days, speed seconds, etc.)")
    points_reward = models.IntegerField(default=0, help_text="Bonus points for unlocking")

    # Display
    icon = models.CharField(max_length=10, default='🏆', help_text="Emoji icon for achievement")
    is_hidden = models.BooleanField(default=False, help_text="Hidden until unlocked")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['achievement_type', 'tier', 'required_value']
        ordering = ['achievement_type', 'required_value']

    def __str__(self):
        return f"{self.icon} {self.name} ({self.tier})"


class UserIcebreakerAchievement(models.Model):
    """Track which icebreaker achievements users have unlocked"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='icebreaker_achievements')
    achievement = models.ForeignKey(IcebreakerAchievement, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='user_achievements')

    # Unlock details
    unlocked_at = models.DateTimeField(auto_now_add=True)
    trigger_value = models.IntegerField(help_text="Value that triggered the unlock")

    class Meta:
        unique_together = ['user', 'achievement', 'event']
        ordering = ['-unlocked_at']

    def __str__(self):
        return f"{self.user.username} unlocked {self.achievement.name}"


class ResponseReaction(models.Model):
    """Enhanced reactions beyond just likes"""

    REACTION_TYPES = [
        ('like', '👍'),
        ('love', '❤️'),
        ('laugh', '😂'),
        ('wow', '😲'),
        ('think', '🤔'),
        ('fire', '🔥'),
    ]

    response = models.ForeignKey(IcebreakerResponse, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=10, choices=REACTION_TYPES, default='like')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['response', 'user']

    def __str__(self):
        return f"{self.user.username} reacted {self.get_reaction_type_display()} to {self.response.activity.title}"
