from icalendar import Calendar, Event as CalendarEvent, vCalAddress, vText
from datetime import datetime, timedelta
import pytz
from django.conf import settings
import uuid
import logging

logger = logging.getLogger(__name__)

def create_event_calendar(event, invitation=None):
    """
    Create an ICS calendar file for an event
    
    Args:
        event: Event model instance
        invitation: Optional Invitation model instance for personalized calendar
    
    Returns:
        Calendar object that can be converted to ICS format
    """
    logger.info(f"Creating calendar for event: {event.name}")
    
    cal = Calendar()
    cal.add('prodid', '-//QR Check-in System//EN')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    cal.add('method', 'REQUEST')
    
    logger.info("Basic calendar properties set")
    
    # Create calendar event
    cal_event = CalendarEvent()
    
    # Basic event info
    cal_event.add('uid', f'{event.id}-{uuid.uuid4()}@eventqr.app')
    cal_event.add('summary', event.name)
    cal_event.add('description', format_event_description(event, invitation))
    cal_event.add('location', format_location(event))
    
    # Date and time
    tz = pytz.timezone(settings.TIME_ZONE if hasattr(settings, 'TIME_ZONE') else 'UTC')
    start_datetime = datetime.combine(event.date, event.time)
    start_datetime = tz.localize(start_datetime)
    cal_event.add('dtstart', start_datetime)
    
    # Assume 2 hour duration if not specified
    end_datetime = start_datetime + timedelta(hours=2)
    cal_event.add('dtstamp', datetime.now(tz))
    cal_event.add('dtend', end_datetime)
    
    # Organizer
    if event.owner.email:
        organizer = vCalAddress(f'MAILTO:{event.owner.email}')
        organizer.params['cn'] = vText(event.owner.get_full_name() or event.owner.username)
        cal_event.add('organizer', organizer)
    
    # Attendee (if invitation provided)
    if invitation and invitation.guest_email:
        attendee = vCalAddress(f'MAILTO:{invitation.guest_email}')
        attendee.params['cn'] = vText(invitation.guest_name)
        attendee.params['role'] = vText('REQ-PARTICIPANT')
        attendee.params['partstat'] = vText('NEEDS-ACTION')
        attendee.params['rsvp'] = vText('TRUE')
        cal_event.add('attendee', attendee)
    
    # Status and classification
    cal_event.add('status', 'CONFIRMED')
    cal_event.add('class', 'PUBLIC')
    
    # Add reminder (15 minutes before)
    cal_event.add('alarm', create_reminder())
    
    cal.add_component(cal_event)
    return cal

def format_event_description(event, invitation=None):
    """Format the event description for calendar"""
    description = []
    
    if event.description:
        description.append(event.description)
        description.append('')  # Empty line
    
    # Add event type info
    if event.event_type != 'in_person':
        description.append(f'Event Type: {event.get_event_type_display()}')
        
        if event.virtual_link:
            description.append(f'Join Link: {event.virtual_link}')
        
        if event.virtual_meeting_id:
            description.append(f'Meeting ID: {event.virtual_meeting_id}')
        
        if event.virtual_passcode:
            description.append(f'Passcode: {event.virtual_passcode}')
        
        if event.virtual_platform:
            description.append(f'Platform: {event.virtual_platform}')
        
        description.append('')  # Empty line
    
    # Add ticket info if invitation provided
    if invitation:
        description.append('--- Your Ticket Information ---')
        description.append(f'Ticket ID: {invitation.id}')
        description.append(f'Name: {invitation.guest_name}')
        # Use BASE_URL setting for production flexibility
        from django.conf import settings
        base_url = getattr(settings, 'BASE_URL', 'https://eventqr.app')
        description.append(f'Check-in URL: {base_url}/tickets/{invitation.id}/')
        description.append('')
        description.append('Please bring your QR code ticket to the event.')
    
    # Add general info
    if event.max_attendees:
        description.append(f'Maximum Attendees: {event.max_attendees}')
    
    return '\n'.join(description)

def format_location(event):
    """Format the location field based on event type"""
    if event.event_type == 'virtual':
        if event.virtual_platform:
            return f'Online ({event.virtual_platform})'
        return 'Online Event'
    elif event.event_type == 'hybrid':
        return f'{event.location} (Hybrid Event)'
    else:
        return event.location

def create_reminder():
    """Create a 15-minute reminder alarm"""
    from icalendar import Alarm
    alarm = Alarm()
    alarm.add('action', 'DISPLAY')
    alarm.add('description', 'Event Reminder')
    alarm.add('trigger', timedelta(minutes=-15))
    return alarm

def generate_ics_filename(event):
    """Generate a safe filename for the ICS file"""
    safe_name = "".join(c for c in event.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_name = safe_name.replace(' ', '_')
    return f"{safe_name}.ics"