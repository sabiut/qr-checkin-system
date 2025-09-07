from django.contrib import admin
from .models import NetworkingProfile, Connection, NetworkingInteraction, EventNetworkingSettings


@admin.register(NetworkingProfile)
class NetworkingProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'company', 'job_title', 'industry', 'visible_in_directory', 'allow_contact_sharing']
    list_filter = ['industry', 'visible_in_directory', 'allow_contact_sharing', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'company', 'job_title']
    readonly_fields = ['networking_qr_token', 'created_at', 'updated_at']
    
    fieldsets = (
        ('User Info', {
            'fields': ('user', 'bio', 'company', 'job_title', 'industry')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'linkedin_url', 'twitter_handle', 'website')
        }),
        ('Networking Preferences', {
            'fields': ('interests', 'looking_for')
        }),
        ('Privacy Settings', {
            'fields': ('allow_contact_sharing', 'visible_in_directory', 'share_email', 'share_phone', 'share_social')
        }),
        ('System', {
            'fields': ('networking_qr_token', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'to_user', 'event', 'connection_method', 'status', 'connected_at', 'points_awarded']
    list_filter = ['connection_method', 'status', 'event', 'connected_at', 'gamification_processed']
    search_fields = ['from_user__username', 'to_user__username', 'event__name']
    readonly_fields = ['id', 'connected_at', 'updated_at']


@admin.register(NetworkingInteraction)
class NetworkingInteractionAdmin(admin.ModelAdmin):
    list_display = ['user', 'target_user', 'event', 'interaction_type', 'timestamp']
    list_filter = ['interaction_type', 'event', 'timestamp']
    search_fields = ['user__username', 'target_user__username', 'event__name']
    readonly_fields = ['timestamp']


@admin.register(EventNetworkingSettings)
class EventNetworkingSettingsAdmin(admin.ModelAdmin):
    list_display = ['event', 'enable_networking', 'enable_attendee_directory', 'enable_qr_exchange', 'networking_points_enabled']
    list_filter = ['enable_networking', 'enable_attendee_directory', 'enable_qr_exchange', 'networking_points_enabled']
    search_fields = ['event__name']
    readonly_fields = ['created_at', 'updated_at']
