from django.db import models
import uuid
import qrcode
import os
import base64
from io import BytesIO
from django.core.files import File
from PIL import Image, ImageDraw
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
import logging

# We're deliberately not importing WeasyPrint due to compatibility issues
# Instead, we use ReportLab for PDF generation

logger = logging.getLogger(__name__)


class TicketFormat(models.TextChoices):
    HTML = 'HTML', 'HTML'
    PDF = 'PDF', 'PDF'
    BOTH = 'BOTH', 'Both'


class Invitation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE, related_name='invitations')
    guest_name = models.CharField(max_length=255)
    guest_email = models.EmailField(blank=True)
    guest_phone = models.CharField(max_length=20, blank=True)
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    ticket_html = models.FileField(upload_to='tickets/html/', blank=True, null=True)
    ticket_pdf = models.FileField(upload_to='tickets/pdf/', blank=True, null=True)
    ticket_format = models.CharField(
        max_length=10,
        choices=TicketFormat.choices,
        default=TicketFormat.BOTH
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.guest_name} - {self.event.name}"
    
    def save(self, *args, **kwargs):
        try:
            logger.info(f"Starting save for invitation {self.id if self.id else 'new'}")
            
            # Generate QR code if it doesn't exist
            if not self.qr_code:
                logger.info(f"Generating QR code for invitation {self.id if self.id else 'new'}")
                self.generate_qr_code()
                logger.info(f"QR code generated successfully")
            
            # Save first to make sure we have an ID and QR code URL
            logger.info(f"Performing initial save to get ID and QR code URL")
            super().save(*args, **kwargs)
            logger.info(f"Initial save completed, invitation ID: {self.id}")
            
            # Generate tickets after initial save (we need the ID first)
            try:
                # Check if we need to generate tickets
                need_ticket_generation = not self.ticket_html or not self.ticket_pdf
                logger.info(f"Need ticket generation? {need_ticket_generation} (HTML: {bool(self.ticket_html)}, PDF: {bool(self.ticket_pdf)})")
                
                if need_ticket_generation:
                    self.generate_tickets()
                    
                    # Save again to store the tickets
                    logger.info(f"Performing second save to store tickets")
                    if 'update_fields' in kwargs:
                        updated_fields = list(kwargs['update_fields']) + ['ticket_html', 'ticket_pdf']
                        logger.info(f"Using update_fields: {updated_fields}")
                        kwargs['update_fields'] = updated_fields
                        super().save(*args, **kwargs)
                    else:
                        try:
                            logger.info(f"Using targeted update_fields save")
                            super().save(update_fields=['ticket_html', 'ticket_pdf'])
                        except Exception as e:
                            # If update_fields fails, try a regular save
                            logger.error(f"Error in update_fields save: {str(e)}")
                            logger.info(f"Falling back to regular save")
                            super().save()
                    
                    logger.info(f"Second save completed")
            except Exception as e:
                # Log but don't fail the whole save if ticket generation fails
                logger.error(f"Error generating tickets: {str(e)}")
                
                # Check what files were created
                logger.info(f"After error - HTML ticket exists? {bool(self.ticket_html)}")
                logger.info(f"After error - PDF ticket exists? {bool(self.ticket_pdf)}")
                
        except Exception as e:
            # This is the outer exception handler - we shouldn't get here,
            # but if we do, re-raise to avoid data corruption
            logger.error(f"Critical error in invitation save: {str(e)}")
            raise
            
        # Final check to see what was actually saved
        logger.info(f"End of save - Invitation {self.id} - QR code exists? {bool(self.qr_code)}")
        logger.info(f"End of save - Invitation {self.id} - HTML ticket exists? {bool(self.ticket_html)}")
        logger.info(f"End of save - Invitation {self.id} - PDF ticket exists? {bool(self.ticket_pdf)}")
    
    def generate_qr_code(self):
        """Generate QR code for this invitation optimized for all devices"""
        # Use higher error correction for better scanning on various devices
        # Use a slightly larger box size for better visibility on small screens
        qr = qrcode.QRCode(
            version=4,  # Automatically adjust size as needed
            error_correction=qrcode.constants.ERROR_CORRECT_Q,  # Higher error correction
            box_size=12,  # Slightly larger boxes for better scanning
            border=4,     # Standard quiet zone
        )
        
        # Add the invitation ID as data
        qr.add_data(str(self.id))
        qr.make(fit=True)
        
        # Create a high-contrast QR code
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        self.qr_code.save(f"qrcode-{self.id}.png", File(buffer), save=False)
        buffer.close()
    
    def get_qr_code_image(self):
        """Get QR code as a PIL Image object, generating it if needed"""
        # If we already have a QR code file saved, try to open it
        if self.qr_code and hasattr(self.qr_code, 'path') and os.path.exists(self.qr_code.path):
            try:
                return Image.open(self.qr_code.path)
            except Exception as e:
                logger.error(f"Error opening existing QR code: {str(e)}")
        
        # If we couldn't load the existing QR code or it doesn't exist, generate a new one
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(str(self.id))
        qr.make(fit=True)
        
        # Return the QR code as a PIL Image
        return qr.make_image(fill_color="black", back_color="white")
    
    def get_qr_code_base64(self):
        """Return the QR code as a base64 data URI."""
        if not self.qr_code:
            logger.warning(f"No QR code file exists for invitation {self.id}, generating new one")
            # Generate a new QR code on the fly
            try:
                qr = qrcode.QRCode(
                    version=4,  # Automatically adjust size as needed
                    error_correction=qrcode.constants.ERROR_CORRECT_Q,  # Higher error correction
                    box_size=12,  # Slightly larger boxes for better scanning
                    border=4,     # Standard quiet zone
                )
                qr.add_data(str(self.id))
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                buffer.seek(0)
                encoded_string = base64.b64encode(buffer.read()).decode('utf-8')
                buffer.close()
                
                logger.info(f"Successfully generated new QR code data URI for invitation {self.id}")
                return f"data:image/png;base64,{encoded_string}"
            except Exception as e:
                logger.error(f"Failed to generate new QR code: {str(e)}")
                return None
        
        try:
            # First try to read directly from the file storage
            with self.qr_code.open('rb') as f:
                image_data = f.read()
                if len(image_data) == 0:
                    logger.error(f"QR code file for invitation {self.id} is empty")
                    return None
                    
                encoded = base64.b64encode(image_data).decode('utf-8')
                logger.info(f"Successfully created QR code data URI from storage for invitation {self.id}")
                return f"data:image/png;base64,{encoded}"
        except Exception as e:
            logger.error(f"Failed to read QR code from storage: {str(e)}")
            
            # Fall back to generating a new QR code
            try:
                qr = qrcode.QRCode(
                    version=4,  # Automatically adjust size as needed
                    error_correction=qrcode.constants.ERROR_CORRECT_Q,  # Higher error correction
                    box_size=12,  # Slightly larger boxes for better scanning
                    border=4,     # Standard quiet zone
                )
                qr.add_data(str(self.id))
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                buffer.seek(0)
                encoded_string = base64.b64encode(buffer.read()).decode('utf-8')
                buffer.close()
                
                logger.info(f"Successfully generated fallback QR code data URI for invitation {self.id}")
                return f"data:image/png;base64,{encoded_string}"
            except Exception as e2:
                logger.error(f"Failed to create fallback QR code: {str(e2)}")
                return None
        
    def generate_tickets(self):
        """Generate HTML and PDF tickets based on the invitation details"""
        logger.info(f"Starting ticket generation for invitation {self.id}")
        
        # First generate HTML ticket
        if self.ticket_format in [TicketFormat.HTML, TicketFormat.BOTH]:
            logger.info(f"Generating HTML ticket for invitation {self.id}")
            self.generate_html_ticket()
            
        # Then generate PDF ticket (from the HTML)
        if self.ticket_format in [TicketFormat.PDF, TicketFormat.BOTH]:
            logger.info(f"Generating PDF ticket for invitation {self.id}")
            try:
                self.generate_pdf_ticket()
            except Exception as e:
                logger.error(f"Failed to generate PDF ticket, but continuing: {str(e)}")
                # PDF generation failure shouldn't stop the process
                pass
            
        logger.info(f"Completed ticket generation for invitation {self.id}")
            
    def generate_html_ticket(self):
        """Generate an HTML ticket based on the invitation details"""
        try:
            logger.info(f"HTML ticket generation started for invitation {self.id}")
            
            if not self.event:
                logger.warning(f"No event found for invitation {self.id}, skipping HTML ticket")
                return
                
            # Get the absolute URL for the QR code
            # For the HTML template, use the full absolute URL with BASE_URL
            from django.conf import settings
            base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
            
            # For QR code, we'll use a data URI to embed it directly in the HTML
            # This ensures it works in emails regardless of server accessibility
            qr_code_url = None
            qr_code_data_uri = None
            
            # Try to get a data URI for the QR code
            qr_code_data_uri = self.get_qr_code_base64()
            if qr_code_data_uri:
                logger.info(f"Successfully created data URI for QR code for invitation {self.id}")
            else:
                logger.warning(f"Failed to create data URI for QR code for invitation {self.id}")
            
            # Set up the URL version as fallback
            if self.qr_code:
                qr_code_url = self.qr_code.url
                if qr_code_url.startswith('/'):
                    qr_code_url = f"{base_url}{qr_code_url}"
                logger.info(f"Using fallback QR code URL: {qr_code_url}")
            else:
                logger.warning(f"No QR code file found for invitation {self.id}")
                
            logger.info(f"QR code URL for invitation {self.id}: {qr_code_url}")
            logger.info(f"QR code data URI created: {bool(qr_code_data_uri)}")
                
            try:
                # Render HTML ticket from template
                context = {
                    'invitation': self,
                    'event': self.event,
                    'qr_code_url': qr_code_url,
                    'qr_code_data_uri': qr_code_data_uri,
                    'base_url': base_url,
                }
                
                logger.info(f"Attempting to render template for invitation {self.id}")
                html_content = render_to_string('invitations/ticket_template.html', context)
                logger.info(f"Template rendered successfully for invitation {self.id}")
            except Exception as template_error:
                # If template rendering fails, fall back to a simple HTML string
                logger.error(f"Error rendering ticket template for invitation {self.id}: {str(template_error)}")
                
                # Generate a simple HTML ticket without template
                logger.info(f"Falling back to simple HTML for invitation {self.id}")
                html_content = self._generate_simple_html_ticket(qr_code_url, qr_code_data_uri)
            
            # Save the HTML ticket
            logger.info(f"Saving HTML ticket for invitation {self.id}")
            html_file = ContentFile(html_content.encode('utf-8'))
            self.ticket_html.save(f"ticket-{self.id}.html", html_file, save=False)
            logger.info(f"HTML ticket saved for invitation {self.id}")
        except Exception as e:
            # Log the error but don't prevent the invite from being created
            logger.error(f"Error generating HTML ticket for invitation {self.id}: {str(e)}")
            # Don't re-raise the exception - allow the invitation to be created
    
    def _generate_simple_html_ticket(self, qr_code_url, qr_code_data_uri=None):
        """Generate a simple HTML ticket as fallback when template rendering fails"""
        event = self.event
        
        # If we have a data URI, use it for the QR code instead of the URL
        qr_code_html = ""
        if qr_code_data_uri:
            qr_code_html = f'<img src="{qr_code_data_uri}" alt="Check-in QR Code">'
        elif qr_code_url:
            qr_code_html = f'<img src="{qr_code_url}" alt="Check-in QR Code">'
        else:
            qr_code_html = '<div style="padding: 60px; text-align: center; border: 10px solid white; box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1); background: #f1f1f1;">(QR code not available)</div>'
        
        # Professional HTML ticket with embedded QR code
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Event Ticket - {event.name}</title>
    <style>
        @page {{
            size: 8.5in 11in;
            margin: 0.3in;
        }}
        body {{
            font-family: 'Helvetica', 'Arial', sans-serif;
            margin: 0;
            padding: 0;
            color: #333;
            background-color: #f9f9f9;
        }}
        .ticket-container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        .ticket {{
            background-color: white;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
            border: 1px solid #e5e5e5;
        }}
        .ticket-header {{
            background: linear-gradient(135deg, #4f46e5 0%, #2e27c0 100%);
            color: white;
            padding: 30px;
            text-align: center;
            position: relative;
        }}
        .ticket-header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }}
        .ticket-header h2 {{
            margin: 5px 0 0;
            font-size: 18px;
            font-weight: 400;
            opacity: 0.9;
        }}
        .ticket-content {{
            display: flex;
            padding: 0;
        }}
        .ticket-info {{
            flex: 1;
            padding: 25px;
            border-right: 1px dashed #e5e5e5;
        }}
        .ticket-qr {{
            width: 230px;
            padding: 25px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background-color: #f9f9f9;
        }}
        .section {{
            margin-bottom: 25px;
        }}
        .section:last-child {{
            margin-bottom: 0;
        }}
        .section-title {{
            font-size: 16px;
            text-transform: uppercase;
            color: #4f46e5;
            margin: 0 0 15px 0;
            font-weight: 600;
            letter-spacing: 1px;
            border-bottom: 2px solid #f0f0f0;
            padding-bottom: 8px;
        }}
        .info-row {{
            display: flex;
            margin-bottom: 10px;
        }}
        .info-label {{
            color: #666;
            font-weight: 600;
            width: 90px;
            flex-shrink: 0;
        }}
        .info-value {{
            color: #333;
            font-weight: 400;
        }}
        .qr-code img {{
            width: 180px;
            height: auto;
            border: 10px solid white;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
        }}
        .qr-instructions {{
            margin-top: 15px;
            text-align: center;
            font-size: 12px;
            color: #666;
        }}
        .ticket-footer {{
            background-color: #f8f8f8;
            padding: 15px 25px;
            text-align: center;
            font-size: 12px;
            color: #888;
            border-top: 1px solid #eaeaea;
        }}
        .ticket-id {{
            font-size: 12px;
            margin-top: 10px;
            color: #999;
            text-align: center;
        }}
        .ticket-design-element {{
            position: absolute;
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 50%;
        }}
        .element-1 {{
            width: 80px;
            height: 80px;
            top: -40px;
            left: -20px;
        }}
        .element-2 {{
            width: 60px;
            height: 60px;
            bottom: -30px;
            right: 40px;
        }}
        /* Mobile responsiveness */
        @media (max-width: 600px) {{
            .ticket-content {{
                flex-direction: column;
            }}
            .ticket-info {{
                border-right: none;
                border-bottom: 1px dashed #e5e5e5;
            }}
            .ticket-qr {{
                width: auto;
            }}
        }}
    </style>
