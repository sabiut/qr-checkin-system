from rest_framework import serializers
from .models import Attendance
from invitations.serializers import InvitationSerializer


class AttendanceSerializer(serializers.ModelSerializer):
    invitation_details = InvitationSerializer(source='invitation', read_only=True)
    
    class Meta:
        model = Attendance
        fields = [
            'id', 'invitation', 'invitation_details',
            'has_attended', 'check_in_time', 'check_in_notes'
        ]
        read_only_fields = ['id']