#!/usr/bin/env python
"""
Direct SMTP email test - bypasses Django completely
"""

import smtplib
import sys
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

# Load .env file
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)
print(f"Loaded .env from {dotenv_path}")

# Email settings from .env
email_host = os.environ.get('EMAIL_HOST', '')
email_port = int(os.environ.get('EMAIL_PORT', 587))
email_use_tls = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
email_host_user = os.environ.get('EMAIL_HOST_USER', '')
email_host_password = os.environ.get('EMAIL_HOST_PASSWORD', '')
default_from_email = os.environ.get('DEFAULT_FROM_EMAIL', '')

# Print settings for debugging
print("Email Settings:")
print(f"EMAIL_HOST: {email_host}")
print(f"EMAIL_PORT: {email_port}")
print(f"EMAIL_USE_TLS: {email_use_tls}")
print(f"EMAIL_HOST_USER: {email_host_user}")
print(f"EMAIL_HOST_PASSWORD: {'*****' if email_host_password else 'NOT SET'}")
print(f"DEFAULT_FROM_EMAIL: {default_from_email}")

# Get to_email from command line or use default
if len(sys.argv) > 1:
    to_email = sys.argv[1]
else:
    to_email = input("Enter recipient email address: ")

# Create message
msg = MIMEMultipart()
msg['From'] = default_from_email
msg['To'] = to_email
msg['Subject'] = f"Direct SMTP Test - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

# Add body text
body = f"""
Hello,

This is a direct SMTP test email sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.

This email bypasses Django completely and uses Python's smtplib directly.

Testing email delivery for the QR Check-in System.

Regards,
The System
"""
msg.attach(MIMEText(body, 'plain'))

# Send email
try:
    print("\nConnecting to SMTP server...")
    with smtplib.SMTP(email_host, email_port) as server:
        # Enable debug output
        server.set_debuglevel(1)
        
        # Start TLS if needed
        if email_use_tls:
            print("Starting TLS...")
            server.starttls()
        
        # Login if credentials provided
        if email_host_user and email_host_password:
            print(f"Logging in as {email_host_user}...")
            server.login(email_host_user, email_host_password)
        else:
            print("Warning: No login credentials provided")
        
        # Send the message
        print(f"Sending email to {to_email}...")
        server.send_message(msg)
        print("Email sent successfully!")
        
except Exception as e:
    print(f"\nError: {str(e)}")
    if "Authentication" in str(e):
        print("\nThis appears to be an authentication issue. Check:")
        print("1. Email and password are correct")
        print("2. For Gmail, make sure you've created an App Password if 2FA is enabled")
        print("3. Gmail may be blocking 'less secure apps' - use App Passwords")
    sys.exit(1)