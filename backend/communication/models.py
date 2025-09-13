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


class IcebreakerActivity(models.Model):
    """Pre-event icebreaker activities"""
    ACTIVITY_TYPES = [
        ('poll', 'Poll'),
        ('quiz', 'Quiz'),
        ('question', 'Question'),
        ('challenge', 'Challenge'),
        ('introduction', 'Introduction'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='icebreaker_activities')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_icebreakers')
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES, default='question')
    
    # Activity data (JSON for flexibility)
    activity_data = models.JSONField(default=dict, help_text="Poll options, quiz questions, etc.")
    
    # Scheduling
    is_active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    
    # Gamification
    points_reward = models.IntegerField(default=5)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.event.name}"


class IcebreakerResponse(models.Model):
    """User responses to icebreaker activities"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    activity = models.ForeignKey(IcebreakerActivity, on_delete=models.CASCADE, related_name='responses')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='icebreaker_responses')
    
    response_data = models.JSONField(default=dict)
    is_public = models.BooleanField(default=True)
    
    # Gamification
    points_earned = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['activity', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}'s response to {self.activity.title}"


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
