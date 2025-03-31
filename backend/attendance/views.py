from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
import logging
import uuid
from .models import Attendance
from .serializers import AttendanceSerializer
from invitations.models import Invitation
from invitations.serializers import InvitationSerializer

logger = logging.getLogger(__name__)

class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [AllowAny]  # Allow public access for this demo
    
    def get_queryset(self):
        queryset = Attendance.objects.all()
        event_id = self.request.query_params.get('event_id')
        if event_id:
            queryset = queryset.filter(invitation__event_id=event_id)
        return queryset
    
    @action(detail=False, methods=['post'])
    def check_in(self, request):
        invitation_id = request.data.get('invitation_id')
        
        # Log the incoming request data
        logger.info(f"Check-in request received with invitation_id: {invitation_id}")
        
        if not invitation_id:
            logger.error("Check-in failed: No invitation_id provided")
            return Response({'error': 'Invitation ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Handle string UUID properly
        try:
            # Convert string to UUID if needed
            if isinstance(invitation_id, str) and not invitation_id.startswith('temp_'):
                try:
                    # Validate UUID format
                    invitation_uuid = uuid.UUID(invitation_id)
                    invitation_id = str(invitation_uuid)  # Ensure correct string format
                except ValueError:
                    logger.error(f"Invalid UUID format: {invitation_id}")
                    return Response({'error': 'Invalid invitation ID format'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Try to get the invitation
            try:
                invitation = Invitation.objects.get(id=invitation_id)
                logger.info(f"Found invitation: {invitation.id} for guest {invitation.guest_name}")
            except Invitation.DoesNotExist:
                logger.error(f"Invitation not found with ID: {invitation_id}")
                return Response({'error': 'Invitation not found'}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                logger.error(f"Error retrieving invitation: {str(e)}")
                return Response({'error': f'Error retrieving invitation: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Create or update attendance record
            try:
                attendance, created = Attendance.objects.get_or_create(invitation=invitation)
                
                if attendance.has_attended:
                    logger.info(f"Guest already checked in: {invitation.guest_name}")
                    return Response({
                        'message': 'Already checked in',
                        'attendance': AttendanceSerializer(attendance).data
                    })
                
                # Update attendance record
                attendance.has_attended = True
                attendance.check_in_time = timezone.now()
                attendance.check_in_notes = request.data.get('notes', '')
                attendance.save()
                
                logger.info(f"Successfully checked in guest: {invitation.guest_name}")
                
                # Serialize with nested invitation details
                serializer = AttendanceSerializer(attendance)
                
                return Response({
                    'message': 'Check-in successful',
                    'attendance': serializer.data
                })
            except Exception as e:
                logger.error(f"Error processing attendance: {str(e)}")
                return Response({'error': f'Error processing attendance: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Unexpected error in check_in: {str(e)}")
            return Response({'error': f'An unexpected error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=['post'])
    def sync_offline(self, request):
        """
        Synchronize offline check-ins with the server
        
        Expects a list of invitation IDs that were checked in offline
        """
        invitation_ids = request.data.get('invitation_ids', [])
        results = {
            'successful': [],
            'failed': []
        }
        
        for invitation_id in invitation_ids:
            try:
                invitation = Invitation.objects.get(id=invitation_id)
                attendance, created = Attendance.objects.get_or_create(invitation=invitation)
                
                if not attendance.has_attended:
                    attendance.has_attended = True
                    attendance.check_in_time = timezone.now()
                    attendance.check_in_notes = 'Synchronized from offline check-in'
                    attendance.save()
                    
                results['successful'].append(invitation_id)
            except Exception as e:
                results['failed'].append({
                    'id': invitation_id,
                    'error': str(e)
                })
                
        return Response(results)