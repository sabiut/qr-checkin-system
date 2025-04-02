"""
Management command to send a test email using Django's email system.
Usage: python manage.py send_test_email <recipient_email>
"""

import os
import logging
from django.core.management.base import BaseCommand, CommandError
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sends a test email using Django\'s email system'
    
    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='The email address to send the test email to')
    
    def handle(self, *args, **options):
        recipient_email = options['email']
        
        # Log the current settings
        self.stdout.write(self.style.NOTICE('Email configuration:'))
        self.stdout.write(f'EMAIL_BACKEND: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'EMAIL_HOST: {settings.EMAIL_HOST}')
        self.stdout.write(f'EMAIL_PORT: {settings.EMAIL_PORT}')
        self.stdout.write(f'EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}')
        self.stdout.write(f'EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}')
        self.stdout.write(f'DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}')
        
        # Create test email content
        subject = f'QR Check-in System Test Email - {timezone.now().strftime("%Y-%m-%d %H:%M")}'
        
        text_content = f"""
        Hello,

        This is a test email from the QR Check-in System Django application.
        
        If you're seeing this, the email system is configured correctly!
        
        Sent at: {timezone.now()}
        
        Django Email Configuration:
        - Backend: {settings.EMAIL_BACKEND}
        - Host: {settings.EMAIL_HOST}
        - Port: {settings.EMAIL_PORT}
        - TLS Enabled: {settings.EMAIL_USE_TLS}
        - From Email: {settings.DEFAULT_FROM_EMAIL}
        
        This is an automated test message.
        """
        
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4f46e5; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .footer {{ text-align: center; margin-top: 30px; font-size: 0.8em; color: #666; }}
                .config {{ background-color: #f5f5f5; padding: 15px; margin: 15px 0; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>QR Check-in System</h1>
                    <h2>Test Email</h2>
                </div>
                <div class="content">
                    <p>Hello,</p>
                    <p>This is a test email from the <strong>QR Check-in System</strong> Django application.</p>
                    <p>If you're seeing this, the email system is configured correctly!</p>
                    <p>Sent at: {timezone.now()}</p>
                    
                    <div class="config">
                        <h3>Django Email Configuration:</h3>
                        <ul>
                            <li><strong>Backend:</strong> {settings.EMAIL_BACKEND}</li>
                            <li><strong>Host:</strong> {settings.EMAIL_HOST}</li>
                            <li><strong>Port:</strong> {settings.EMAIL_PORT}</li>
                            <li><strong>TLS Enabled:</strong> {settings.EMAIL_USE_TLS}</li>
                            <li><strong>From Email:</strong> {settings.DEFAULT_FROM_EMAIL}</li>
                        </ul>
                    </div>
                </div>
                <div class="footer">
                    <p>This is an automated test message from the QR Check-in System.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Create and send the email
        try:
            self.stdout.write('Preparing email...')
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email],
            )
            email.attach_alternative(html_content, "text/html")
            
            self.stdout.write('Sending email...')
            result = email.send(fail_silently=False)
            
            if result:
                self.stdout.write(self.style.SUCCESS(f'Successfully sent test email to {recipient_email}'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to send email. Result code: {result}'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error sending email: {e}'))
            logger.exception('Error in send_test_email command')
            
            # Provide troubleshooting advice based on the error
            if "Authentication" in str(e):
                self.stdout.write(self.style.WARNING("\nAuthentication failed. This could be due to:"))
                self.stdout.write("1. Incorrect username or password")
                self.stdout.write("2. Less secure app access being disabled (for Gmail)")
                self.stdout.write("3. Two-factor authentication requiring an app password")
                self.stdout.write("\nFor Gmail:")
                self.stdout.write("- Make sure you're using an app password if 2FA is enabled")
                self.stdout.write("- Check: https://myaccount.google.com/apppasswords")
            elif "SMTPSenderRefused" in str(e):
                self.stdout.write(self.style.WARNING("\nSender refused. This could be due to:"))
                self.stdout.write("1. From email address doesn't match authenticated user")
                self.stdout.write("2. Email service blocking due to spam concerns")
            elif "SMTP" in str(e):
                self.stdout.write(self.style.WARNING("\nSMTP Error. This could be due to:"))
                self.stdout.write("1. Incorrect host or port")
                self.stdout.write("2. Network connectivity issues")
                self.stdout.write("3. Firewall blocking the connection")
                
            raise CommandError('Failed to send test email') from e