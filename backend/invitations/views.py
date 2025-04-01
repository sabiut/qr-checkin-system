from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Invitation
from .serializers import InvitationSerializer
from events.models import Event
import logging
import os

logger = logging.getLogger(__name__)

class InvitationViewSet(viewsets.ModelViewSet):
    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer
    permission_classes = [AllowAny]  # Allow public access for this demo
    
    def perform_create(self, serializer):
        """Override create to send email with ticket."""
        invitation = serializer.save()
        
        # Wait for tickets to be generated
        # At this point, save() in the model should have generated the tickets
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
    
    @action(detail=True, methods=['get'])
    def ticket_html(self, request, pk=None):
        """Get HTML ticket for an invitation."""
        invitation = self.get_object()
        if invitation.ticket_html:
            html_url = request.build_absolute_uri(invitation.ticket_html.url)
            return Response({'ticket_html_url': html_url})
        return Response({'error': 'HTML ticket not found'}, status=404)

    @action(detail=True, methods=['get'])
    def ticket_pdf(self, request, pk=None):
        """Get PDF ticket for an invitation."""
        invitation = self.get_object()
        if invitation.ticket_pdf:
            pdf_url = request.build_absolute_uri(invitation.ticket_pdf.url)
            return Response({'ticket_pdf_url': pdf_url})
        return Response({'error': 'PDF ticket not found'}, status=404)

    @action(detail=True, methods=['get'])
    def view_ticket(self, request, pk=None):
        """View HTML ticket directly."""
        invitation = self.get_object()
        if invitation.ticket_html:
            with invitation.ticket_html.open('r') as f:
                html_content = f.read().decode('utf-8')
                
            # If this is a direct view (not API), we may need to fix QR code URL
            # Ensure QR code URLs are absolute in the HTML
            if invitation.qr_code and invitation.qr_code.url:
                from django.conf import settings
                base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
                qr_code_url = invitation.qr_code.url
                if qr_code_url.startswith('/'):
                    absolute_qr_url = f"{base_url}{qr_code_url}"
                    # Replace relative URL with absolute URL in the HTML
                    html_content = html_content.replace(f'src="{qr_code_url}"', f'src="{absolute_qr_url}"')
                    
            return HttpResponse(html_content)
        return Response({'error': 'Ticket not found'}, status=404)
    
    @action(detail=True, methods=['post'])
    def send_email(self, request, pk=None):
        """Manually send email with ticket for an invitation."""
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
        """Send invitation email with digital ticket."""
        if not invitation.guest_email:
            logger.info(f"No guest email for invitation {invitation.id}, skipping email")
            return
            
        # Get the event details
        event = invitation.event
        logger.info(f"Preparing email for invitation {invitation.id} to {invitation.guest_email}")
        
        # Build base URL for links - using a default for development
        base_url = settings.BASE_URL if hasattr(settings, 'BASE_URL') else "http://localhost:8000"
        logger.info(f"Using base URL: {base_url}")
        
        # Get ticket URLs
        ticket_view_url = f"{base_url}/tickets/{invitation.id}/"
        logger.info(f"Ticket view URL: {ticket_view_url}")
        
        # Email subject
        subject = f"Your Ticket for {event.name}"
        
        # Plain text message
        message = f"""
        Hello {invitation.guest_name},
        
        Your ticket for {event.name} is attached.
        
        Event Details:
        - Date: {event.date}
        - Time: {event.time}
        - Location: {event.location}
        
        Please bring your ticket with the QR code to the event for quick check-in.
        You can also view your ticket online at: {ticket_view_url}
        
        Thank you!
        """
        
        # HTML message with embedded ticket details
        html_message = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4f46e5; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .footer {{ text-align: center; margin-top: 30px; font-size: 0.8em; color: #666; }}
                .button {{ display: inline-block; background-color: #4f46e5; color: white; padding: 10px 20px; 
                          text-decoration: none; border-radius: 4px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Your Ticket is Ready!</h1>
                </div>
                <div class="content">
                    <p>Hello {invitation.guest_name},</p>
                    
                    <p>Your ticket for <strong>{event.name}</strong> is ready!</p>
                    
                    <h2>Event Details:</h2>
                    <ul>
                        <li><strong>Date:</strong> {event.date}</li>
                        <li><strong>Time:</strong> {event.time}</li>
                        <li><strong>Location:</strong> {event.location}</li>
                    </ul>
                    
                    <p>Your ticket is attached to this email as a PDF.</p>
                    
                    <p>You can also view your ticket online:</p>
                    
                    <a href="{ticket_view_url}" class="button">View Ticket</a>
                    
                    <p>Please bring your ticket with the QR code to the event for quick check-in.</p>
                    
                    <p>Thank you!</p>
                </div>
                <div class="footer">
                    <p>This is an automated message from the QR Check-in System.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Log email settings
        logger.info(f"Email settings - Backend: {settings.EMAIL_BACKEND}")
        logger.info(f"Email settings - Host: {settings.EMAIL_HOST}")
        logger.info(f"Email settings - Port: {settings.EMAIL_PORT}")
        logger.info(f"Email settings - TLS: {settings.EMAIL_USE_TLS}")
        logger.info(f"Email settings - User: {settings.EMAIL_HOST_USER}")
        logger.info(f"Email settings - From: {settings.DEFAULT_FROM_EMAIL}")
        
        try:
            # Prepare email
            logger.info(f"Creating email message to {invitation.guest_email}")
            email = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[invitation.guest_email],
            )
            
            # Attach HTML content
            logger.info("Attaching HTML content")
            email.attach_alternative(html_message, "text/html")
            
            # Attach PDF ticket if available
            if invitation.ticket_pdf:
                if os.path.exists(invitation.ticket_pdf.path):
                    logger.info(f"Attaching PDF ticket: {invitation.ticket_pdf.path}")
                    email.attach_file(invitation.ticket_pdf.path)
                else:
                    logger.warning(f"PDF file doesn't exist at path: {invitation.ticket_pdf.path}")
            else:
                logger.warning("No PDF ticket available to attach")
                
            # Attach HTML ticket as a file too
            if invitation.ticket_html and os.path.exists(invitation.ticket_html.path):
                logger.info(f"Attaching HTML ticket: {invitation.ticket_html.path}")
                email.attach_file(invitation.ticket_html.path)
                
            # Send email
            logger.info("Sending email...")
            result = email.send()
            logger.info(f"Email send result: {result}")
            return True
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise
        
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
                invitation_data.pop('ticket_html', None)
                invitation_data.pop('ticket_pdf', None)
                invitation_data.pop('created_at', None)
                invitation_data.pop('updated_at', None)
                
                serializer = self.get_serializer(data=invitation_data)
                if serializer.is_valid():
                    invitation = serializer.save()
                    id_mapping[temp_id] = str(invitation.id)
            except Event.DoesNotExist:
                continue
                
        return Response({'id_mapping': id_mapping})


@api_view(['GET'])
@csrf_exempt
def debug_ticket_generation(request, invitation_id):
    """Debug endpoint to test ticket generation for an invitation"""
    logger.info(f"Debug ticket generation called for invitation {invitation_id}")
    
    try:
        invitation = Invitation.objects.get(id=invitation_id)
        
        # Force generate tickets
        logger.info("Forcing ticket generation...")
        invitation.generate_tickets()
        invitation.save()
        
        # Check if tickets were created
        html_exists = bool(invitation.ticket_html)
        pdf_exists = bool(invitation.ticket_pdf)
        
        # Get ticket paths if they exist
        html_path = invitation.ticket_html.path if html_exists else None
        pdf_path = invitation.ticket_pdf.path if pdf_exists else None
        
        # Check if files actually exist on disk
        html_file_exists = html_exists and os.path.exists(html_path)
        pdf_file_exists = pdf_exists and os.path.exists(pdf_path)
        
        result = {
            'success': True,
            'invitation_id': str(invitation.id),
            'html_ticket': {
                'record_exists': html_exists,
                'file_exists': html_file_exists,
                'path': html_path,
                'url': invitation.ticket_html.url if html_exists else None
            },
            'pdf_ticket': {
                'record_exists': pdf_exists,
                'file_exists': pdf_file_exists,
                'path': pdf_path,
                'url': invitation.ticket_pdf.url if pdf_exists else None
            }
        }
        
        return JsonResponse(result)
    except Invitation.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'error': f'Invitation with ID {invitation_id} not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error in debug endpoint: {str(e)}")
        return JsonResponse({
            'success': False, 
            'error': str(e)
        }, status=500)
        
        
@api_view(['POST'])
@csrf_exempt
def test_email_delivery(request, invitation_id):
    """Test endpoint to send an invitation email with ticket attachments"""
    logger.info(f"Test email delivery called for invitation {invitation_id}")
    
    # Get the test email from request or use a default
    email = request.data.get('email', None)
    if not email:
        return JsonResponse({
            'success': False,
            'error': 'Email address is required'
        }, status=400)
    
    try:
        # Get the invitation
        invitation = Invitation.objects.get(id=invitation_id)
        
        # Store original email
        original_email = invitation.guest_email
        
        # Temporarily set the invitation email to the test email
        invitation.guest_email = email
        
        # Force generate tickets if they don't exist
        if not invitation.ticket_html or not invitation.ticket_pdf:
            logger.info(f"Generating tickets for invitation {invitation_id}")
            invitation.generate_tickets()
            invitation.save()
        
        # Send the email
        logger.info(f"Sending test email to {email}")
        view_set = InvitationViewSet()
        view_set.send_invitation_email(invitation)
        
        # Restore original email
        invitation.guest_email = original_email
        invitation.save(update_fields=['guest_email'])
        
        return JsonResponse({
            'success': True,
            'message': f'Test email sent to {email}',
            'html_ticket_url': invitation.ticket_html.url if invitation.ticket_html else None,
            'pdf_ticket_url': invitation.ticket_pdf.url if invitation.ticket_pdf else None
        })
    except Invitation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': f'Invitation with ID {invitation_id} not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error sending test email: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)