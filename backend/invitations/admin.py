from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Invitation
from attendance.models import Attendance

# Custom filter for check-in status
class CheckedInListFilter(admin.SimpleListFilter):
    title = _('Check-in Status')
    parameter_name = 'checked_in'
    
    def lookups(self, request, model_admin):
        return (
            ('yes', _('Checked In')),
            ('no', _('Not Checked In')),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'yes':
            # Find invitations that have an attendance record with has_attended=True
            return queryset.filter(attendance__has_attended=True)
        if self.value() == 'no':
            # Find invitations that either have no attendance record or has_attended=False
            return queryset.filter(attendance__has_attended=False) | queryset.filter(attendance__isnull=True)

@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ('guest_name', 'event_name', 'email_display', 'phone_display', 'check_in_status', 'qr_code_display')
    list_filter = ('event', CheckedInListFilter)
    search_fields = ('guest_name', 'guest_email', 'guest_phone')
    readonly_fields = ('id', 'qr_code_preview', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('id', 'event', 'guest_name', 'guest_email', 'guest_phone'),
        }),
        ('QR Code', {
            'fields': ('qr_code_preview',),
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def email_display(self, obj):
        return obj.guest_email or '-'
    email_display.short_description = 'Email'
    
    def phone_display(self, obj):
        return obj.guest_phone or '-'
    phone_display.short_description = 'Phone'
    
    def event_name(self, obj):
        return obj.event.name
    event_name.short_description = 'Event'
    event_name.admin_order_field = 'event__name'
    
    def check_in_status(self, obj):
        try:
            return obj.attendance.has_attended
        except:
            return None
    check_in_status.short_description = 'Checked In'
    check_in_status.boolean = True
    
    def qr_code_preview(self, obj):
        if obj.qr_code:
            return format_html('<img src="{}" style="max-width: 200px; max-height: 200px;" />', obj.qr_code.url)
        return "No QR code generated"
    qr_code_preview.short_description = 'QR Code Preview'
    
    def qr_code_display(self, obj):
        if obj.qr_code:
            return format_html('<a href="{}" target="_blank">View</a>', obj.qr_code.url)
        return "-"
    qr_code_display.short_description = 'QR Code'
    
    # Actions
    actions = ['send_invitation_emails']
    
    def send_invitation_emails(self, request, queryset):
        from django.core.mail import send_mail
        from django.conf import settings
        
        success_count = 0
        failed_count = 0
        
        for invitation in queryset:
            if invitation.guest_email:
                try:
                    # Simple event information email
                    subject = f"Invitation to {invitation.event.name}"
                    message = f"""
                    Hello {invitation.guest_name},
                    
                    You've been invited to {invitation.event.name}!
                    
                    Event Details:
                    - Date: {invitation.event.date}
                    - Time: {invitation.event.time}
                    - Location: {invitation.event.location}
                    
                    Your QR code for check-in is attached or available at: {request.build_absolute_uri(invitation.qr_code.url)}
                    
                    Please bring this QR code with you to the event for a quick check-in.
                    
                    Thank you!
                    """
                    
                    send_mail(
                        subject=subject,
                        message=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[invitation.guest_email],
                        fail_silently=False,
                    )
                    success_count += 1
                except Exception as e:
                    failed_count += 1
        
        if failed_count:
            self.message_user(request, f"Sent {success_count} emails. Failed to send {failed_count} emails.", level='WARNING')
        else:
            self.message_user(request, f"Successfully sent {success_count} invitation emails.")
            
    send_invitation_emails.short_description = "Send invitation emails to selected guests"