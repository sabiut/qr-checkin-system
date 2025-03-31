from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Event


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class EventSerializer(serializers.ModelSerializer):
    # Use serializer method fields instead of model properties to handle potential errors
    attendee_count = serializers.SerializerMethodField()
    is_full = serializers.SerializerMethodField()
    owner = UserSerializer(read_only=True)
    owner_id = serializers.PrimaryKeyRelatedField(
        source='owner', 
        queryset=User.objects.all(),
        required=False,
        write_only=True
    )
    
    class Meta:
        model = Event
        fields = [
            'id', 'owner', 'owner_id', 'name', 'description', 'date', 'time', 
            'location', 'max_attendees', 'attendee_count',
            'is_full', 'created_at', 'updated_at'
        ]
        read_only_fields = ['owner']
        
    def get_attendee_count(self, obj):
        try:
            # Safely get the attendance count
            return obj.invitations.filter(
                attendance__isnull=False,
                attendance__has_attended=True
            ).count()
        except Exception:
            # Return 0 if there's any error
            return 0
            
    def get_is_full(self, obj):
        try:
            if obj.max_attendees:
                return self.get_attendee_count(obj) >= obj.max_attendees
            return False
        except Exception:
            return False