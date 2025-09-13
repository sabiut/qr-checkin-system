"""Email utilities for communication module"""
from django.core.mail import EmailMultiAlternatives, send_mass_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


def send_message_email_to_guest(invitation, sender, message_content, event):
    """
    Send an email notification to a guest who doesn't have an account yet
    when they receive a message.
    """
    try:
        subject = f"New message from {sender.get_full_name() or sender.username} - {event.name}"
        
        # Create email context
        context = {
            'guest_name': invitation.guest_name,
            'sender_name': sender.get_full_name() or sender.username,
            'event_title': event.name,
            'message_content': message_content,
            'event_date': event.date,
            'event_location': event.location,
            'registration_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/register?email={invitation.guest_email}&event={event.id}",
        }
        
        # Generate plain text message
        text_message = f"""
Hello {invitation.guest_name},

You have received a new message from {context['sender_name']} regarding the event "{event.name}".

Message:
{message_content}

To reply to this message and access all event communication features, please create your account at:
{context['registration_url']}

Event Details:
- {event.name}
- Date: {event.date}
- Location: {event.location}

Best regards,
The {event.name} Team
"""
        
        # Generate HTML message
        html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px 10px 0 0;
            text-align: center;
        }}
        .content {{
            background: white;
            padding: 30px;
            border: 1px solid #e1e1e1;
            border-radius: 0 0 10px 10px;
        }}
        .message-box {{
            background: #f7f7f7;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .cta-button {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 12px 30px;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .event-details {{
            background: #f9f9f9;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>New Message</h1>
        <p>You have a message about {event.name}</p>
    </div>
    <div class="content">
        <p>Hello {invitation.guest_name},</p>
        
        <p><strong>{context['sender_name']}</strong> has sent you a message regarding the event <strong>{event.name}</strong>:</p>
        
        <div class="message-box">
            <p>{message_content}</p>
        </div>
        
        <p>To reply to this message and access all event communication features, please create your account:</p>
        
        <center>
            <a href="{context['registration_url']}" class="cta-button">Create Account & Reply</a>
        </center>
        
        <div class="event-details">
            <h3>Event Details</h3>
            <p><strong>{event.name}</strong><br>
            📅 {event.date}<br>
            📍 {event.location}</p>
        </div>
    </div>
    <div class="footer">
        <p>This message was sent to you as an invitee of {event.name}</p>
    </div>
</body>
</html>
"""
        
        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[invitation.guest_email],
        )
        
        # Attach HTML version
        email.attach_alternative(html_message, "text/html")
        
        # Send email
        result = email.send()
        
        logger.info(f"Message email sent to guest {invitation.guest_email} for event {event.id}, result: {result}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send message email to guest {invitation.guest_email}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


def send_announcement_to_all_invitees(announcement, event):
    """
    Send announcement email to all invited guests and registered attendees for an event
    """
    from invitations.models import Invitation
    from django.contrib.auth.models import User
    from attendance.models import Attendance

    try:
        # Collect all email addresses to send to
        email_addresses = set()

        # 1. Get all invitations for this event (guests and registered users)
        invitations = Invitation.objects.filter(
            event=event,
            guest_email__isnull=False
        ).exclude(guest_email='')

        for invitation in invitations:
            email_addresses.add(invitation.guest_email)

        # 2. Include the event owner
        if event.owner and event.owner.email:
            email_addresses.add(event.owner.email)

        if not email_addresses:
            logger.info(f"No email addresses found for event {event.id}")
            return 0
        
        # Get priority label and color
        priority_colors = {
            'critical': '#dc2626',  # red
            'high': '#ea580c',      # orange
            'normal': '#2563eb',    # blue
            'low': '#6b7280',        # gray
        }
        priority_color = priority_colors.get(announcement.priority, '#2563eb')
        
        # Prepare email content
        subject = f"[{announcement.priority.upper()}] {announcement.title} - {event.name}"
        
        # Create HTML email
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px 10px 0 0;
            text-align: center;
        }}
        .priority-badge {{
            display: inline-block;
            background: {priority_color};
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
            margin-bottom: 10px;
        }}
        .content {{
            background: white;
            padding: 30px;
            border: 1px solid #e1e1e1;
            border-radius: 0 0 10px 10px;
        }}
        .announcement-box {{
            background: #f9f9f9;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid {priority_color};
        }}
        .event-details {{
            background: #f0f0f0;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="priority-badge">{announcement.priority} Priority</div>
        <h1>Event Announcement</h1>
        <p>{event.name}</p>
    </div>
    <div class="content">
        <h2>{announcement.title}</h2>
        
        <div class="announcement-box">
            <p>{announcement.content}</p>
        </div>
        
        <p><strong>From:</strong> {announcement.author.get_full_name() or announcement.author.username}<br>
        <strong>Type:</strong> {announcement.announcement_type.title()}</p>
        
        <div class="event-details">
            <h3>Event Information</h3>
            <p><strong>{event.name}</strong><br>
            📅 Date: {event.date}<br>
            ⏰ Time: {event.time}<br>
            📍 Location: {event.location}</p>
        </div>
    </div>
    <div class="footer">
        <p>You received this announcement as an invitee of {event.name}</p>
        <p>To manage your event communications, please register at:<br>
        <a href="{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/register">Create Account</a></p>
    </div>
</body>
</html>
"""
        
        # Plain text version
        text_message = f"""
{announcement.priority.upper()} PRIORITY ANNOUNCEMENT

{announcement.title}

{announcement.content}

From: {announcement.author.get_full_name() or announcement.author.username}
Type: {announcement.announcement_type.title()}

Event: {event.name}
Date: {event.date}
Time: {event.time}
Location: {event.location}

---
You received this announcement as an invitee of {event.name}.
"""
        
        # Send emails to all recipients
        sent_count = 0
        failed_count = 0

        for email_address in email_addresses:
            try:
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[email_address],
                )
                email.attach_alternative(html_template, "text/html")
                email.send()
                sent_count += 1
                logger.info(f"Announcement sent to {email_address}")
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to send announcement to {email_address}: {str(e)}")

        logger.info(f"Announcement emails sent: {sent_count} successful, {failed_count} failed")
        return sent_count
        
    except Exception as e:
        logger.error(f"Failed to send announcement emails: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return 0


def send_icebreaker_invitations(activity):
    """
    Send icebreaker activity invitations to all event invitees
    """
    from invitations.models import Invitation
    from django.contrib.auth.models import User

    try:
        event = activity.event

        # Collect all email addresses to send to
        email_addresses = set()

        # 1. Get all invitations for this event
        invitations = Invitation.objects.filter(
            event=event,
            guest_email__isnull=False
        ).exclude(guest_email='')

        for invitation in invitations:
            email_addresses.add(invitation.guest_email)

        # 2. Include the event owner
        if event.owner and event.owner.email:
            email_addresses.add(event.owner.email)

        if not email_addresses:
            logger.info(f"No email addresses found for event {event.id}")
            return 0

        # Get guest response URL
        guest_response_url = activity.get_guest_response_url()

        # Prepare email content
        subject = f"Join the Icebreaker: {activity.title} - {event.name}"

        # Create HTML email
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 30px;
            border-radius: 10px 10px 0 0;
            text-align: center;
        }}
        .content {{
            background: white;
            padding: 30px;
            border: 1px solid #e1e1e1;
            border-radius: 0 0 10px 10px;
        }}
        .activity-box {{
            background: #f0fdf4;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #10b981;
        }}
        .cta-button {{
            display: inline-block;
            background: #10b981;
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 8px;
            margin: 20px 0;
            font-weight: 600;
            text-align: center;
        }}
        .event-details {{
            background: #f9f9f9;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
        }}
        .activity-type {{
            display: inline-block;
            background: #065f46;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
            margin-bottom: 10px;
        }}
        .points-badge {{
            display: inline-block;
            background: #fbbf24;
            color: #92400e;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧊 Icebreaker Activity</h1>
        <p>Get to know your fellow attendees before {event.name}!</p>
    </div>
    <div class="content">
        <div class="activity-type">{activity.activity_type.title()}</div>
        <h2>{activity.title}</h2>

        <div class="activity-box">
            <p>{activity.description}</p>
            {f'<div class="points-badge">🏆 {activity.points_reward} points</div>' if activity.points_reward > 0 else ''}
        </div>

        <p>We've created this fun icebreaker activity to help you connect with other attendees before the event. Your participation helps make the event more engaging for everyone!</p>

        <center>
            <a href="{guest_response_url}" class="cta-button">🚀 Participate Now</a>
        </center>

        <p><small>💡 <strong>Tip:</strong> This activity only takes a few minutes and is a great way to break the ice with fellow attendees!</small></p>

        <div class="event-details">
            <h3>📅 Event Information</h3>
            <p><strong>{event.name}</strong><br>
            📅 Date: {event.date}<br>
            ⏰ Time: {event.time}<br>
            📍 Location: {event.location}</p>
        </div>
    </div>
    <div class="footer">
        <p>You received this invitation as an attendee of {event.name}</p>
        <p>Created by {activity.creator.get_full_name() or activity.creator.username}</p>
    </div>
</body>
</html>
"""

        # Plain text version
        text_message = f"""
🧊 ICEBREAKER ACTIVITY: {activity.title}

{activity.description}

We've created this fun icebreaker activity to help you connect with other attendees before {event.name}. Your participation helps make the event more engaging for everyone!

To participate, click this link:
{guest_response_url}

Activity Details:
- Type: {activity.activity_type.title()}
- Points: {activity.points_reward} (if you have an account)

Event: {event.name}
Date: {event.date}
Time: {event.time}
Location: {event.location}

Created by: {activity.creator.get_full_name() or activity.creator.username}

---
You received this invitation as an attendee of {event.name}.
This activity only takes a few minutes and is a great way to break the ice!
"""

        # Send emails to all recipients
        sent_count = 0
        failed_count = 0

        for email_address in email_addresses:
            try:
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[email_address],
                )
                email.attach_alternative(html_template, "text/html")
                email.send()
                sent_count += 1
                logger.info(f"Icebreaker invitation sent to {email_address}")
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to send icebreaker invitation to {email_address}: {str(e)}")

        logger.info(f"Icebreaker invitations sent: {sent_count} successful, {failed_count} failed")
        return sent_count

    except Exception as e:
        logger.error(f"Failed to send icebreaker invitations: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return 0