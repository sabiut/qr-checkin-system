from rest_framework import serializers
from .models import Invitation
from events.serializers import EventSerializer


class InvitationSerializer(serializers.ModelSerializer):
    event_details = EventSerializer(source='event', read_only=True)
    qr_code_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Invitation
        fields = [
            'id', 'event', 'event_details', 'guest_name', 
            'guest_email', 'guest_phone', 'qr_code', 
            'qr_code_url', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'qr_code', 'qr_code_url']
    
    def get_qr_code_url(self, obj):
        if obj.qr_code:
            return obj.qr_code.url
        return None