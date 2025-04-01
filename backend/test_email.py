#!/usr/bin/env python
"""
Test script for sending emails
Run with: python test_email.py
"""
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qrcheckin.settings')
django.setup()

from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_email_sending():
    """Test sending an email using Django's email system"""
    logger.info("Testing email sending with these settings:")
    logger.info(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    logger.info(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    logger.info(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    logger.info(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    logger.info(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    logger.info(f"EMAIL_HOST_PASSWORD: {'*' * len(settings.EMAIL_HOST_PASSWORD) if settings.EMAIL_HOST_PASSWORD else 'Not set'}")
    logger.info(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    # Prompt for test email address
    test_email = input("Enter a test email address: ")
    
    # Simple text email
    subject = "Test Email from QR Check-in System"
    text_content = "This is a test email from the QR Check-in System."
    html_content = "<h1>Test Email</h1><p>This is a test email from the QR Check-in System.</p>"
    
    try:
        logger.info(f"Attempting to send email to {test_email}")
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[test_email]
        )
        email.attach_alternative(html_content, "text/html")
        
        # Send the email
        result = email.send()
        logger.info(f"Email send result: {result}")
        
        print(f"\nEmail sent to {test_email}. Check your inbox!")
        print("If you used console backend, check the console output for the email content.")
        
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        print(f"\nError sending email: {str(e)}")

if __name__ == "__main__":
    print("Testing email sending...")
    test_email_sending()
    print("Done!")