</head>
<body>
    <div class="ticket-container">
        <div class="ticket">
            <div class="ticket-header">
                <div class="ticket-design-element element-1"></div>
                <div class="ticket-design-element element-2"></div>
                <h1>{event.name}</h1>
                <h2>Admission Ticket</h2>
            </div>
            <div class="ticket-content">
                <div class="ticket-info">
                    <div class="section">
                        <h3 class="section-title">Guest Information</h3>
                        <div class="info-row">
                            <span class="info-label">Name:</span>
                            <span class="info-value">{self.guest_name}</span>
                        </div>
                        {f'<div class="info-row"><span class="info-label">Email:</span><span class="info-value">{self.guest_email}</span></div>' if self.guest_email else ''}
                        {f'<div class="info-row"><span class="info-label">Phone:</span><span class="info-value">{self.guest_phone}</span></div>' if self.guest_phone else ''}
                    </div>
                    
                    <div class="section">
                        <h3 class="section-title">Event Details</h3>
                        <div class="info-row">
                            <span class="info-label">Date:</span>
                            <span class="info-value">{event.date}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Time:</span>
                            <span class="info-value">{event.time}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Location:</span>
                            <span class="info-value">{event.location}</span>
                        </div>
                        {f'<div class="info-row"><span class="info-label">Details:</span><span class="info-value">{event.description}</span></div>' if event.description else ''}
                    </div>
                </div>
                <div class="ticket-qr">
                    <div class="qr-code">
                        {qr_code_html}
                    </div>
                    <div class="qr-instructions">
                        Scan for check-in
                    </div>
                    <div class="ticket-id">
                        Ticket ID: {self.id}
                    </div>
                </div>
            </div>
            <div class="ticket-footer">
                <p>This ticket is personalized and non-transferrable. Please present this QR code when you arrive at the event.</p>
                <p>Generated by QR Check-in System</p>
            </div>
        </div>
    </div>
