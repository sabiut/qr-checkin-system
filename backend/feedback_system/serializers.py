from rest_framework import serializers
from .models import FeedbackTag, EventFeedback, FeedbackAnalytics
from events.models import Event
from invitations.models import Invitation


class FeedbackTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackTag
        fields = ['id', 'name', 'category', 'icon', 'description', 'is_positive']


class EventFeedbackSerializer(serializers.ModelSerializer):
    tags = FeedbackTagSerializer(many=True, read_only=True)
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    average_rating = serializers.ReadOnlyField()
    nps_category = serializers.ReadOnlyField()
    
    class Meta:
        model = EventFeedback
        fields = [
            'id', 'event', 'invitation', 'respondent_name', 'respondent_email',
            'is_anonymous', 'overall_rating', 'venue_rating', 'content_rating',
            'organization_rating', 'nps_score', 'what_went_well',
            'what_needs_improvement', 'additional_comments', 'would_recommend',
            'would_attend_future', 'interested_topics', 'tags', 'tag_ids',
            'submission_source', 'submitted_at', 'average_rating', 'nps_category',
            'points_awarded'
        ]
        read_only_fields = ['id', 'submitted_at', 'gamification_processed', 'points_awarded']
    
    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        feedback = super().create(validated_data)
        
        if tag_ids:
            tags = FeedbackTag.objects.filter(id__in=tag_ids)
            feedback.tags.set(tags)
        
        return feedback
    
    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        feedback = super().update(instance, validated_data)
        
        if tag_ids is not None:
            tags = FeedbackTag.objects.filter(id__in=tag_ids)
            feedback.tags.set(tags)
        
        return feedback


class EventFeedbackCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for feedback creation via public forms."""
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = EventFeedback
        fields = [
            'event', 'invitation', 'respondent_name', 'respondent_email',
            'is_anonymous', 'overall_rating', 'venue_rating', 'content_rating',
            'organization_rating', 'nps_score', 'what_went_well',
            'what_needs_improvement', 'additional_comments', 'would_recommend',
            'would_attend_future', 'interested_topics', 'tag_ids', 'submission_source'
        ]
    
    def validate_event(self, value):
        """Ensure event exists and is past its date."""
        if not Event.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Event not found.")
        return value
    
    def validate_invitation(self, value):
        """Ensure invitation belongs to the event if provided."""
        if value and hasattr(self, 'initial_data'):
            event_id = self.initial_data.get('event')
            if event_id and value.event.id != int(event_id):
                raise serializers.ValidationError("Invitation does not belong to this event.")
        return value
    
    def validate_respondent_email(self, value):
        """Ensure one feedback per email per event."""
        event_id = self.initial_data.get('event')
        if event_id:
            existing = EventFeedback.objects.filter(
                event_id=event_id,
                respondent_email=value
            ).exists()
            if existing:
                raise serializers.ValidationError("Feedback already submitted for this email and event.")
        return value
    
    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        
        # Auto-populate respondent_name from invitation if not provided
        if not validated_data.get('respondent_name') and validated_data.get('invitation'):
            validated_data['respondent_name'] = validated_data['invitation'].guest_name
        
        feedback = super().create(validated_data)
        
        if tag_ids:
            tags = FeedbackTag.objects.filter(id__in=tag_ids)
            feedback.tags.set(tags)
        
        return feedback


class FeedbackAnalyticsSerializer(serializers.ModelSerializer):
    calculated_nps = serializers.SerializerMethodField()
    
    class Meta:
        model = FeedbackAnalytics
        fields = [
            'event', 'total_responses', 'response_rate', 'avg_overall_rating',
            'avg_venue_rating', 'avg_content_rating', 'avg_organization_rating',
            'avg_nps_score', 'nps_detractors', 'nps_passives', 'nps_promoters',
            'net_promoter_score', 'calculated_nps', 'would_recommend_count',
            'would_attend_future_count', 'top_positive_tags', 'top_negative_tags',
            'last_updated'
        ]
    
    def get_calculated_nps(self, obj):
        return obj.calculate_nps()


class FeedbackSummarySerializer(serializers.Serializer):
    """Serializer for feedback summary data."""
    event_name = serializers.CharField()
    total_feedback = serializers.IntegerField()
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    response_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    nps_score = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    
    # Rating breakdowns
    rating_distribution = serializers.DictField()
    nps_distribution = serializers.DictField()
    
    # Common feedback themes
    top_positive_feedback = serializers.ListField()
    top_improvement_suggestions = serializers.ListField()
    
    # Tags
    most_used_tags = serializers.ListField()


class QuickFeedbackSerializer(serializers.Serializer):
    """Serializer for quick feedback collection (e.g., from QR codes)."""
    event_id = serializers.IntegerField()
    invitation_id = serializers.UUIDField(required=False)
    email = serializers.EmailField()
    rating = serializers.IntegerField(min_value=1, max_value=5)
    quick_comment = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def create(self, validated_data):
        return EventFeedback.objects.create(
            event_id=validated_data['event_id'],
            invitation_id=validated_data.get('invitation_id'),
            respondent_email=validated_data['email'],
            overall_rating=validated_data['rating'],
            additional_comments=validated_data.get('quick_comment', ''),
            submission_source='qr_code'
        )