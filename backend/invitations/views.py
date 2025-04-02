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
import smtplib
from datetime import datetime

logger = logging.getLogger(__name__)

class InvitationViewSet(viewsets.ModelViewSet):
    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer
    permission_classes = [IsAuthenticated]  # Default to authenticated users only
    
    def get_permissions(self):
        """
        - Require authentication for all invitation operations including viewing tickets
        """
        permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Override create to send email with ticket."""
        invitation = serializer.save()
        logger.info(f"Created invitation {invitation.id}")
        
        # Wait for tickets to be generated
        # At this point, save() in the model should have generated the tickets
        if invitation.guest_email:
            logger.info(f"Invitation has email ({invitation.guest_email}), sending email...")
            
            # Make sure tickets are generated before trying to send email
            if not invitation.ticket_html or not invitation.ticket_pdf:
                logger.info(f"Tickets not found for invitation {invitation.id}, generating them now")
                try:
                    invitation.generate_tickets()
                    invitation.save()
                    logger.info(f"Tickets generated for invitation {invitation.id}")
                except Exception as e:
                    logger.error(f"Failed to generate tickets for invitation {invitation.id}: {str(e)}")
            
            # Now try to send the email
            try:
                # Use the existing endpoint to send the email
                self.get_object = lambda: invitation  # Temporarily set get_object to return our invitation
                response = self.send_email(request=None, pk=invitation.id)
                if response.status_code >= 400:
                    logger.error(f"Failed to send email: {response.data}")
                else:
                    logger.info(f"Email sent successfully to {invitation.guest_email}")
            except Exception as e:
                logger.error(f"Failed to send invitation email: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                
        return invitation
    
    def get_queryset(self):
        """
        Filter invitations to only show those for events the user owns,
        or all invitations if the user is staff
        """
        user = self.request.user
        
        # Staff can see all invitations
        if user.is_staff:
            queryset = Invitation.objects.all()
        else:
            # Regular users can only see invitations for events they own
            queryset = Invitation.objects.filter(event__owner=user)
            
        # Filter by event_id if provided
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
        
        logger.info(f"Manual email request for invitation {invitation.id} to {invitation.guest_email}")
        
        # Check if we have ticket files
        if not invitation.ticket_html and not invitation.ticket_pdf:
            logger.info(f"No tickets found for invitation {invitation.id}, generating them now")
            try:
                invitation.generate_tickets()
                invitation.save()
                logger.info(f"Tickets generated for invitation {invitation.id}")
            except Exception as e:
                logger.error(f"Failed to generate tickets for invitation {invitation.id}: {str(e)}")
        
        # Verify email configuration
        if settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
            if not settings.EMAIL_HOST or not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
                error_msg = "SMTP email settings are incomplete. Check EMAIL_HOST, EMAIL_HOST_USER, and EMAIL_HOST_PASSWORD."
                logger.error(error_msg)
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
        try:
            # Get the event details
            event = invitation.event
            
            # Build base URL for links - using a default for development
            base_url = settings.BASE_URL if hasattr(settings, 'BASE_URL') else "http://localhost:8000"
            
            # Get ticket URLs
            ticket_view_url = f"{base_url}/tickets/{invitation.id}/"
            
            # Email subject
            subject = f"Your Ticket for {event.name}"
            
            # Plain text message
            message = f"""
            Hello {invitation.guest_name},
            
            Your ticket for {event.name} is ready.
            
            Event Details:
            - Date: {event.date}
            - Time: {event.time}
            - Location: {event.location}
            
            Please bring your ticket with the QR code to the event for quick check-in.
            You can view your ticket online at: {ticket_view_url}
            
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
                        
                        <p>You can view your ticket online by clicking the button below:</p>
                        
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
            logger.info(f"Email settings for manual send - Backend: {settings.EMAIL_BACKEND}")
            logger.info(f"Email settings for manual send - Host: {settings.EMAIL_HOST}")
            logger.info(f"Email settings for manual send - Port: {settings.EMAIL_PORT}")
            logger.info(f"Email settings for manual send - TLS: {settings.EMAIL_USE_TLS}")
            logger.info(f"Email settings for manual send - User: {settings.EMAIL_HOST_USER}")
            logger.info(f"Email settings for manual send - From: {settings.DEFAULT_FROM_EMAIL}")
            
            # Verify needed settings before proceeding
            if settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
                # Check all required SMTP settings are present
                missing_settings = []
                if not settings.EMAIL_HOST:
                    missing_settings.append("EMAIL_HOST")
                if not settings.EMAIL_PORT:
                    missing_settings.append("EMAIL_PORT")
                if not settings.EMAIL_HOST_USER:
                    missing_settings.append("EMAIL_HOST_USER")
                if not settings.EMAIL_HOST_PASSWORD:
                    missing_settings.append("EMAIL_HOST_PASSWORD")
                
                if missing_settings:
                    error_msg = f"Missing required SMTP settings: {', '.join(missing_settings)}"
                    logger.error(error_msg)
                    return Response(
                        {'error': error_msg},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            
            # Try creating a direct SMTP connection to validate credentials
            if settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
                try:
                    logger.info("Testing direct SMTP connection before sending...")
                    server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
                    server.set_debuglevel(1)  # Verbose logging
                    
                    if settings.EMAIL_USE_TLS:
                        server.starttls()
                        
                    if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
                        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                        
                    server.quit()
                    logger.info("Direct SMTP connection successful.")
                except Exception as smtp_test_error:
                    error_msg = f"Failed to connect to SMTP server: {str(smtp_test_error)}"
                    logger.error(error_msg)
                    return Response(
                        {'error': error_msg},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                    
            # Now create the Django connection
            from django.core.mail import get_connection
            logger.info("Creating Django email connection...")
            connection = get_connection(
                backend=settings.EMAIL_BACKEND,
                host=settings.EMAIL_HOST,
                port=settings.EMAIL_PORT,
                username=settings.EMAIL_HOST_USER,
                password=settings.EMAIL_HOST_PASSWORD,
                use_tls=settings.EMAIL_USE_TLS,
                fail_silently=False,
            )
            
            # Create the email message
            from django.core.mail import EmailMultiAlternatives
            email = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[invitation.guest_email],
                connection=connection,
            )
            
            # Attach HTML content
            email.attach_alternative(html_message, "text/html")
            
            # PDF ticket attachment was removed to simplify email sending
            logger.info("PDF attachment is disabled to avoid potential issues")
            
            # HTML ticket attachment was removed to simplify email sending
            logger.info("HTML attachment is disabled to avoid potential issues")
            
            # Send the email
            logger.info(f"Sending email to {invitation.guest_email}...")
            logger.info(f"Email connection: {email.connection}")
            logger.info(f"Email subject: {email.subject}")
            logger.info(f"Email from: {email.from_email}")
            logger.info(f"Email to: {email.to}")
            
            try:
                result = email.send(fail_silently=False)
                logger.info(f"Email send result: {result}")
                
                # Log more details about the SMTP server response if available
                if hasattr(email.connection, 'last_response'):
                    logger.info(f"SMTP server last response: {email.connection.last_response}")
            except Exception as send_error:
                logger.error(f"Exception during email.send(): {str(send_error)}")
                # Re-raise to be caught by the outer try-except
                raise
            
            return Response({'message': f'Invitation email sent successfully to {invitation.guest_email}'})
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP Authentication Error: {str(e)}"
            logger.error(error_msg)
            logger.error("This is likely due to incorrect username/password or Gmail security settings.")
            logger.error("For Gmail, make sure you're using an App Password if 2FA is enabled.")
            return Response(
                {'error': error_msg},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except smtplib.SMTPException as e:
            error_msg = f"SMTP Error: {str(e)}"
            logger.error(error_msg)
            return Response(
                {'error': error_msg},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Failed to send invitation email: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
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
        
        # Verify email config is set
        if not settings.EMAIL_HOST or not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            logger.warning("Email configuration is incomplete. Check EMAIL_HOST, EMAIL_HOST_USER, and EMAIL_HOST_PASSWORD settings.")
            if settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
                logger.warning("Using SMTP backend but credentials are missing. Email may fail to send.")
        
        # Plain text message
        message = f"""
        Hello {invitation.guest_name},
        
        Your ticket for {event.name} is ready.
        
        Event Details:
        - Date: {event.date}
        - Time: {event.time}
        - Location: {event.location}
        
        Please bring your ticket with the QR code to the event for quick check-in.
        You can view your ticket online at: {ticket_view_url}
        
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
                    
                    <p>You can view your ticket online by clicking the button below:</p>
                    
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
            
            # PDF ticket attachment was removed to simplify email sending
            logger.info("PDF attachment is disabled to avoid potential issues")
            
            # HTML ticket attachment was removed to simplify email sending
            logger.info("HTML attachment is disabled to avoid potential issues")
                
            # Send email
            logger.info("Sending email...")
            
            # Add debugging information for connection
            if email.connection:
                try:
                    connection_debug = email.connection.open()
                    logger.info(f"Email connection opened: {connection_debug}")
                except Exception as conn_err:
                    logger.error(f"Error opening email connection: {str(conn_err)}")
            else:
                logger.error("Email connection is None. Creating a new connection.")
                from django.core.mail import get_connection
                email.connection = get_connection(
                    backend=settings.EMAIL_BACKEND,
                    host=settings.EMAIL_HOST,
                    port=settings.EMAIL_PORT,
                    username=settings.EMAIL_HOST_USER,
                    password=settings.EMAIL_HOST_PASSWORD,
                    use_tls=settings.EMAIL_USE_TLS,
                )
            
            result = email.send()
            logger.info(f"Email send result: {result}")
            return True
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication Error: {str(e)}")
            logger.error("This is likely due to incorrect username/password or Gmail security settings.")
            logger.error("For Gmail, make sure you're using an App Password if 2FA is enabled.")
            logger.error("Check: https://myaccount.google.com/apppasswords")
            import traceback
            logger.error(traceback.format_exc())
            raise
        except smtplib.SMTPException as e:
            logger.error(f"SMTP Error: {str(e)}")
            logger.error("This could be due to incorrect host/port or network connectivity issues.")
            import traceback
            logger.error(traceback.format_exc())
            raise
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
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': 'Authentication required'
        }, status=401)
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
def simple_test_email(request):
    """Super simple email test without any attachments or complex logic"""
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': 'Authentication required'
        }, status=401)
    # Get the test email from request or use a default
    email = request.data.get('email', None)
    if not email:
        return JsonResponse({
            'success': False,
            'error': 'Email address is required'
        }, status=400)
    
    logger.info(f"Simple test email requested for {email}")
    
    # Log email settings for debugging
    logger.info("=================== EMAIL SETTINGS ===================")
    logger.info(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    logger.info(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    logger.info(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    logger.info(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    logger.info(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    logger.info(f"EMAIL_HOST_PASSWORD: {'*****' if settings.EMAIL_HOST_PASSWORD else 'NOT SET'}")
    logger.info(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    logger.info("====================================================")
    
    try:
        # Create a simple email message
        from django.core.mail import EmailMessage
        
        # Create a direct connection
        from django.core.mail import get_connection
        connection = get_connection(
            backend=settings.EMAIL_BACKEND,
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            use_tls=settings.EMAIL_USE_TLS,
            fail_silently=False,
        )
        
        # Try to open the connection explicitly
        try:
            connection.open()
            logger.info("Connection opened successfully")
        except Exception as conn_error:
            logger.error(f"Error opening connection: {str(conn_error)}")
            return JsonResponse({
                'success': False,
                'error': f'Failed to connect to mail server: {str(conn_error)}'
            }, status=500)
        
        # Create and send the message
        subject = "Test Email from QR Check-in System"
        body = f"This is a test email sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
        email_msg = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
            connection=connection,
        )
        
        # Try to send
        logger.info(f"Sending simple test email to {email}...")
        result = email_msg.send(fail_silently=False)
        logger.info(f"Email sent result: {result}")
        
        # Finally close the connection
        connection.close()
        
        return JsonResponse({
            'success': True,
            'message': f'Simple test email sent to {email}'
        })
    except Exception as e:
        logger.error(f"Error in simple test email: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['POST'])
@csrf_exempt
def test_email_delivery(request, invitation_id):
    """Test endpoint to send an invitation email with ticket attachments"""
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': 'Authentication required'
        }, status=401)
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