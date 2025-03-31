from django.contrib import admin
from django.utils import timezone
from .models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'date', 'time', 'location', 'max_attendees', 'attendee_count', 'is_full', 'is_upcoming')
    list_filter = ('date', 'owner')
    search_fields = ('name', 'description', 'location', 'owner__username')
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at', 'attendee_count', 'is_full')
    
    def attendee_count(self, obj):
        return obj.attendee_count
    
    def is_full(self, obj):
        return obj.is_full
    
    def is_upcoming(self, obj):
        return obj.date >= timezone.now().date()
    
    attendee_count.short_description = 'Attendees'
    is_full.boolean = True
    is_full.short_description = 'Full'
    is_upcoming.boolean = True
    is_upcoming.short_description = 'Upcoming'