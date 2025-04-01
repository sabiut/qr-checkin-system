from django.db import models
import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image, ImageDraw
# Import weasyprint conditionally to avoid errors when it's not installed
try:
    import weasyprint
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
import logging

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
        """Generate QR code for this invitation"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(str(self.id))
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        self.qr_code.save(f"qrcode-{self.id}.png", File(buffer), save=False)
        buffer.close()
        
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
            self.generate_pdf_ticket()
            
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
            
            # Always make QR code URL absolute
            if self.qr_code:
                qr_code_url = self.qr_code.url
                # Always make it absolute to ensure it works in all contexts
                if qr_code_url.startswith('/'):
                    qr_code_url = f"{base_url}{qr_code_url}"
            else:
                qr_code_url = None
                
            logger.info(f"QR code URL for invitation {self.id}: {qr_code_url}")
                
            try:
                # Render HTML ticket from template
                context = {
                    'invitation': self,
                    'event': self.event,
                    'qr_code_url': qr_code_url,
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
                html_content = self._generate_simple_html_ticket(qr_code_url)
            
            # Save the HTML ticket
            logger.info(f"Saving HTML ticket for invitation {self.id}")
            html_file = ContentFile(html_content.encode('utf-8'))
            self.ticket_html.save(f"ticket-{self.id}.html", html_file, save=False)
            logger.info(f"HTML ticket saved for invitation {self.id}")
        except Exception as e:
            # Log the error but don't prevent the invite from being created
            logger.error(f"Error generating HTML ticket for invitation {self.id}: {str(e)}")
            # Don't re-raise the exception - allow the invitation to be created
    
    def _generate_simple_html_ticket(self, qr_code_url):
        """Generate a simple HTML ticket as fallback when template rendering fails"""
        event = self.event
        
        # Very simple HTML, no external dependencies
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Event Ticket - {event.name}</title>
    <style>
        body {{ font-family: sans-serif; margin: 0; padding: 20px; }}
        h1, h2, h3 {{ margin-top: 0; }}
        .ticket {{ border: 1px solid #ccc; padding: 20px; max-width: 600px; margin: 0 auto; }}
        .header {{ background: #4f46e5; color: white; padding: 10px; text-align: center; }}
        .section {{ margin-bottom: 20px; }}
        .footer {{ text-align: center; font-size: 0.8em; color: #666; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="ticket">
        <div class="header">
            <h1>{event.name}</h1>
            <h2>Admission Ticket</h2>
        </div>
        
        <div class="section">
            <h3>Guest Information</h3>
            <p><strong>Name:</strong> {self.guest_name}</p>
            {f'<p><strong>Email:</strong> {self.guest_email}</p>' if self.guest_email else ''}
            {f'<p><strong>Phone:</strong> {self.guest_phone}</p>' if self.guest_phone else ''}
        </div>
        
        <div class="section">
            <h3>Event Details</h3>
            <p><strong>Event Name:</strong> {event.name}</p>
            <p><strong>Date:</strong> {event.date}</p>
            <p><strong>Time:</strong> {event.time}</p>
            <p><strong>Location:</strong> {event.location}</p>
            {f'<p><strong>Description:</strong> {event.description}</p>' if event.description else ''}
        </div>
        
        <div class="section" style="text-align: center;">
            <h3>Check-in Code</h3>
            {f'<img src="{qr_code_url}" alt="Check-in QR Code" style="max-width: 200px;">' if qr_code_url else '<p>(QR code not available)</p>'}
            <p>Please present this QR code when you arrive at the event.</p>
        </div>
        
        <div style="font-size: 0.8em; text-align: right;">
            Ticket ID: {self.id}
        </div>
        
        <div class="footer">
            <p>This ticket is personalized and non-transferrable.</p>
            <p>Generated by QR Check-in System.</p>
        </div>
    </div>
</body>
</html>"""
        return html
        
    def generate_pdf_ticket(self):
        """Generate a PDF ticket from the HTML ticket"""
        try:
            # Skip if WeasyPrint isn't available
            if not WEASYPRINT_AVAILABLE:
                logger.warning("WeasyPrint not available, skipping PDF ticket generation")
                return
                
            if not self.ticket_html:
                self.generate_html_ticket()
                
            if not self.ticket_html:
                return
                
            # Use WeasyPrint to convert HTML to PDF
            try:
                # We need the HTML content
                with self.ticket_html.open('r') as f:
                    # Read as string without decoding
                    html_content = f.read()
                    
                    # If it's bytes, decode it; if it's already a string, use it directly
                    if isinstance(html_content, bytes):
                        html_content = html_content.decode('utf-8')
                    
                # Create PDF
                # Fix base URL for images
                base_url = os.path.dirname(self.ticket_html.path)
                pdf = weasyprint.HTML(string=html_content, base_url=base_url).write_pdf()
                
                # Save the PDF ticket
                pdf_file = ContentFile(pdf)
                self.ticket_pdf.save(f"ticket-{self.id}.pdf", pdf_file, save=False)
                
                logger.info(f"PDF ticket generated successfully for invitation {self.id}")
            except Exception as inner_e:
                logger.error(f"Error processing HTML to PDF: {str(inner_e)}")
                
                # Alternative approach: generate a simpler PDF directly
                try:
                    logger.info("Trying alternative PDF generation approach")
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
                    self.ticket_pdf.save(f"ticket-simple-{self.id}.pdf", pdf_file, save=False)
                    
                    logger.info(f"Alternative PDF ticket generated successfully for invitation {self.id}")
                except Exception as alt_e:
                    logger.error(f"Alternative PDF generation also failed: {str(alt_e)}")
                    raise
                
        except Exception as e:
            # Log the error but don't prevent the invite from being created
            logger.error(f"Error generating PDF ticket: {str(e)}")
            # Don't re-raise the exception - allow the invitation to be created