from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings
from .models import Event
from .serializers import EventSerializer
import logging

logger = logging.getLogger(__name__)

class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return events filtered by owner or all events for staff users"""
        user = self.request.user
        if user.is_staff:
            return Event.objects.all()
        return Event.objects.filter(owner=user)
    
    def perform_create(self, serializer):
        """Set the owner to the current user when creating an event"""
        serializer.save(owner=self.request.user)
    
    def create(self, request, *args, **kwargs):
        # Log the incoming data for debugging
        logger.info(f"Creating event with data: {request.data}")
        
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                logger.info(f"Event created successfully: {serializer.data.get('id')}")
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            else:
                logger.error(f"Validation errors: {serializer.errors}")
                return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(f"Error creating event: {str(e)}")
            return Response({"detail": f"Server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def sync(self, request):
        """
        Synchronize offline events with the server.
        
        Expects a list of events in the request body, each with a temporary ID.
        Returns a mapping of temporary IDs to permanent IDs.
        """
        try:
            events_data = request.data
            id_mapping = {}
            errors = []
            
            logger.info(f"Syncing events: {len(events_data)} events received")
            
            for event_data in events_data:
                try:
                    temp_id = event_data.pop('temp_id', None)
                    
                    if not temp_id:
                        continue
                        
                    # Remove any fields that shouldn't be set directly
                    event_data.pop('id', None)
                    event_data.pop('created_at', None)
                    event_data.pop('updated_at', None)
                    event_data.pop('attendee_count', None)
                    event_data.pop('is_full', None)
                    
                    serializer = self.get_serializer(data=event_data)
                    if serializer.is_valid():
                        event = serializer.save()
                        id_mapping[temp_id] = event.id
                    else:
                        errors.append({
                            'temp_id': temp_id,
                            'errors': serializer.errors
                        })
                except Exception as e:
                    logger.exception(f"Error syncing event with temp_id {temp_id}: {str(e)}")
                    errors.append({
                        'temp_id': temp_id,
                        'errors': str(e)
                    })
            
            return Response({
                'id_mapping': id_mapping,
                'errors': errors
            })
        except Exception as e:
            logger.exception(f"Error in sync endpoint: {str(e)}")
            return Response({
                'detail': f"Server error: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)