</body>
</html>"""
        return html
        
    def generate_pdf_ticket(self):
        """Generate a professional PDF ticket from the HTML ticket"""
        try:
            logger.info("Using ReportLab for professional PDF ticket generation")
                
            if not self.ticket_html:
                self.generate_html_ticket()
                
            if not self.ticket_html:
                return
            
            # Use ReportLab for a professional PDF ticket
            try:
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import letter
                from reportlab.lib import colors
                from reportlab.lib.units import inch
                from reportlab.platypus import Paragraph, Frame
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from io import BytesIO
                
                # Create a buffer and canvas
                buffer = BytesIO()
                p = canvas.Canvas(buffer, pagesize=letter)
                width, height = letter
                
                # Define colors
                primary_color = colors.HexColor('#4f46e5')  # Purple
                light_gray = colors.HexColor('#f9f9f9')
                
                # Set up styles for paragraphs
                styles = getSampleStyleSheet()
                normal_style = styles['Normal']
                
                # Create background for the page
                p.setFillColor(light_gray)
                p.rect(0, 0, width, height, fill=1, stroke=0)
                
                # Create a white ticket area
                margin = 0.5 * inch
                ticket_width = width - 2 * margin
                ticket_height = height - 2 * margin
                p.setFillColor(colors.white)
                p.roundRect(margin, margin, ticket_width, ticket_height, radius=10, fill=1, stroke=0)
                
                # Add a colored header
                header_height = 1.5 * inch
                p.setFillColor(primary_color)
                p.roundRect(margin, height - margin - header_height, 
                          ticket_width, header_height, 
                          radius=10, fill=1, stroke=0)
                
                # Add event name and "Admission Ticket" text in header
                p.setFillColor(colors.white)
                
                # Event name
                p.setFont("Helvetica-Bold", 24)
                event_name = self.event.name
                # If name is too long, use a smaller font
                if len(event_name) > 30:
                    p.setFont("Helvetica-Bold", 18)
                p.drawCentredString(width/2, height - margin - header_height/2 - 0.1*inch, event_name)
                
                # Admission Ticket text
                p.setFont("Helvetica", 16)
                p.drawCentredString(width/2, height - margin - header_height/2 - 0.4*inch, "ADMISSION TICKET")
                
                # Draw a horizontal line under the header
                p.setStrokeColor(colors.lightgrey)
                p.setLineWidth(1)
                p.line(margin + 0.2*inch, height - margin - header_height, 
                      width - margin - 0.2*inch, height - margin - header_height)
                
                # Starting position for content
                y_position = height - margin - header_height - 0.5*inch
                
                # Define column layout
                left_column = margin + 0.5*inch
                right_column = width/2 + 0.5*inch
                
                # Add Guest Information section
                p.setFont("Helvetica-Bold", 14)
                p.setFillColor(primary_color)
                p.drawString(left_column, y_position, "GUEST INFORMATION")
                
                # Add line under section title
                p.setStrokeColor(colors.lightgrey)
                p.line(left_column, y_position - 0.1*inch, 
                      width/2 - 0.5*inch, y_position - 0.1*inch)
                
                # Guest details
                p.setFillColor(colors.black)
                y_position -= 0.5*inch
                p.setFont("Helvetica-Bold", 12)
                p.drawString(left_column, y_position, "Name:")
                p.setFont("Helvetica", 12)
                p.drawString(left_column + 1*inch, y_position, self.guest_name)
                
                if self.guest_email:
                    y_position -= 0.3*inch
                    p.setFont("Helvetica-Bold", 12)
                    p.drawString(left_column, y_position, "Email:")
                    p.setFont("Helvetica", 12)
                    
                    # Handle long email addresses
                    email = self.guest_email
                    if len(email) > 25:
                        p.drawString(left_column + 1*inch, y_position, email[:25] + "...")
                    else:
                        p.drawString(left_column + 1*inch, y_position, email)
                
                if self.guest_phone:
                    y_position -= 0.3*inch
                    p.setFont("Helvetica-Bold", 12)
                    p.drawString(left_column, y_position, "Phone:")
                    p.setFont("Helvetica", 12)
                    p.drawString(left_column + 1*inch, y_position, self.guest_phone)
                
                # Add Event Details section
                y_position -= 0.5*inch
                p.setFont("Helvetica-Bold", 14)
                p.setFillColor(primary_color)
                p.drawString(left_column, y_position, "EVENT DETAILS")
                
                # Add line under section title
                p.setStrokeColor(colors.lightgrey)
                p.line(left_column, y_position - 0.1*inch, 
                      width/2 - 0.5*inch, y_position - 0.1*inch)
                
                # Event details
                p.setFillColor(colors.black)
                y_position -= 0.5*inch
                p.setFont("Helvetica-Bold", 12)
                p.drawString(left_column, y_position, "Date:")
                p.setFont("Helvetica", 12)
                p.drawString(left_column + 1*inch, y_position, str(self.event.date))
                
                y_position -= 0.3*inch
                p.setFont("Helvetica-Bold", 12)
                p.drawString(left_column, y_position, "Time:")
                p.setFont("Helvetica", 12)
                p.drawString(left_column + 1*inch, y_position, str(self.event.time))
                
                y_position -= 0.3*inch
                p.setFont("Helvetica-Bold", 12)
                p.drawString(left_column, y_position, "Location:")
                p.setFont("Helvetica", 12)
                
                # Location might be long, wrap it
                location = str(self.event.location)
                if len(location) > 25:
                    # Create a paragraph for the location
                    location_style = ParagraphStyle(
                        'Location',
                        parent=normal_style,
                        leading=14
                    )
                    location_frame = Frame(
                        left_column + 1*inch, y_position - 0.8*inch, 
                        width/2 - 2*inch, 0.8*inch, 
                        showBoundary=0
                    )
                    location_para = Paragraph(location, location_style)
                    location_frame.addFromList([location_para], p)
                    y_position -= 0.9*inch  # Adjust position
                else:
                    p.drawString(left_column + 1*inch, y_position, location)
                    y_position -= 0.3*inch
                
                # Add QR Code section in right column
                # Create a light gray box for the QR code
                qr_box_top = height - margin - header_height - 0.5*inch
                qr_box_height = 5*inch
                p.setFillColor(light_gray)
                p.roundRect(right_column - 0.5*inch, qr_box_top - qr_box_height, 
                          width/2 - 0.5*inch, qr_box_height, 
                          radius=10, fill=1, stroke=0)
                
                # Add "SCAN FOR CHECK-IN" header
                p.setFillColor(primary_color)
                p.setFont("Helvetica-Bold", 14)
                p.drawCentredString(width - width/4, qr_box_top - 0.7*inch, "SCAN FOR CHECK-IN")
                
                # Add QR Code
                if self.qr_code and os.path.exists(self.qr_code.path):
                    try:
                        from reportlab.lib.utils import ImageReader
                        
                        # Calculate box center for better vertical alignment
                        qr_box_center_y = qr_box_top - (qr_box_height / 2)
                        
                        # Set QR code size (slightly larger)
                        qr_size = 3.2*inch
                        
                        # Center the QR code horizontally and vertically in the box
                        qr_x = width - width/4 - qr_size/2
                        
                        # Position QR code lower by centering it vertically in the box
                        # and adding a small offset to move it down from the header
                        qr_y = qr_box_center_y - qr_size/2 - 0.3*inch
                        
                        # Add white background for QR code with more padding
                        p.setFillColor(colors.white)
                        padding = 0.25*inch
                        p.roundRect(qr_x - padding, qr_y - padding, 
                                  qr_size + 2*padding, qr_size + 2*padding, 
                                  radius=10, fill=1, stroke=0)
                        
                        # Draw QR code
                        p.drawImage(ImageReader(self.qr_code.path), qr_x, qr_y, width=qr_size, height=qr_size)
                        
                        # Add ticket ID
                        p.setFillColor(colors.black)
                        p.setFont("Helvetica", 10)
                        p.drawCentredString(width - width/4, qr_y - 0.5*inch, f"Ticket ID: {self.id}")
                    except Exception as qr_error:
                        logger.error(f"Could not add QR code to PDF: {str(qr_error)}")
                
                # Add footer with dotted line to simulate perforation
                p.setStrokeColor(colors.lightgrey)
                p.setDash([3, 3], 0)
                p.line(margin, margin + 1*inch, width - margin, margin + 1*inch)
                p.setDash([], 0)  # Reset dash pattern
                
                # Add footer text
                p.setFillColor(colors.grey)
                p.setFont("Helvetica-Oblique", 10)
                p.drawString(margin + 0.5*inch, margin + 0.7*inch, 
                           "This ticket is personalized and non-transferrable.")
                p.drawString(margin + 0.5*inch, margin + 0.5*inch, 
                           "Please present this QR code when you arrive at the event.")
                
                # Add generation timestamp
                from datetime import datetime
                now = datetime.now()
                date_str = now.strftime("%Y-%m-%d %H:%M:%S")
                p.setFont("Helvetica", 8)
                p.drawRightString(width - margin - 0.5*inch, margin + 0.5*inch, f"Generated: {date_str}")
                
                # Add company name at bottom
                p.setFillColor(primary_color)
                p.setFont("Helvetica-Bold", 10)
                p.drawCentredString(width/2, margin + 0.2*inch, "QR Check-in System")
                
                # Save the PDF
                p.showPage()
                p.save()
                
                buffer.seek(0)
                pdf_file = ContentFile(buffer.read())
                self.ticket_pdf.save(f"ticket-{self.id}.pdf", pdf_file, save=False)
                
                logger.info(f"Professional PDF ticket generated successfully for invitation {self.id}")
                return True
            except Exception as alt_e:
                logger.error(f"Professional PDF generation failed: {str(alt_e)}")
                # Try a simpler approach as fallback
                return self._generate_simple_pdf_ticket()
                
        except Exception as e:
            logger.error(f"Error generating PDF ticket: {str(e)}")
            return False
    
    def _generate_simple_pdf_ticket(self):
        """Generate a simple PDF ticket as fallback"""
        try:
            logger.info(f"Attempting simpler PDF generation for invitation {self.id}")
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from io import BytesIO
            
            buffer = BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            
            # Add content to the PDF
            p.setFont("Helvetica-Bold", 16)
            p.drawString(100, 750, f"Event Ticket: {self.event.name}")
            
            p.setFont("Helvetica-Bold", 12)
            p.drawString(100, 700, "Guest Information:")
            p.setFont("Helvetica", 12)
            p.drawString(120, 680, f"Name: {self.guest_name}")
            if self.guest_email:
                p.drawString(120, 660, f"Email: {self.guest_email}")
            if self.guest_phone:
                p.drawString(120, 640, f"Phone: {self.guest_phone}")
            
            p.setFont("Helvetica-Bold", 12)
            p.drawString(100, 600, "Event Details:")
            p.setFont("Helvetica", 12)
            p.drawString(120, 580, f"Date: {self.event.date}")
            p.drawString(120, 560, f"Time: {self.event.time}")
            p.drawString(120, 540, f"Location: {self.event.location}")
            
            p.setFont("Helvetica-Bold", 12)
            p.drawString(100, 500, "Ticket ID:")
            p.setFont("Helvetica", 12)
            p.drawString(120, 480, f"{self.id}")
            
            # If QR code exists, try to add it
            if self.qr_code and os.path.exists(self.qr_code.path):
                try:
                    from reportlab.lib.utils import ImageReader
                    p.drawImage(ImageReader(self.qr_code.path), 250, 300, width=100, height=100)
                except Exception as qr_error:
                    logger.error(f"Could not add QR code to PDF: {str(qr_error)}")
            
            p.setFont("Helvetica-Oblique", 10)
            p.drawString(100, 200, "Please bring this ticket with you to the event.")
            p.drawString(100, 180, "This ticket is personalized and non-transferrable.")
            
            p.showPage()
            p.save()
            
            buffer.seek(0)
            pdf_file = ContentFile(buffer.read())
            self.ticket_pdf.save(f"ticket-{self.id}.pdf", pdf_file, save=False)
            
            logger.info(f"Simple PDF ticket generated successfully for invitation {self.id}")
            return True
        except Exception as e:
            logger.error(f"Simple PDF generation failed: {str(e)}")
            return False