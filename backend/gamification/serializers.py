from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    AttendeeProfile, Badge, UserBadge, Achievement, LeaderboardEntry
)


class BadgeSerializer(serializers.ModelSerializer):
    """Serializer for Badge model"""
    
    class Meta:
        model = Badge
        fields = [
            'id', 'name', 'description', 'badge_type', 'icon', 'color',
            'points_reward', 'is_active', 'created_at'
        ]


class UserBadgeSerializer(serializers.ModelSerializer):
    """Serializer for UserBadge model"""
    badge = BadgeSerializer(read_only=True)
    event_name = serializers.CharField(source='event.name', read_only=True)
    
    class Meta:
        model = UserBadge
        fields = ['id', 'badge', 'event_name', 'earned_at']


class AttendeeProfileSerializer(serializers.ModelSerializer):
    """Serializer for AttendeeProfile model"""
    username = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.SerializerMethodField()
    badges_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AttendeeProfile
        fields = [
            'id', 'username', 'full_name', 'current_streak', 'longest_streak',
            'total_events_attended', 'total_points', 'level', 'badges_count',
            'last_attended_date', 'created_at'
        ]
    
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    
    def get_badges_count(self, obj):
        return obj.user.earned_badges.count()


class AchievementSerializer(serializers.ModelSerializer):
    """Serializer for Achievement model"""
    event_name = serializers.CharField(source='event.name', read_only=True)
    
    class Meta:
        model = Achievement
        fields = [
            'id', 'title', 'description', 'icon', 'event_name',
            'achieved_at', 'data'
        ]


class LeaderboardEntrySerializer(serializers.ModelSerializer):
    """Serializer for LeaderboardEntry model"""
    username = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = LeaderboardEntry
        fields = [
            'rank', 'username', 'full_name', 'events_attended',
            'points_earned', 'current_streak', 'badges_earned'
        ]
    
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


class UserStatsSerializer(serializers.Serializer):
    """Serializer for comprehensive user gamification stats"""
    profile = AttendeeProfileSerializer(read_only=True)
    badges = UserBadgeSerializer(many=True, read_only=True)
    recent_achievements = AchievementSerializer(many=True, read_only=True)
    monthly_rank = serializers.IntegerField(allow_null=True)
    level_progress = serializers.FloatField()
    next_badge = serializers.SerializerMethodField()
    
    def get_next_badge(self, obj):
        next_badge = obj.get('next_badge')
        if next_badge and isinstance(next_badge, dict):
            return {
                'badge': BadgeSerializer(next_badge['badge']).data,
                'progress': next_badge['progress']
            }
        return None


class LeaderboardSerializer(serializers.Serializer):
    """Serializer for leaderboard data"""
    period = serializers.CharField()
    entries = serializers.ListSerializer(child=LeaderboardEntrySerializer(), read_only=True)
    user_rank = serializers.IntegerField(allow_null=True)
    total_participants = serializers.IntegerField()