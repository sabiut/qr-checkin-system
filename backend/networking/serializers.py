from rest_framework import serializers
from django.contrib.auth.models import User
from .models import NetworkingProfile, Connection, NetworkingInteraction, EventNetworkingSettings
from events.models import Event


class NetworkingProfileSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()
    
    class Meta:
        model = NetworkingProfile
        fields = [
            'user', 'user_name', 'user_email', 'bio', 'company', 'job_title', 'industry',
            'phone_number', 'linkedin_url', 'twitter_handle', 'website', 
            'interests', 'looking_for', 'allow_contact_sharing', 'visible_in_directory',
            'share_email', 'share_phone', 'share_social', 'networking_qr_token',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'networking_qr_token', 'created_at', 'updated_at']
    
    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    
    def get_user_email(self, obj):
        # Only return email if privacy settings allow
        if obj.share_email:
            return obj.user.email
        return None


class NetworkingProfileCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating networking profiles"""
    
    class Meta:
        model = NetworkingProfile
        fields = [
            'bio', 'company', 'job_title', 'industry', 'phone_number', 
            'linkedin_url', 'twitter_handle', 'website', 'interests', 'looking_for',
            'allow_contact_sharing', 'visible_in_directory', 'share_email', 
            'share_phone', 'share_social'
        ]
    
    def create(self, validated_data):
        # Get the user from the request context
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)


class AttendeeDirectorySerializer(serializers.ModelSerializer):
    """Simplified serializer for attendee directory listing"""
    user_name = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField() 
    shareable_info = serializers.SerializerMethodField()
    
    class Meta:
        model = NetworkingProfile
        fields = [
            'user', 'user_name', 'user_email', 'company', 'job_title', 'industry',
            'bio', 'interests', 'looking_for', 'shareable_info'
        ]
    
    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    
    def get_user_email(self, obj):
        if obj.share_email:
            return obj.user.email
        return None
    
    def get_shareable_info(self, obj):
        return obj.get_shareable_info()


class ConnectionSerializer(serializers.ModelSerializer):
    from_user_name = serializers.SerializerMethodField()
    to_user_name = serializers.SerializerMethodField()
    event_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Connection
        fields = [
            'id', 'from_user', 'to_user', 'from_user_name', 'to_user_name',
            'event', 'event_name', 'connection_method', 'status', 'meeting_location',
            'notes_from_user', 'notes_to_user', 'points_awarded', 'connected_at'
        ]
        read_only_fields = ['id', 'points_awarded', 'connected_at']
    
    def get_from_user_name(self, obj):
        return obj.from_user.get_full_name() or obj.from_user.username
    
    def get_to_user_name(self, obj):
        return obj.to_user.get_full_name() or obj.to_user.username
    
    def get_event_name(self, obj):
        return obj.event.name


class ConnectionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating connections"""
    
    class Meta:
        model = Connection
        fields = [
            'to_user', 'event', 'connection_method', 'meeting_location', 'notes_from_user'
        ]
    
    def create(self, validated_data):
        validated_data['from_user'] = self.context['request'].user
        connection = super().create(validated_data)
        
        # Create reverse connection if it doesn't exist
        connection.create_reverse_connection()
        
        return connection
    
    def validate(self, data):
        from_user = self.context['request'].user
        to_user = data['to_user']
        event = data['event']
        
        # Check if connection already exists
        if Connection.objects.filter(from_user=from_user, to_user=to_user, event=event).exists():
            raise serializers.ValidationError("Connection already exists between these users for this event.")
        
        # Check if users can't connect to themselves
        if from_user == to_user:
            raise serializers.ValidationError("Users cannot connect to themselves.")
        
        return data


class NetworkingInteractionSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    target_user_name = serializers.SerializerMethodField()
    event_name = serializers.SerializerMethodField()
    
    class Meta:
        model = NetworkingInteraction
        fields = [
            'user', 'user_name', 'target_user', 'target_user_name', 
            'event', 'event_name', 'interaction_type', 'interaction_data', 'timestamp'
        ]
        read_only_fields = ['user', 'timestamp']
    
    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    
    def get_target_user_name(self, obj):
        if obj.target_user:
            return obj.target_user.get_full_name() or obj.target_user.username
        return None
    
    def get_event_name(self, obj):
        return obj.event.name
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class QRContactSerializer(serializers.Serializer):
    """Serializer for QR code contact exchange"""
    networking_token = serializers.UUIDField()
    event_id = serializers.IntegerField()
    meeting_location = serializers.CharField(max_length=200, required=False)
    notes = serializers.CharField(max_length=1000, required=False)
    
    def validate_networking_token(self, value):
        try:
            self.networking_profile = NetworkingProfile.objects.get(networking_qr_token=value)
            return value
        except NetworkingProfile.DoesNotExist:
            raise serializers.ValidationError("Invalid networking QR token.")
    
    def validate_event_id(self, value):
        try:
            self.event = Event.objects.get(id=value)
            return value
        except Event.DoesNotExist:
            raise serializers.ValidationError("Event not found.")
    
    def create_connection(self, user):
        # Create the connection from scanner to scanned user
        connection = Connection.objects.create(
            from_user=user,
            to_user=self.networking_profile.user,
            event=self.event,
            connection_method='qr_scan',
            meeting_location=self.validated_data.get('meeting_location', ''),
            notes_from_user=self.validated_data.get('notes', '')
        )
        
        # Create reverse connection
        connection.create_reverse_connection()
        
        return connection


class EventNetworkingSettingsSerializer(serializers.ModelSerializer):
    event_name = serializers.SerializerMethodField()
    
    class Meta:
        model = EventNetworkingSettings
        fields = [
            'event', 'event_name', 'enable_networking', 'enable_attendee_directory',
            'enable_qr_exchange', 'enable_contact_export', 'allow_industry_filter',
            'allow_interest_filter', 'allow_company_filter', 'require_mutual_consent',
            'allow_anonymous_browsing', 'networking_points_enabled', 'points_per_connection',
            'max_daily_networking_points', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_event_name(self, obj):
        return obj.event.name


class NetworkingStatsSerializer(serializers.Serializer):
    """Serializer for networking statistics"""
    total_connections = serializers.IntegerField()
    new_connections_today = serializers.IntegerField()
    most_active_events = serializers.ListField()
    connection_methods = serializers.DictField()
    points_earned = serializers.IntegerField()
    top_connectors = serializers.ListField()
