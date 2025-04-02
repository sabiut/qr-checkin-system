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
        
    def get_qr_code_html(self, qr_code_data_uri, qr_code_url):
        """Generate HTML for the QR code with proper styling for all devices"""
        # Enhanced mobile-friendly styling
        img_style = (
            "display: block; "
            "max-width: 180px; "
            "width: 100%; "
            "height: auto; "
            "margin: 0 auto; "
            "border: 8px solid white; "
            "box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1); "
            "-webkit-box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1); " # Safari support
            "border-radius: 4px; "
        )
        
        # Add width and height attributes to help email clients with image rendering
        if qr_code_data_uri:
            logger.info(f"Using data URI for QR code in email (length: {len(qr_code_data_uri) if qr_code_data_uri else 0})")
            return f'<img src="{qr_code_data_uri}" width="180" height="180" alt="QR Code" style="{img_style}">'
        elif qr_code_url:
            logger.info(f"Using URL for QR code in email: {qr_code_url}")
            return f'<img src="{qr_code_url}" width="180" height="180" alt="QR Code" style="{img_style}">'
        else:
            logger.warning("No QR code available for email")
            placeholder_style = (
                "display: block; "
                "width: 180px; "
                "height: 180px; "
                "margin: 0 auto; "
                "background: #f1f1f1; "
                "border: 8px solid white; "
                "box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1); "
                "text-align: center; "
                "line-height: 180px; "
                "color: #888; "
                "font-size: 14px; "
            )
            return f'<div style="{placeholder_style}">(QR code not available)</div>'
    
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
                
            # For direct browser viewing, we need to make sure QR code is visible
            # Try to regenerate and embed QR code directly into the HTML
            qr_code_data_uri = invitation.get_qr_code_base64()
            
            if qr_code_data_uri:
                logger.info(f"Generated base64 QR code for viewing ticket {invitation.id}")
                # Try to replace the QR code image with our data URI version
                if invitation.qr_code and invitation.qr_code.url:
                    qr_code_url = invitation.qr_code.url
                    if qr_code_url.startswith('/'):
                        from django.conf import settings
                        base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
                        absolute_qr_url = f"{base_url}{qr_code_url}"
                        # Replace the URL with our data URI
                        html_content = html_content.replace(f'src="{qr_code_url}"', f'src="{qr_code_data_uri}"')
                        html_content = html_content.replace(f'src="{absolute_qr_url}"', f'src="{qr_code_data_uri}"')
            else:
                # Fallback to making URLs absolute
                logger.warning(f"Could not generate QR code data URI for ticket {invitation.id}, using URL fallback")
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
            
            # Get QR code URL and data URI for embedding in email
            qr_code_url = None
            
            # Use the helper method to get a base64 encoded QR code
            qr_code_data_uri = invitation.get_qr_code_base64()
            if qr_code_data_uri:
                logger.info(f"Successfully created QR code data URI for email for invitation {invitation.id}")
            else:
                logger.warning(f"Could not create QR code data URI for email for invitation {invitation.id}")
            
            # Always set up URL as fallback
            if invitation.qr_code:
                qr_code_url = invitation.qr_code.url
                if qr_code_url.startswith('/'):
                    qr_code_url = f"{base_url}{qr_code_url}"
                logger.info(f"Using fallback QR code URL for email: {qr_code_url}")
                    
            # HTML message with embedded ticket
            html_message = f"""
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{ font-family: 'Helvetica', 'Arial', sans-serif; margin: 0; padding: 0; color: #333; background-color: #f9f9f9; }}
                    .email-container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .email-header {{ background: linear-gradient(135deg, #4f46e5 0%, #2e27c0 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .email-header h1 {{ margin: 0; font-size: 24px; font-weight: 700; }}
                    .email-content {{ background-color: #ffffff; padding: 30px; border-radius: 0 0 8px 8px; }}
                    .email-footer {{ margin-top: 20px; text-align: center; font-size: 12px; color: #888; }}
                    .email-greeting {{ margin-bottom: 25px; font-size: 16px; }}
                    
                    /* Ticket styles */
                    .ticket {{ background-color: white; border-radius: 16px; overflow: hidden; box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1); margin: 25px 0; border: 1px solid #e5e5e5; }}
                    .ticket-header {{ background: linear-gradient(135deg, #4f46e5 0%, #2e27c0 100%); color: white; padding: 20px; text-align: center; }}
                    .ticket-header h2 {{ margin: 0; font-size: 18px; font-weight: 700; }}
                    .ticket-header h3 {{ margin: 5px 0 0; font-size: 14px; font-weight: 400; opacity: 0.9; }}
                    .ticket-content {{ display: flex; flex-direction: column; }}
                    .ticket-details {{ padding: 20px; }}
                    .ticket-section {{ margin-bottom: 20px; }}
                    .ticket-section-title {{ font-size: 14px; text-transform: uppercase; color: #4f46e5; margin: 0 0 10px 0; font-weight: 600; letter-spacing: 1px; border-bottom: 1px solid #f0f0f0; padding-bottom: 5px; }}
                    .ticket-info-row {{ margin-bottom: 8px; }}
                    .ticket-info-label {{ font-weight: 600; color: #666; display: inline-block; width: 80px; }}
                    .ticket-qr {{ padding: 20px; text-align: center; background-color: #f9f9f9; }}
                    .ticket-qr img {{ max-width: 150px; height: auto; border: 8px solid white; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1); }}
                    .ticket-instructions {{ font-size: 12px; color: #666; margin-top: 10px; }}
                    .ticket-id {{ font-size: 11px; color: #999; margin-top: 5px; }}
                    .ticket-footer {{ background-color: #f8f8f8; padding: 15px; text-align: center; font-size: 11px; color: #888; border-top: 1px solid #eaeaea; }}
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="email-header">
                        <h1>Your Ticket for {event.name}</h1>
                    </div>
                    <div class="email-content">
                        <div class="email-greeting">
                            <p>Hello {invitation.guest_name},</p>
                            <p>Thank you for registering for <strong>{event.name}</strong>! Your e-ticket is below.</p>
                        </div>
                        
                        <!-- Embedded Ticket -->
                        <div class="ticket">
                            <div class="ticket-header">
                                <h2>{event.name}</h2>
                                <h3>Admission Ticket</h3>
                            </div>
                            <div class="ticket-content">
                                <div class="ticket-details">
                                    <div class="ticket-section">
                                        <h4 class="ticket-section-title">Guest Information</h4>
                                        <div class="ticket-info-row">
                                            <span class="ticket-info-label">Name:</span>
                                            <span>{invitation.guest_name}</span>
                                        </div>
                                        {f'<div class="ticket-info-row"><span class="ticket-info-label">Email:</span><span>{invitation.guest_email}</span></div>' if invitation.guest_email else ''}
                                        {f'<div class="ticket-info-row"><span class="ticket-info-label">Phone:</span><span>{invitation.guest_phone}</span></div>' if invitation.guest_phone else ''}
                                    </div>
                                    
                                    <div class="ticket-section">
                                        <h4 class="ticket-section-title">Event Details</h4>
                                        <div class="ticket-info-row">
                                            <span class="ticket-info-label">Date:</span>
                                            <span>{event.date}</span>
                                        </div>
                                        <div class="ticket-info-row">
                                            <span class="ticket-info-label">Time:</span>
                                            <span>{event.time}</span>
                                        </div>
                                        <div class="ticket-info-row">
                                            <span class="ticket-info-label">Location:</span>
                                            <span>{event.location}</span>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="ticket-qr">
                                    <!-- QR Code Image with improved visibility -->
                                    {self.get_qr_code_html(qr_code_data_uri, qr_code_url)}
                                    <div class="ticket-instructions">Scan for check-in</div>
                                    <div class="ticket-id">Ticket ID: {invitation.id}</div>
                                </div>
                                
                                <div class="ticket-footer">
                                    <p>Please present this QR code at the venue for quick check-in.</p>
                                </div>
                            </div>
                        </div>
                        
                        <p>Please save this email and present the QR code at the event entrance for quick check-in.</p>
                        <p>You can also access your ticket online at: <a href="{ticket_view_url}">{ticket_view_url}</a></p>
                        
                        <p>We look forward to seeing you!</p>
                    </div>
                    <div class="email-footer">
                        <p>This is an automated message from the QR Check-in System.</p>
                        <p>&copy; 2025 QR Check-in System. All rights reserved.</p>
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
            
            # Try to attach the QR code as a Content-ID (CID) attachment
            qr_cid = None
            if invitation.qr_code and hasattr(invitation.qr_code, 'path') and os.path.exists(invitation.qr_code.path):
                try:
                    with open(invitation.qr_code.path, 'rb') as f:
                        qr_image_data = f.read()
                    
                    # Generate a Content-ID for the image
                    qr_cid = f"<qrcode_{invitation.id}@qrticket.app>"
                    
                    # Attach the image with the Content-ID
                    from email.mime.image import MIMEImage
                    img = MIMEImage(qr_image_data)
                    img.add_header('Content-ID', qr_cid)
                    img.add_header('Content-Disposition', 'inline')
                    email.attach(img)
                    
                    logger.info(f"Attached QR code as CID: {qr_cid}")
                    
                    # Create a version of HTML with CID image reference
                    cid_html_message = html_message
                    
                    # Replace any QR code references with our CID reference
                    if qr_code_data_uri:
                        cid_html_message = cid_html_message.replace(
                            f'src="{qr_code_data_uri}"', 
                            f'src="cid:{qr_cid[1:-1]}"'
                        )
                    if qr_code_url:
                        cid_html_message = cid_html_message.replace(
                            f'src="{qr_code_url}"', 
                            f'src="cid:{qr_cid[1:-1]}"'
                        )
                    
                    # Use the CID version of the HTML
                    html_message = cid_html_message
                    logger.info("Using HTML with CID reference to QR code")
                except Exception as e:
                    logger.error(f"Failed to attach QR code as CID: {str(e)}")
                    # Continue with the original HTML that has data URI or URL
            
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
        
        # Get QR code URL and data URI for embedding in email
        qr_code_url = None
        
        # Use the helper method to get a base64 encoded QR code
        qr_code_data_uri = invitation.get_qr_code_base64()
        if qr_code_data_uri:
            logger.info(f"Successfully created QR code data URI for email for invitation {invitation.id}")
        else:
            logger.warning(f"Could not create QR code data URI for email for invitation {invitation.id}")
        
        # Always set up URL as fallback
        if invitation.qr_code:
            qr_code_url = invitation.qr_code.url
            if qr_code_url.startswith('/'):
                qr_code_url = f"{base_url}{qr_code_url}"
            logger.info(f"Using fallback QR code URL for email: {qr_code_url}")
                
        # HTML message with embedded ticket
        html_message = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: 'Helvetica', 'Arial', sans-serif; margin: 0; padding: 0; color: #333; background-color: #f9f9f9; }}
                .email-container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .email-header {{ background: linear-gradient(135deg, #4f46e5 0%, #2e27c0 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .email-header h1 {{ margin: 0; font-size: 24px; font-weight: 700; }}
                .email-content {{ background-color: #ffffff; padding: 30px; border-radius: 0 0 8px 8px; }}
                .email-footer {{ margin-top: 20px; text-align: center; font-size: 12px; color: #888; }}
                .email-greeting {{ margin-bottom: 25px; font-size: 16px; }}
                
                /* Ticket styles */
                .ticket {{ background-color: white; border-radius: 16px; overflow: hidden; box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1); margin: 25px 0; border: 1px solid #e5e5e5; }}
                .ticket-header {{ background: linear-gradient(135deg, #4f46e5 0%, #2e27c0 100%); color: white; padding: 20px; text-align: center; }}
                .ticket-header h2 {{ margin: 0; font-size: 18px; font-weight: 700; }}
                .ticket-header h3 {{ margin: 5px 0 0; font-size: 14px; font-weight: 400; opacity: 0.9; }}
                .ticket-content {{ display: flex; flex-direction: column; }}
                .ticket-details {{ padding: 20px; }}
                .ticket-section {{ margin-bottom: 20px; }}
                .ticket-section-title {{ font-size: 14px; text-transform: uppercase; color: #4f46e5; margin: 0 0 10px 0; font-weight: 600; letter-spacing: 1px; border-bottom: 1px solid #f0f0f0; padding-bottom: 5px; }}
                .ticket-info-row {{ margin-bottom: 8px; }}
                .ticket-info-label {{ font-weight: 600; color: #666; display: inline-block; width: 80px; }}
                .ticket-qr {{ padding: 20px; text-align: center; background-color: #f9f9f9; }}
                .ticket-qr img {{ max-width: 150px; height: auto; border: 8px solid white; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1); }}
                .ticket-instructions {{ font-size: 12px; color: #666; margin-top: 10px; }}
                .ticket-id {{ font-size: 11px; color: #999; margin-top: 5px; }}
                .ticket-footer {{ background-color: #f8f8f8; padding: 15px; text-align: center; font-size: 11px; color: #888; border-top: 1px solid #eaeaea; }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="email-header">
                    <h1>Your Ticket for {event.name}</h1>
                </div>
                <div class="email-content">
                    <div class="email-greeting">
                        <p>Hello {invitation.guest_name},</p>
                        <p>Thank you for registering for <strong>{event.name}</strong>! Your e-ticket is below.</p>
                    </div>
                    
                    <!-- Embedded Ticket -->
                    <div class="ticket">
                        <div class="ticket-header">
                            <h2>{event.name}</h2>
                            <h3>Admission Ticket</h3>
                        </div>
                        <div class="ticket-content">
                            <div class="ticket-details">
                                <div class="ticket-section">
                                    <h4 class="ticket-section-title">Guest Information</h4>
                                    <div class="ticket-info-row">
                                        <span class="ticket-info-label">Name:</span>
                                        <span>{invitation.guest_name}</span>
                                    </div>
                                    {f'<div class="ticket-info-row"><span class="ticket-info-label">Email:</span><span>{invitation.guest_email}</span></div>' if invitation.guest_email else ''}
                                    {f'<div class="ticket-info-row"><span class="ticket-info-label">Phone:</span><span>{invitation.guest_phone}</span></div>' if invitation.guest_phone else ''}
                                </div>
                                
                                <div class="ticket-section">
                                    <h4 class="ticket-section-title">Event Details</h4>
                                    <div class="ticket-info-row">
                                        <span class="ticket-info-label">Date:</span>
                                        <span>{event.date}</span>
                                    </div>
                                    <div class="ticket-info-row">
                                        <span class="ticket-info-label">Time:</span>
                                        <span>{event.time}</span>
                                    </div>
                                    <div class="ticket-info-row">
                                        <span class="ticket-info-label">Location:</span>
                                        <span>{event.location}</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="ticket-qr">
                                <!-- QR Code Image with improved visibility -->
                                {self.get_qr_code_html(qr_code_data_uri, qr_code_url)}
                                <div class="ticket-instructions">Scan for check-in</div>
                                <div class="ticket-id">Ticket ID: {invitation.id}</div>
                            </div>
                            
                            <div class="ticket-footer">
                                <p>Please present this QR code at the venue for quick check-in.</p>
                            </div>
                        </div>
                    </div>
                    
                    <p>Please save this email and present the QR code at the event entrance for quick check-in.</p>
                    <p>You can also access your ticket online at: <a href="{ticket_view_url}">{ticket_view_url}</a></p>
                    
                    <p>We look forward to seeing you!</p>
                </div>
                <div class="email-footer">
                    <p>This is an automated message from the QR Check-in System.</p>
                    <p>&copy; 2025 QR Check-in System. All rights reserved.</p>
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
            
            # Try to attach the QR code as a Content-ID (CID) attachment
            qr_cid = None
            if invitation.qr_code and hasattr(invitation.qr_code, 'path') and os.path.exists(invitation.qr_code.path):
                try:
                    with open(invitation.qr_code.path, 'rb') as f:
                        qr_image_data = f.read()
                    
                    # Generate a Content-ID for the image
                    qr_cid = f"<qrcode_{invitation.id}@qrticket.app>"
                    
                    # Attach the image with the Content-ID
                    from email.mime.image import MIMEImage
                    img = MIMEImage(qr_image_data)
                    img.add_header('Content-ID', qr_cid)
                    img.add_header('Content-Disposition', 'inline')
                    email.attach(img)
                    
                    logger.info(f"Attached QR code as CID: {qr_cid}")
                    
                    # Create a version of HTML with CID image reference
                    cid_html_message = html_message
                    
                    # Replace any QR code references with our CID reference
                    if qr_code_data_uri:
                        cid_html_message = cid_html_message.replace(
                            f'src="{qr_code_data_uri}"', 
                            f'src="cid:{qr_cid[1:-1]}"'
                        )
                    if qr_code_url:
                        cid_html_message = cid_html_message.replace(
                            f'src="{qr_code_url}"', 
                            f'src="cid:{qr_cid[1:-1]}"'
                        )
                    
                    # Use the CID version of the HTML
                    html_message = cid_html_message
                    logger.info("Using HTML with CID reference to QR code")
                except Exception as e:
                    logger.error(f"Failed to attach QR code as CID: {str(e)}")
                    # Continue with the original HTML that has data URI or URL
            
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