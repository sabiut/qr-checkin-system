from django.contrib import admin
from .models import (
    Message, Announcement, AnnouncementRead, ForumThread, ForumPost,
    QAQuestion, QAAnswer, IcebreakerActivity, IcebreakerResponse,
    IcebreakerResponseLike, IcebreakerResponseReply, NotificationPreference
)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'content_preview', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'event']
    search_fields = ['sender__username', 'recipient__username', 'content']
    readonly_fields = ['created_at', 'delivered_at', 'read_at']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'event', 'author', 'priority', 'is_published', 'created_at']
    list_filter = ['priority', 'announcement_type', 'is_published', 'created_at']
    search_fields = ['title', 'content', 'event__name']
    readonly_fields = ['view_count', 'sent_at']
    
    actions = ['publish_announcements']
    
    def publish_announcements(self, request, queryset):
        queryset.update(is_published=True)
    publish_announcements.short_description = 'Publish selected announcements'

@admin.register(ForumThread)
class ForumThreadAdmin(admin.ModelAdmin):
    list_display = ['title', 'event', 'author', 'category', 'reply_count', 'is_pinned', 'created_at']
    list_filter = ['category', 'is_pinned', 'is_locked', 'created_at']
    search_fields = ['title', 'content', 'author__username']
    readonly_fields = ['view_count', 'reply_count', 'like_count', 'last_activity']

@admin.register(QAQuestion)
class QAQuestionAdmin(admin.ModelAdmin):
    list_display = ['question_preview', 'author_display', 'event', 'status', 'upvotes', 'created_at']
    list_filter = ['status', 'is_anonymous', 'is_featured', 'created_at']
    search_fields = ['question', 'author__username', 'session_name']
    readonly_fields = ['upvotes', 'approved_at', 'answered_at']
    
    def question_preview(self, obj):
        return obj.question[:50] + '...' if len(obj.question) > 50 else obj.question
    question_preview.short_description = 'Question'
    
    def author_display(self, obj):
        return 'Anonymous' if obj.is_anonymous else obj.author.username
    author_display.short_description = 'Author'

@admin.register(IcebreakerActivity)
class IcebreakerActivityAdmin(admin.ModelAdmin):
    list_display = ['title', 'event', 'activity_type', 'is_active', 'is_featured', 'response_count', 'starts_at']
    list_filter = ['activity_type', 'is_active', 'is_featured', 'starts_at']
    search_fields = ['title', 'description', 'event__name']
    readonly_fields = ['response_count', 'view_count']

    actions = ['activate_activities', 'feature_activities']

    def activate_activities(self, request, queryset):
        queryset.update(is_active=True)
    activate_activities.short_description = 'Activate selected activities'

    def feature_activities(self, request, queryset):
        queryset.update(is_featured=True)
    feature_activities.short_description = 'Feature selected activities'

@admin.register(IcebreakerResponse)
class IcebreakerResponseAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity', 'response_preview', 'like_count', 'is_public', 'created_at']
    list_filter = ['is_public', 'created_at', 'activity__activity_type']
    search_fields = ['user__username', 'text_response', 'activity__title']
    readonly_fields = ['like_count', 'reply_count']

    def response_preview(self, obj):
        content = obj.text_response or obj.selected_option
        return content[:50] + '...' if len(content) > 50 else content
    response_preview.short_description = 'Response'

admin.site.register(AnnouncementRead)
admin.site.register(ForumPost)
admin.site.register(QAAnswer)
admin.site.register(IcebreakerResponseLike)
admin.site.register(IcebreakerResponseReply)
admin.site.register(NotificationPreference)
