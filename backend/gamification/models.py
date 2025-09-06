from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from events.models import Event
from attendance.models import Attendance
import json


class AttendeeProfile(models.Model):
    """Extended user profile for gamification features"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='gamification_profile')
    
    # Streak tracking
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_attended_date = models.DateField(null=True, blank=True)
    
    # Overall stats
    total_events_attended = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)
    level = models.CharField(max_length=20, default='Bronze')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-total_points', '-current_streak']
    
    def __str__(self):
        return f"{self.user.username} - Level {self.level} ({self.total_points} pts)"
    
    def update_streak(self, event_date):
        """Update streak based on event attendance"""
        if self.last_attended_date:
            # Calculate days between last attendance and current event
            days_diff = (event_date - self.last_attended_date).days
            
            if days_diff == 1:
                # Consecutive day - increment streak
                self.current_streak += 1
            elif days_diff > 1:
                # Gap in attendance - reset streak
                self.current_streak = 1
            # If days_diff == 0 (same day), don't change streak
        else:
            # First event attended
            self.current_streak = 1
        
        # Update longest streak
        self.longest_streak = max(self.longest_streak, self.current_streak)
        self.last_attended_date = event_date
        self.save()
    
    def add_points(self, points):
        """Add points and check for level up"""
        self.total_points += points
        self.update_level()
        self.save()
    
    def update_level(self):
        """Update user level based on total points"""
        if self.total_points >= 1000:
            self.level = 'Platinum'
        elif self.total_points >= 500:
            self.level = 'Gold'
        elif self.total_points >= 200:
            self.level = 'Silver'
        else:
            self.level = 'Bronze'


class Badge(models.Model):
    """Achievement badges that users can earn"""
    BADGE_TYPES = [
        ('attendance', 'Attendance'),
        ('punctuality', 'Punctuality'),
        ('streak', 'Streak'),
        ('networking', 'Networking'),
        ('special', 'Special'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    badge_type = models.CharField(max_length=20, choices=BADGE_TYPES)
    icon = models.CharField(max_length=50, default='🏆')  # Emoji or icon class
    color = models.CharField(max_length=7, default='#FFD700')  # Hex color
    
    # Badge criteria (stored as JSON)
    criteria = models.JSONField(default=dict)
    points_reward = models.IntegerField(default=10)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['badge_type', 'name']
    
    def __str__(self):
        return f"{self.icon} {self.name}"


class UserBadge(models.Model):
    """Badges earned by users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='earned_badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True)
    
    earned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'badge']
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.badge.name}"


class LeaderboardEntry(models.Model):
    """Leaderboard snapshots for different time periods"""
    PERIOD_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('all_time', 'All Time'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    period_date = models.DateField()  # Date representing the period
    
    # Metrics for ranking
    events_attended = models.IntegerField(default=0)
    points_earned = models.IntegerField(default=0)
    current_streak = models.IntegerField(default=0)
    badges_earned = models.IntegerField(default=0)
    
    rank = models.IntegerField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'period', 'period_date']
        ordering = ['period', 'rank']
    
    def __str__(self):
        return f"#{self.rank} {self.user.username} - {self.period} {self.period_date}"


class Achievement(models.Model):
    """User achievements and milestones"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    title = models.CharField(max_length=200)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='🎯')
    
    achieved_at = models.DateTimeField(auto_now_add=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True)
    
    # Achievement data (flexible JSON field)
    data = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-achieved_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"