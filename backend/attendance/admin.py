from django.contrib import admin
from django.utils.html import format_html
from .models import Attendance

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('guest_name', 'event_name', 'check_in_status', 'check_in_time', 'notes_preview')
    list_filter = ('has_attended', 'check_in_time', 'invitation__event')
    search_fields = ('invitation__guest_name', 'invitation__event__name', 'check_in_notes')
    readonly_fields = ('invitation',)
    date_hierarchy = 'check_in_time'
    
    def guest_name(self, obj):
        return obj.invitation.guest_name
    guest_name.short_description = 'Guest'
    guest_name.admin_order_field = 'invitation__guest_name'
    
    def event_name(self, obj):
        return obj.invitation.event.name
    event_name.short_description = 'Event'
    event_name.admin_order_field = 'invitation__event__name'
    
    def check_in_status(self, obj):
        return obj.has_attended
    check_in_status.short_description = 'Checked In'
    check_in_status.boolean = True
    
    def notes_preview(self, obj):
        if not obj.check_in_notes:
            return '-'
        if len(obj.check_in_notes) > 50:
            return f"{obj.check_in_notes[:50]}..."
        return obj.check_in_notes
    notes_preview.short_description = 'Notes'
    
    # Actions
    actions = ['mark_as_attended', 'mark_as_not_attended']
    
    def mark_as_attended(self, request, queryset):
        updated = queryset.update(has_attended=True)
        self.message_user(request, f"{updated} attendees were marked as checked in.")
    mark_as_attended.short_description = "Mark selected attendees as checked in"
    
    def mark_as_not_attended(self, request, queryset):
        updated = queryset.update(has_attended=False)
        self.message_user(request, f"{updated} attendees were marked as not checked in.")
    mark_as_not_attended.short_description = "Mark selected attendees as not checked in"