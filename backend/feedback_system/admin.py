from django.contrib import admin
from django.utils.html import format_html
from .models import FeedbackTag, EventFeedback, FeedbackAnalytics


@admin.register(FeedbackTag)
class FeedbackTagAdmin(admin.ModelAdmin):
    list_display = ['icon', 'name', 'category', 'is_positive', 'created_at']
    list_filter = ['category', 'is_positive', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['category', 'name']


@admin.register(EventFeedback)
class EventFeedbackAdmin(admin.ModelAdmin):
    list_display = [
        'event', 'respondent_name', 'respondent_email', 'overall_rating',
        'submission_source', 'submitted_at', 'gamification_processed'
    ]
    list_filter = [
        'overall_rating', 'submission_source', 'submitted_at', 
        'would_recommend', 'would_attend_future', 'gamification_processed'
    ]
    search_fields = ['respondent_name', 'respondent_email', 'event__name']
    readonly_fields = ['id', 'submitted_at', 'ip_address', 'user_agent', 'average_rating', 'nps_category']
    filter_horizontal = ['tags']
    
    fieldsets = (
        ('Event Information', {
            'fields': ('id', 'event', 'invitation')
        }),
        ('Respondent', {
            'fields': ('respondent_name', 'respondent_email', 'is_anonymous')
        }),
        ('Ratings', {
            'fields': ('overall_rating', 'venue_rating', 'content_rating', 'organization_rating', 'nps_score'),
            'description': 'Ratings are on a 1-5 scale (except NPS which is 0-10)'
        }),
        ('Text Feedback', {
            'fields': ('what_went_well', 'what_needs_improvement', 'additional_comments', 'interested_topics'),
            'classes': ('collapse',)
        }),
        ('Preferences', {
            'fields': ('would_recommend', 'would_attend_future')
        }),
        ('Tags', {
            'fields': ('tags',)
        }),
        ('Metadata', {
            'fields': ('submission_source', 'submitted_at', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Computed Fields', {
            'fields': ('average_rating', 'nps_category'),
            'classes': ('collapse',)
        }),
        ('Gamification', {
            'fields': ('gamification_processed', 'points_awarded'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('event', 'invitation').prefetch_related('tags')


@admin.register(FeedbackAnalytics)
class FeedbackAnalyticsAdmin(admin.ModelAdmin):
    list_display = [
        'event', 'total_responses', 'response_rate', 'avg_overall_rating',
        'net_promoter_score', 'last_updated'
    ]
    search_fields = ['event__name']
    readonly_fields = [
        'total_responses', 'response_rate', 'avg_overall_rating',
        'avg_venue_rating', 'avg_content_rating', 'avg_organization_rating',
        'avg_nps_score', 'nps_detractors', 'nps_passives', 'nps_promoters',
        'net_promoter_score', 'would_recommend_count', 'would_attend_future_count',
        'top_positive_tags', 'top_negative_tags', 'last_updated'
    ]
    
    fieldsets = (
        ('Event', {
            'fields': ('event',)
        }),
        ('Response Statistics', {
            'fields': ('total_responses', 'response_rate')
        }),
        ('Rating Averages', {
            'fields': ('avg_overall_rating', 'avg_venue_rating', 'avg_content_rating', 'avg_organization_rating')
        }),
        ('Net Promoter Score', {
            'fields': ('avg_nps_score', 'nps_detractors', 'nps_passives', 'nps_promoters', 'net_promoter_score')
        }),
        ('Recommendations', {
            'fields': ('would_recommend_count', 'would_attend_future_count')
        }),
        ('Tag Analysis', {
            'fields': ('top_positive_tags', 'top_negative_tags'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('last_updated',)
        })
    )
    
    def has_add_permission(self, request):
        return False  # Analytics are auto-generated
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser