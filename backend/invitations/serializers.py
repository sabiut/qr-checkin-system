from rest_framework import serializers
from .models import Invitation, TicketFormat
from events.serializers import EventSerializer


class InvitationSerializer(serializers.ModelSerializer):
    event_details = EventSerializer(source='event', read_only=True)
    qr_code_url = serializers.SerializerMethodField()
    ticket_html_url = serializers.SerializerMethodField()
    ticket_pdf_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Invitation
        fields = [
            'id', 'event', 'event_details', 'guest_name', 
            'guest_email', 'guest_phone', 'qr_code', 
            'qr_code_url', 'ticket_html_url', 'ticket_pdf_url', 
            'ticket_format', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'qr_code', 'qr_code_url', 
                            'ticket_html_url', 'ticket_pdf_url']
    
    def get_qr_code_url(self, obj):
        if obj.qr_code:
            return obj.qr_code.url
        return None
        
    def get_ticket_html_url(self, obj):
        try:
            if obj.ticket_html:
                return obj.ticket_html.url
        except Exception as e:
            # Log the error but return None
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error getting HTML ticket URL: {str(e)}")
        return None
        
    def get_ticket_pdf_url(self, obj):
        try:
            if obj.ticket_pdf:
                return obj.ticket_pdf.url
        except Exception as e:
            # Log the error but return None
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error getting PDF ticket URL: {str(e)}")
        return None