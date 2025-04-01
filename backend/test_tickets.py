#!/usr/bin/env python
"""
Test script for ticket generation
Run with: python test_tickets.py
"""
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qrcheckin.settings')
django.setup()

from invitations.models import Invitation, TicketFormat
from events.models import Event
from django.contrib.auth.models import User
from django.utils import timezone
import datetime

def create_test_invitation():
    """Create a test event and invitation to test ticket generation"""
    
    # Get or create a test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'is_staff': True
        }
    )
    
    if created:
        user.set_password('testpassword')
        user.save()
        print("Created test user")
    
    # Create a test event
    event = Event.objects.create(
        owner=user,
        name='Test Event',
        description='This is a test event for ticket generation',
        date=datetime.date.today() + datetime.timedelta(days=30),
        time=timezone.now().time(),
        location='Test Location',
        max_attendees=100
    )
    print(f"Created test event: {event.name}")
    
    # Create a test invitation
    invitation = Invitation.objects.create(
        event=event,
        guest_name='Test Guest',
        guest_email='guest@example.com',
        guest_phone='555-123-4567',
        ticket_format=TicketFormat.BOTH
    )
    print(f"Created test invitation: {invitation.id}")
    
    # Verify tickets were generated
    if invitation.ticket_html:
        print(f"HTML ticket generated: {invitation.ticket_html.path}")
    else:
        print("HTML ticket was not generated")
    
    if invitation.ticket_pdf:
        print(f"PDF ticket generated: {invitation.ticket_pdf.path}")
    else:
        print("PDF ticket was not generated")
    
    return invitation

if __name__ == "__main__":
    print("Testing ticket generation...")
    invitation = create_test_invitation()
    print("Done!")