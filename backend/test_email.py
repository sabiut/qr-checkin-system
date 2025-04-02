#!/usr/bin/env python

"""
Test script for email delivery
Run this script directly to test email delivery without going through Django views
"""

import os
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get email settings from environment variables
email_host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
email_port = int(os.environ.get('EMAIL_PORT', 587))
email_use_tls = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
email_host_user = os.environ.get('EMAIL_HOST_USER', '')
email_host_password = os.environ.get('EMAIL_HOST_PASSWORD', '')
default_from_email = os.environ.get('DEFAULT_FROM_EMAIL', email_host_user)

# Get test email address from command line argument
if len(sys.argv) >= 2:
    test_email = sys.argv[1]
else:
    test_email = input("Enter the email address to send a test to: ")

print(f"\nEmail Settings:")
print(f"Host: {email_host}")
print(f"Port: {email_port}")
print(f"Use TLS: {email_use_tls}")
print(f"User: {email_host_user}")
print(f"Password: {'*' * 8 if email_host_password else 'Not Set'}")
print(f"From Email: {default_from_email}")
print(f"To Email: {test_email}")

# Prepare email message
msg = MIMEMultipart('alternative')
msg['Subject'] = "Test Email from QR Check-in System"
msg['From'] = default_from_email
msg['To'] = test_email

# Plain text and HTML content
text = """
Hello,

This is a test email from the QR Check-in System.

If you're seeing this, email delivery is working correctly!

Test completed at: [timestamp]
"""

html = """
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #4f46e5; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .footer { text-align: center; margin-top: 30px; font-size: 0.8em; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Test Email</h1>
        </div>
        <div class="content">
            <p>Hello,</p>
            <p>This is a test email from the <strong>QR Check-in System</strong>.</p>
            <p>If you're seeing this, email delivery is working correctly!</p>
            <p>Test completed at: [timestamp]</p>
        </div>
        <div class="footer">
            <p>This is an automated test message from the QR Check-in System.</p>
        </div>
    </div>
</body>
</html>
"""

# Add both plain text and HTML parts
part1 = MIMEText(text, 'plain')
part2 = MIMEText(html, 'html')
msg.attach(part1)
msg.attach(part2)

try:
    # Connect to SMTP server
    print("\nConnecting to SMTP server...")
    server = smtplib.SMTP(email_host, email_port)
    server.set_debuglevel(1)  # Verbose debug output
    
    if email_use_tls:
        print("Starting TLS...")
        server.starttls()
    
    if email_host_user and email_host_password:
        print("Logging in...")
        server.login(email_host_user, email_host_password)
    
    # Send email
    print("Sending email...")
    server.sendmail(default_from_email, test_email, msg.as_string())
    server.quit()
    
    print("\nEmail sent successfully!")
except Exception as e:
    print(f"\nError sending email: {str(e)}")
    
    # Provide more detailed troubleshooting information
    if "Authentication" in str(e):
        print("\nAuthentication failed. This could be due to:")
        print("1. Incorrect username or password")
        print("2. Less secure app access being disabled (for Gmail)")
        print("3. Two-factor authentication requiring an app password")
        print("\nFor Gmail:")
        print("- Make sure you're using an app password if 2FA is enabled")
        print("- Check: https://myaccount.google.com/apppasswords")
    elif "SMTPSenderRefused" in str(e):
        print("\nSender refused. This could be due to:")
        print("1. From email address doesn't match authenticated user")
        print("2. Email service blocking due to spam concerns")
    elif "SMTP" in str(e):
        print("\nSMTP Error. This could be due to:")
        print("1. Incorrect host or port")
        print("2. Network connectivity issues")
        print("3. Firewall blocking the connection")
    
    sys.exit(1)