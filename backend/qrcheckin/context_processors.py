from django.utils import timezone
from events.models import Event
from invitations.models import Invitation
from attendance.models import Attendance

def admin_stats(request):
    """
    Context processor to add stats to the admin index page
    """
    if not request.path.startswith('/admin/'):
        return {}
        
    # Only calculate on the index page to avoid unnecessary DB queries
    if request.path != '/admin/':
        return {}
        
    try:
        event_count = Event.objects.count()
        upcoming_events = Event.objects.filter(date__gte=timezone.now().date()).count()
        invitation_count = Invitation.objects.count()
        checked_in_count = Attendance.objects.filter(has_attended=True).count()
        
        return {
            'event_count': event_count,
            'upcoming_events': upcoming_events,
            'invitation_count': invitation_count,
            'checked_in_count': checked_in_count,
        }
    except:
        # Return empty context if DB tables don't exist yet (e.g., during migrations)
        return {}