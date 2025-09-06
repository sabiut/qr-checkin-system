from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import (
    AttendeeProfile, Badge, UserBadge, LeaderboardEntry, Achievement
)


@admin.register(AttendeeProfile)
class AttendeeProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'level', 'total_points', 'current_streak', 
        'longest_streak', 'total_events_attended', 'badge_count'
    )
    list_filter = ('level', 'current_streak')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at', 'badge_count', 'level_progress')
    
    fieldsets = (
        ('User Info', {
            'fields': ('user', 'level', 'level_progress')
        }),
        ('Points & Stats', {
            'fields': ('total_points', 'total_events_attended', 'badge_count')
        }),
        ('Streak Info', {
            'fields': ('current_streak', 'longest_streak', 'last_attended_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').annotate(
            badge_count=Count('user__earned_badges')
        )
    
    def badge_count(self, obj):
        return obj.badge_count
    badge_count.short_description = 'Badges Earned'
    badge_count.admin_order_field = 'badge_count'
    
    def level_progress(self, obj):
        """Show progress bar for level advancement"""
        from .services import GamificationStatsService
        service = GamificationStatsService()
        progress = service._calculate_level_progress(obj)
        
        return format_html(
            '<div style="width: 200px; background-color: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; background-color: #4CAF50; height: 20px; border-radius: 3px; text-align: center; line-height: 20px; color: white; font-size: 12px;">'
            '{}%</div></div>',
            progress, int(progress)
        )
    level_progress.short_description = 'Level Progress'


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('icon_display', 'name', 'badge_type', 'points_reward', 'earned_count', 'is_active')
    list_filter = ('badge_type', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('earned_count', 'created_at')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description', 'badge_type', 'is_active')
        }),
        ('Appearance', {
            'fields': ('icon', 'color')
        }),
        ('Rewards & Criteria', {
            'fields': ('points_reward', 'criteria')
        }),
        ('Stats', {
            'fields': ('earned_count', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            earned_count=Count('userbadge')
        )
    
    def icon_display(self, obj):
        return format_html(
            '<span style="font-size: 20px; color: {};">{}</span>',
            obj.color, obj.icon
        )
    icon_display.short_description = 'Icon'
    
    def earned_count(self, obj):
        return obj.earned_count
    earned_count.short_description = 'Times Earned'
    earned_count.admin_order_field = 'earned_count'
    
    actions = ['create_sample_badges']
    
    def create_sample_badges(self, request, queryset):
        """Action to create sample badges for testing"""
        sample_badges = [
            {
                'name': 'Early Bird',
                'description': 'Check in 30 minutes before event starts',
                'badge_type': 'punctuality',
                'icon': '🐦',
                'color': '#FFD700',
                'criteria': {'min_minutes_early': 30, 'max_minutes_early': 180},
                'points_reward': 15
            },
            {
                'name': 'Attendance Champion',
                'description': 'Attend 10 events',
                'badge_type': 'attendance',
                'icon': '🏆',
                'color': '#4CAF50',
                'criteria': {'events_required': 10, 'time_period': 'all_time'},
                'points_reward': 50
            },
            {
                'name': 'Streak Master',
                'description': 'Maintain a 7-day attendance streak',
                'badge_type': 'streak',
                'icon': '🔥',
                'color': '#FF4444',
                'criteria': {'streak_required': 7, 'streak_type': 'current'},
                'points_reward': 25
            },
            {
                'name': 'Social Butterfly',
                'description': 'Attend 5 networking events',
                'badge_type': 'networking',
                'icon': '🦋',
                'color': '#9C27B0',
                'criteria': {'events_for_networking': 5},
                'points_reward': 20
            },
            {
                'name': 'VIP Guest',
                'description': 'Special badge for VIP attendees',
                'badge_type': 'special',
                'icon': '⭐',
                'color': '#FF9800',
                'criteria': {'event_type': 'vip'},
                'points_reward': 100
            }
        ]
        
        created_count = 0
        for badge_data in sample_badges:
            badge, created = Badge.objects.get_or_create(
                name=badge_data['name'],
                defaults=badge_data
            )
            if created:
                created_count += 1
        
        self.message_user(
            request,
            f"Created {created_count} sample badges. ({len(sample_badges) - created_count} already existed)"
        )
    
    create_sample_badges.short_description = "Create sample badges for testing"


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge_icon', 'badge_name', 'event', 'earned_at')
    list_filter = ('badge__badge_type', 'earned_at', 'badge')
    search_fields = ('user__username', 'badge__name', 'event__name')
    readonly_fields = ('earned_at',)
    
    def badge_icon(self, obj):
        return format_html(
            '<span style="font-size: 16px;">{}</span>',
            obj.badge.icon
        )
    badge_icon.short_description = 'Icon'
    
    def badge_name(self, obj):
        return obj.badge.name
    badge_name.short_description = 'Badge'
    badge_name.admin_order_field = 'badge__name'


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'icon', 'event', 'achieved_at')
    list_filter = ('achieved_at', 'event')
    search_fields = ('user__username', 'title', 'description')
    readonly_fields = ('achieved_at', 'data_display')
    
    fieldsets = (
        ('Achievement Info', {
            'fields': ('user', 'title', 'description', 'icon')
        }),
        ('Context', {
            'fields': ('event', 'achieved_at')
        }),
        ('Data', {
            'fields': ('data_display',),
            'classes': ('collapse',)
        })
    )
    
    def data_display(self, obj):
        """Display achievement data in a readable format"""
        if obj.data:
            formatted_data = []
            for key, value in obj.data.items():
                formatted_data.append(f"<strong>{key}:</strong> {value}")
            return format_html("<br>".join(formatted_data))
        return "No additional data"
    data_display.short_description = 'Achievement Data'


@admin.register(LeaderboardEntry)
class LeaderboardEntryAdmin(admin.ModelAdmin):
    list_display = (
        'rank', 'user', 'period', 'period_date', 
        'events_attended', 'points_earned', 'current_streak'
    )
    list_filter = ('period', 'period_date', 'rank')
    search_fields = ('user__username',)
    readonly_fields = ('created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


# Custom admin actions
def award_badge_to_users(modeladmin, request, queryset):
    """Custom action to award a badge to selected users"""
    # This would open a form to select badge and award it
    pass

award_badge_to_users.short_description = "Award badge to selected users"


# Register the action with AttendeeProfileAdmin
AttendeeProfileAdmin.actions = [award_badge_to_users]