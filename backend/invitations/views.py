from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import Invitation
from .serializers import InvitationSerializer
from events.models import Event
import logging

logger = logging.getLogger(__name__)

class InvitationViewSet(viewsets.ModelViewSet):
    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer
    permission_classes = [AllowAny]  # Allow public access for this demo
    
    def perform_create(self, serializer):
        """Override create to send email with QR code."""
        invitation = serializer.save()
        
        # Wait for QR code to be generated
        # At this point, save() in the model should have generated the QR code
        if invitation.guest_email:
            try:
                self.send_invitation_email(invitation)
            except Exception as e:
                logger.error(f"Failed to send invitation email: {str(e)}")
                
        return invitation
    
    def get_queryset(self):
        queryset = Invitation.objects.all()
        event_id = self.request.query_params.get('event_id')
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        return queryset
    
    @action(detail=True, methods=['get'])
    def qr_code(self, request, pk=None):
        invitation = self.get_object()
        if invitation.qr_code:
            qr_url = request.build_absolute_uri(invitation.qr_code.url)
            return Response({'qr_code_url': qr_url})
        return Response({'error': 'QR code not found'}, status=404)
    
    @action(detail=True, methods=['post'])
    def send_email(self, request, pk=None):
        """Manually send email with QR code for an invitation."""
        invitation = self.get_object()
        if not invitation.guest_email:
            return Response(
                {'error': 'Invitation has no email address'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            self.send_invitation_email(invitation)
            return Response({'message': 'Invitation email sent successfully'})
        except Exception as e:
            logger.error(f"Failed to send invitation email: {str(e)}")
            return Response(
                {'error': f'Failed to send email: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def send_invitation_email(self, invitation):
        """Send invitation email with QR code."""
        if not invitation.guest_email:
            return
            
        # Get the event details
        event = invitation.event
        
        # Build URL for QR code - we can't use build_absolute_uri here because we may not have request
        # Just use the relative URL which works with absolute URLs in the frontend
        base_url = "http://localhost:8000"  # Default for development
        qr_url = f"{base_url}{invitation.qr_code.url}"
        
        # Email content
        subject = f"Invitation to {event.name}"
        
        # Simple plain text message
        message = f"""
        Hello {invitation.guest_name},
        
        You've been invited to {event.name}!
        
        Event Details:
        - Date: {event.date}
        - Time: {event.time}
        - Location: {event.location}
        
        Your QR code for check-in is available at: {qr_url}
        
        Please bring this QR code with you to the event for a quick check-in.
        
        Thank you!
        """
        
        # HTML message with embedded QR code
        html_message = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4f46e5; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .footer {{ text-align: center; margin-top: 30px; font-size: 0.8em; color: #666; }}
                .qr-code {{ text-align: center; margin: 30px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>You're Invited!</h1>
                </div>
                <div class="content">
                    <p>Hello {invitation.guest_name},</p>
                    
                    <p>You've been invited to <strong>{event.name}</strong>!</p>
                    
                    <h2>Event Details:</h2>
                    <ul>
                        <li><strong>Date:</strong> {event.date}</li>
                        <li><strong>Time:</strong> {event.time}</li>
                        <li><strong>Location:</strong> {event.location}</li>
                    </ul>
                    
                    <div class="qr-code">
                        <h3>Your QR Code for Check-in:</h3>
                        <img src="{qr_url}" alt="Check-in QR Code" style="max-width: 200px;">
                    </div>
                    
                    <p>Please bring this QR code with you to the event for a quick check-in.</p>
                    
                    <p>Thank you!</p>
                </div>
                <div class="footer">
                    <p>This is an automated message from the QR Check-in System.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send the email
        send_mail(
            subject=subject,
            message=message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invitation.guest_email],
            fail_silently=False,
        )
        
    @action(detail=False, methods=['post'])
    def sync(self, request):
        """
        Synchronize offline invitations with the server
        
        Expects a list of invitations with temp_ids and the actual event_id
        """
        invitations_data = request.data
        id_mapping = {}
        
        for invitation_data in invitations_data:
            temp_id = invitation_data.pop('temp_id', None)
            event_id = invitation_data.get('event')
            
            if not temp_id or not event_id:
                continue
                
            try:
                # Verify the event exists
                Event.objects.get(id=event_id)
                
                # Remove any fields that shouldn't be set directly
                invitation_data.pop('id', None)
                invitation_data.pop('qr_code', None)
                invitation_data.pop('created_at', None)
                invitation_data.pop('updated_at', None)
                
                serializer = self.get_serializer(data=invitation_data)
                if serializer.is_valid():
                    invitation = serializer.save()
                    id_mapping[temp_id] = str(invitation.id)
            except Event.DoesNotExist:
                continue
                
        return Response({'id_mapping': id_mapping})