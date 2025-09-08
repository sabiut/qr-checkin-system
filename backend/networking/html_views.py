from django.http import HttpResponse, HttpRequest
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils.html import escape
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.middleware.csrf import get_token
from django.core.exceptions import ValidationError
from django.db import transaction
from django.core.paginator import Paginator
from typing import Union
from .models import NetworkingProfile, Connection, EventNetworkingSettings, ConnectionStatus, ConnectionMethod
from .services import NetworkingQRService
from events.models import Event
import json
import logging

logger = logging.getLogger(__name__)


def check_existing_connection(user1: User, user2: User, event: Event) -> Union[Connection, None]:
    """
    Check if a connection already exists between two users for an event.
    Returns the existing connection or None.
    """
    from django.db.models import Q
    
    return Connection.objects.filter(
        Q(from_user=user1, to_user=user2) |
        Q(from_user=user2, to_user=user1),
        event=event
    ).first()


def create_bidirectional_connection(from_user: User, to_user: User, event: Event, method: str = ConnectionMethod.QR_SCAN) -> tuple:
    """
    Create a bidirectional connection between two users for an event.
    Returns tuple of (primary_connection, reverse_connection).
    
    Args:
        from_user: User initiating the connection
        to_user: User being connected to
        event: Event where connection is made
        method: Connection method (qr_scan, directory, manual, etc.)
    
    Returns:
        Tuple of (primary_connection, reverse_connection)
    
    Raises:
        Exception: If connection creation fails
    """
    with transaction.atomic():
        # Create primary connection
        connection = Connection.objects.create(
            from_user=from_user,
            to_user=to_user,
            event=event,
            connection_method=method,
            status=ConnectionStatus.ACCEPTED
        )
        logger.info(f"Primary connection created: {connection.id} ({from_user.username} → {to_user.username})")
        
        # Create reciprocal connection
        reverse_connection, created = connection.create_reverse_connection()
        if created:
            logger.info(f"Reciprocal connection created: {reverse_connection.id} ({to_user.username} → {from_user.username})")
        else:
            logger.info(f"Reciprocal connection already exists: {reverse_connection.id}")
        
        # Award gamification points if available
        try:
            from gamification.services import GamificationService
            gamification_service = GamificationService()
            gamification_service.award_points(from_user, 'networking_connection', event=event)
            gamification_service.award_points(to_user, 'networking_connection', event=event)
            logger.info(f"Networking points awarded to {from_user.username} and {to_user.username}")
        except ImportError:
            logger.debug("Gamification not available - skipping points")
        except Exception as e:
            logger.warning(f"Could not award gamification points: {str(e)}")
            # Don't raise - connection creation should still succeed
        
        return connection, reverse_connection


def validate_event_access(user: User, event: Event) -> tuple[bool, str]:
    """
    Validate if user has access to event networking features.
    Returns (is_valid, error_message) tuple.
    
    Enhanced security checks:
    - Validates user authentication
    - Checks event invitation status
    - Verifies RSVP status
    - Checks if networking is enabled for the event
    """
    # Basic authentication check
    if not user.is_authenticated:
        return False, "Authentication required"
    
    # Check if event exists and is active
    if not event:
        return False, "Event not found"
    
    try:
        from invitations.models import Invitation
        # Find invitation by matching guest_email with user's email
        # Use select_related to avoid additional queries
        invitation = Invitation.objects.select_related('event').get(
            guest_email=user.email, 
            event=event
        )
        
        # Check RSVP status - only allow PENDING and ATTENDING
        if invitation.rsvp_status == 'DECLINED':
            return False, "Access denied: You have declined this event invitation"
        
        # Validate that networking is enabled for this event
        try:
            networking_settings = event.networking_settings
            if not networking_settings.enable_networking:
                return False, "Networking is disabled for this event"
        except EventNetworkingSettings.DoesNotExist:
            # Default to allowing networking if no settings exist
            pass
        
        return True, ""
        
    except Invitation.DoesNotExist:
        # Log security attempt for monitoring
        logger.warning(f"Unauthorized access attempt: user {user.id} ({user.email}) tried to access event {event.id}")
        return False, "Access denied: You must be invited to this event"
    
    except Exception as e:
        # Log unexpected errors for debugging
        logger.error(f"Error validating event access for user {user.id} and event {event.id}: {str(e)}")
        return False, "Access validation failed"


def build_connection_html(connections, event: Event, current_user: User) -> str:
    """
    Build HTML for displaying connections.
    Extracted for better code organization and reusability.
    """
    if not connections:
        return f'''
        <div class="empty-state">
            <div class="empty-icon">🤝</div>
            <h3>No connections yet</h3>
            <p>Start networking by scanning QR codes or browsing the attendee directory!</p>
            <div class="empty-actions">
                <a href="/networking/directory/{event.id}/" class="btn-primary">Browse Attendees</a>
                <a href="/networking/qr-code/{current_user.id}/{event.id}/" class="btn-secondary">Show My QR Code</a>
            </div>
        </div>
        '''
    
    connections_html = ""
    for conn in connections:
        # Determine which user is the "other" user (not current_user)
        if conn.from_user == current_user:
            connected_user = conn.to_user
        else:
            connected_user = conn.from_user
            
        profile = getattr(connected_user, 'networking_profile', None)
        
        # Get user info
        full_name = connected_user.get_full_name() or connected_user.username
        company = profile.company if profile else ""
        bio = profile.bio if profile else ""
        connection_method = dict(Connection.CONNECTION_METHODS).get(conn.connection_method, conn.connection_method)
        
        connections_html += f'''
        <div class="connection-card">
            <div class="connection-avatar">
                {escape(full_name[0].upper() if full_name else "U")}
            </div>
            <div class="connection-content">
                <div class="connection-header">
                    <div class="connection-name">{escape(full_name)}</div>
                    <div class="connection-method">{escape(connection_method)}</div>
                </div>
                {f'<div class="connection-company">{escape(company)}</div>' if company else ''}
                {f'<div class="connection-bio">{escape(bio[:100] + ("..." if len(bio) > 100 else ""))}</div>' if bio else ''}
                <div class="connection-date">Connected {conn.connected_at.strftime("%B %d, %Y at %I:%M %p")}</div>
            </div>
            <div class="connection-actions">
                <a href="/networking/profile/{connected_user.id}/{event.id}/" class="btn-secondary">View Profile</a>
            </div>
        </div>
        '''
    
    return connections_html


def networking_qr_page(request: HttpRequest, user_id: int, event_id: int) -> HttpResponse:
    """User-friendly QR code page - No auth required for viewing QR codes"""
    try:
        user = get_object_or_404(User, id=user_id)
        event = get_object_or_404(Event, id=event_id)
        
        # Get or create networking profile
        profile, created = NetworkingProfile.objects.get_or_create(
            user=user,
            defaults={
                'company': '',
                'visible_in_directory': True,
                'allow_contact_sharing': True
            }
        )
        
        # Generate QR code
        qr_code = NetworkingQRService.generate_networking_qr(user, event, format='png')
        
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>My Networking QR Code - {event.name}</title>
            <style>
                body {{
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
                    min-height: 100vh;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 20px;
                    padding: 40px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.1);
                    text-align: center;
                }}
                .header {{
                    margin-bottom: 30px;
                }}
                .title {{
                    font-size: 28px;
                    font-weight: 700;
                    color: #1e293b;
                    margin-bottom: 10px;
                }}
                .subtitle {{
                    color: #64748b;
                    font-size: 16px;
                }}
                .qr-container {{
                    background: #f8fafc;
                    border-radius: 16px;
                    padding: 30px;
                    margin: 30px 0;
                }}
                .qr-code {{
                    max-width: 250px;
                    width: 100%;
                    height: auto;
                    margin: 0 auto;
                    display: block;
                    border-radius: 8px;
                }}
                .instructions {{
                    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                    border-radius: 12px;
                    padding: 25px;
                    margin: 25px 0;
                    text-align: left;
                }}
                .instructions h3 {{
                    margin: 0 0 15px 0;
                    color: #0ea5e9;
                    font-size: 18px;
                }}
                .instructions ul {{
                    margin: 0;
                    padding-left: 20px;
                    color: #475569;
                }}
                .instructions li {{
                    margin: 8px 0;
                }}
                .user-info {{
                    background: #f1f5f9;
                    border-radius: 12px;
                    padding: 20px;
                    margin: 25px 0;
                }}
                .user-name {{
                    font-size: 20px;
                    font-weight: 600;
                    color: #1e293b;
                    margin-bottom: 8px;
                }}
                .user-details {{
                    color: #64748b;
                    font-size: 14px;
                }}
                .actions {{
                    display: flex;
                    gap: 15px;
                    justify-content: center;
                    flex-wrap: wrap;
                    margin-top: 30px;
                }}
                .btn {{
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    padding: 12px 24px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: 600;
                    font-size: 14px;
                    transition: all 0.3s ease;
                }}
                .btn-primary {{
                    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
                    color: white;
                }}
                .btn-secondary {{
                    background: #f1f5f9;
                    color: #475569;
                    border: 1px solid #e2e8f0;
                }}
                .btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(0,0,0,0.15);
                }}
                @media (max-width: 640px) {{
                    body {{ padding: 10px; }}
                    .container {{ padding: 25px 20px; }}
                    .actions {{ flex-direction: column; align-items: stretch; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="title">📱 My Networking QR Code</div>
                    <div class="subtitle">Share this code to connect instantly</div>
                </div>
                
                <div class="user-info">
                    <div class="user-name">{user.get_full_name() or user.username}</div>
                    <div class="user-details">
                        {f"{profile.company}" if profile.company else ""}
                        {f" • {profile.job_title}" if profile.job_title else ""}
                        <br>Event: {event.name}
                    </div>
                </div>
                
                <div class="qr-container">
                    <img src="{qr_code}" alt="Networking QR Code" class="qr-code">
                    <p style="margin: 15px 0 0 0; color: #64748b; font-size: 14px;">
                        Show this QR code to other attendees to connect instantly
                    </p>
                </div>
                
                <div class="instructions">
                    <h3>🤝 How to Network:</h3>
                    <ul>
                        <li><strong>Show your QR code</strong> to people you meet</li>
                        <li><strong>Scan others' codes</strong> with your phone camera</li>
                        <li><strong>Instant connection</strong> - no typing needed!</li>
                        <li><strong>Earn points</strong> for each new connection (+5 pts)</li>
                        <li><strong>Export contacts</strong> after the event</li>
                    </ul>
                </div>
                
                <div class="actions">
                    <a href="javascript:window.print()" class="btn btn-primary">
                        <span>🖨️</span> Print QR Code
                    </a>
                    <a href="/networking/directory/{event.id}/" class="btn btn-secondary">
                        <span>👥</span> Browse Attendees
                    </a>
                    <a href="/networking/connections/{event.id}/" class="btn btn-secondary">
                        <span>🔗</span> My Connections
                    </a>
                </div>
            </div>
        </body>
        </html>
        '''
        
        return HttpResponse(html)
        
    except Exception as e:
        return HttpResponse(f"Error generating QR code: {str(e)}", status=500)


def networking_directory_page(request: HttpRequest, event_id: int) -> HttpResponse:
    """User-friendly attendee directory page - No auth required for browsing"""
    try:
        event = get_object_or_404(Event, id=event_id)
        
        # Check networking settings
        try:
            settings = event.networking_settings
            if not settings.enable_attendee_directory:
                return HttpResponse("Attendee directory is not enabled for this event.", status=403)
        except:
            return HttpResponse("Networking not configured for this event.", status=404)
        
        # Get attendees with networking profiles - optimized query
        from .models import NetworkingProfile
        profiles = NetworkingProfile.objects.filter(
            visible_in_directory=True
        ).select_related('user').distinct()[:20]  # Limit to 20 for demo
        
        attendees_html = ""
        for profile in profiles:
            user = profile.user
            interests_str = ", ".join(profile.interests[:3]) if profile.interests else "No interests listed"
            
            # Generate avatar initials with HTML escaping
            name = escape(user.get_full_name() or user.username)
            initials = ''.join([word[0].upper() for word in name.split()[:2]]) if name else "?"
            
            # Escape all user-provided content
            safe_company = escape(profile.company or "Company not specified")
            safe_job_title = escape(profile.job_title or "Attendee") 
            safe_bio = escape(profile.bio[:100] + "..." if len(profile.bio) > 100 else profile.bio or "No bio available")
            safe_interests = escape(interests_str)
            
            # Dynamic colors based on name hash
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9']
            color = colors[hash(name) % len(colors)]
            
            attendees_html += f'''
            <div class="attendee-card" data-name="{escape(name.lower())}" data-company="{escape((profile.company or '').lower())}" data-title="{escape((profile.job_title or '').lower())}" data-interests="{escape(interests_str.lower())}">
                <div class="attendee-avatar" style="background: {color};">
                    <span class="avatar-initials">{initials}</span>
                    <div class="online-indicator"></div>
                </div>
                <div class="attendee-content">
                    <div class="attendee-header">
                        <div class="attendee-name">{name}</div>
                        <div class="attendee-title">{safe_job_title}</div>
                    </div>
                    <div class="attendee-company">
                        <span class="company-icon">🏢</span>
                        {safe_company}
                    </div>
                    <div class="attendee-bio">{safe_bio}</div>
                    <div class="attendee-interests">
                        <span class="interests-icon">⭐</span>
                        <strong>Interests:</strong> {safe_interests}
                    </div>
                    <div class="attendee-actions">
                        <button class="btn btn-connect" onclick="connectWith('{user.id}', '{name}')">
                            <span class="btn-icon">🤝</span>
                            <span>Connect</span>
                            <span class="btn-hover-text">Let's network!</span>
                        </button>
                        <button class="btn btn-secondary" onclick="viewProfile('{user.id}')">
                            <span class="btn-icon">👤</span>
                            <span>Profile</span>
                        </button>
                    </div>
                </div>
            </div>
            '''
        
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Attendee Directory - {event.name}</title>
            <style>
                body {{
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
                    min-height: 100vh;
                }}
                .container {{
                    max-width: 900px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 20px;
                    padding: 40px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 40px;
                }}
                .title {{
                    font-size: 28px;
                    font-weight: 700;
                    color: #1e293b;
                    margin-bottom: 10px;
                }}
                .subtitle {{
                    color: #64748b;
                    font-size: 16px;
                }}
                .stats {{
                    display: flex;
                    justify-content: center;
                    gap: 30px;
                    margin: 30px 0;
                    padding: 25px;
                    background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
                    border-radius: 16px;
                    border: 1px solid #10b981;
                }}
                .stat-item {{
                    text-align: center;
                }}
                .stat-number {{
                    font-size: 24px;
                    font-weight: 700;
                    color: #059669;
                    margin-bottom: 5px;
                }}
                .stat-label {{
                    font-size: 12px;
                    color: #64748b;
                    text-transform: uppercase;
                    font-weight: 500;
                }}
                .search-section {{
                    margin: 30px 0;
                    text-align: center;
                }}
                .search-input {{
                    width: 100%;
                    max-width: 500px;
                    padding: 15px 20px;
                    border: 2px solid #e2e8f0;
                    border-radius: 50px;
                    font-size: 16px;
                    background: #f8fafc;
                    transition: all 0.3s ease;
                }}
                .search-input:focus {{
                    outline: none;
                    border-color: #10b981;
                    box-shadow: 0 0 0 3px rgba(16,185,129,0.1);
                }}
                .filter-buttons {{
                    display: flex;
                    justify-content: center;
                    gap: 10px;
                    margin-top: 15px;
                    flex-wrap: wrap;
                }}
                .filter-btn {{
                    padding: 8px 16px;
                    border: 2px solid #e2e8f0;
                    border-radius: 25px;
                    background: white;
                    color: #64748b;
                    font-size: 13px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.3s ease;
                }}
                .filter-btn:hover, .filter-btn.active {{
                    background: #10b981;
                    color: white;
                    border-color: #10b981;
                }}
                .attendees-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
                    gap: 25px;
                    margin: 30px 0;
                }}
                .attendee-card {{
                    background: white;
                    border-radius: 16px;
                    padding: 0;
                    border: 2px solid #f1f5f9;
                    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                    overflow: hidden;
                    position: relative;
                    display: flex;
                    flex-direction: column;
                }}
                .attendee-card:hover {{
                    transform: translateY(-8px) scale(1.02);
                    box-shadow: 0 20px 40px rgba(16,185,129,0.15);
                    border-color: #10b981;
                }}
                .attendee-card::before {{
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    height: 4px;
                    background: linear-gradient(90deg, #10b981, #059669);
                    transform: scaleX(0);
                    transition: transform 0.3s ease;
                }}
                .attendee-card:hover::before {{
                    transform: scaleX(1);
                }}
                .attendee-avatar {{
                    width: 70px;
                    height: 70px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 20px 20px 0 20px;
                    position: relative;
                    box-shadow: 0 8px 16px rgba(0,0,0,0.1);
                }}
                .avatar-initials {{
                    color: white;
                    font-size: 24px;
                    font-weight: 700;
                    text-shadow: 0 1px 2px rgba(0,0,0,0.1);
                }}
                .online-indicator {{
                    position: absolute;
                    bottom: 5px;
                    right: 5px;
                    width: 16px;
                    height: 16px;
                    background: #22c55e;
                    border: 3px solid white;
                    border-radius: 50%;
                    animation: pulse 2s infinite;
                }}
                @keyframes pulse {{
                    0%, 100% {{ opacity: 1; }}
                    50% {{ opacity: 0.5; }}
                }}
                .attendee-content {{
                    padding: 0 20px 20px 20px;
                    flex-grow: 1;
                    display: flex;
                    flex-direction: column;
                }}
                .attendee-header {{
                    margin-bottom: 15px;
                }}
                .attendee-name {{
                    font-size: 20px;
                    font-weight: 700;
                    color: #1e293b;
                    margin-bottom: 5px;
                    line-height: 1.2;
                }}
                .attendee-title {{
                    color: #10b981;
                    font-weight: 600;
                    font-size: 14px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                .attendee-company {{
                    color: #475569;
                    font-size: 15px;
                    margin: 15px 0 10px 0;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }}
                .company-icon, .interests-icon {{
                    font-size: 16px;
                }}
                .attendee-bio {{
                    color: #64748b;
                    font-size: 14px;
                    line-height: 1.5;
                    margin-bottom: 15px;
                    font-style: italic;
                }}
                .attendee-interests {{
                    color: #64748b;
                    font-size: 13px;
                    margin-bottom: 20px;
                    display: flex;
                    align-items: flex-start;
                    gap: 8px;
                    line-height: 1.4;
                }}
                .attendee-actions {{
                    display: flex;
                    gap: 10px;
                    margin-top: auto;
                }}
                .btn {{
                    position: relative;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    gap: 8px;
                    padding: 12px 18px;
                    border-radius: 12px;
                    text-decoration: none;
                    font-weight: 600;
                    font-size: 14px;
                    transition: all 0.3s ease;
                    border: none;
                    cursor: pointer;
                    overflow: hidden;
                    flex: 1;
                }}
                .btn-connect {{
                    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                    color: white;
                    box-shadow: 0 4px 12px rgba(16,185,129,0.3);
                }}
                .btn-connect:hover {{
                    background: linear-gradient(135deg, #059669 0%, #047857 100%);
                    box-shadow: 0 6px 20px rgba(16,185,129,0.4);
                }}
                .btn-secondary {{
                    background: #f8fafc;
                    color: #475569;
                    border: 2px solid #e2e8f0;
                }}
                .btn-secondary:hover {{
                    background: #f1f5f9;
                    border-color: #cbd5e1;
                }}
                .btn-icon {{
                    font-size: 16px;
                }}
                .btn-hover-text {{
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    opacity: 0;
                    font-size: 12px;
                    font-weight: 500;
                    transition: opacity 0.3s ease;
                }}
                .btn-connect:hover .btn-hover-text {{
                    opacity: 1;
                }}
                .btn-connect:hover span:not(.btn-hover-text) {{
                    opacity: 0;
                }}
                .no-results {{
                    text-align: center;
                    padding: 60px 20px;
                    color: #64748b;
                }}
                .no-results-icon {{
                    font-size: 48px;
                    margin-bottom: 16px;
                    opacity: 0.5;
                }}
                .no-results-text {{
                    font-size: 18px;
                    font-weight: 600;
                    margin-bottom: 8px;
                }}
                .no-results-subtext {{
                    font-size: 14px;
                    opacity: 0.8;
                }}
                .btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(0,0,0,0.15);
                }}
                .back-btn {{
                    background: #f1f5f9;
                    color: #475569;
                    border: 1px solid #e2e8f0;
                    margin: 20px auto;
                    display: inline-flex;
                }}
                @media (max-width: 768px) {{
                    body {{ padding: 10px; }}
                    .container {{ padding: 25px 20px; }}
                    .attendees-grid {{ 
                        grid-template-columns: 1fr; 
                        gap: 20px;
                    }}
                    .stats {{ 
                        flex-direction: column; 
                        gap: 15px; 
                    }}
                    .search-input {{
                        font-size: 14px;
                        padding: 12px 18px;
                    }}
                    .filter-buttons {{
                        gap: 8px;
                    }}
                    .filter-btn {{
                        font-size: 12px;
                        padding: 6px 12px;
                    }}
                    .attendee-card {{
                        transform: none !important;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
                    }}
                    .attendee-actions {{
                        flex-direction: column;
                        gap: 8px;
                    }}
                    .btn {{
                        padding: 10px 16px;
                        font-size: 13px;
                    }}
                    .attendee-avatar {{
                        width: 60px;
                        height: 60px;
                        margin: 15px 15px 0 15px;
                    }}
                    .avatar-initials {{
                        font-size: 20px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="title">👥 Attendee Directory</div>
                    <div class="subtitle">Connect with fellow attendees at {event.name}</div>
                </div>
                
                <div class="stats">
                    <div class="stat-item">
                        <div class="stat-number" id="attendee-count">{profiles.count()}</div>
                        <div class="stat-label">Attendees</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">{len(set(p.industry for p in profiles if p.industry))}</div>
                        <div class="stat-label">Industries</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">{len(set(p.company for p in profiles if p.company))}</div>
                        <div class="stat-label">Companies</div>
                    </div>
                </div>
                
                <div class="search-section">
                    <input 
                        type="text" 
                        class="search-input" 
                        placeholder="🔍 Search attendees by name, company, title, or interests..." 
                        id="searchInput"
                        onkeyup="filterAttendees()"
                    >
                    <div class="filter-buttons">
                        <button class="filter-btn active" onclick="filterByCategory('all')">All</button>
                        <button class="filter-btn" onclick="filterByCategory('company')">By Company</button>
                        <button class="filter-btn" onclick="filterByCategory('title')">By Title</button>
                        <button class="filter-btn" onclick="filterByCategory('interests')">By Interests</button>
                    </div>
                </div>
                
                <div class="attendees-grid" id="attendeesGrid">
                    {attendees_html}
                </div>
                
                <div class="no-results" id="noResults" style="display: none;">
                    <div class="no-results-icon">🔍</div>
                    <div class="no-results-text">No attendees found</div>
                    <div class="no-results-subtext">Try adjusting your search terms or filters</div>
                </div>
                
                <div style="text-align: center; margin-top: 40px;">
                    <a href="javascript:history.back()" class="btn back-btn">
                        <span>←</span> Back to Ticket
                    </a>
                </div>
            </div>
            
            <script>
            let currentFilter = 'all';
            
            function connectWith(userId, userName) {{
                // Create a more engaging connection popup
                const popup = document.createElement('div');
                popup.style.cssText = `
                    position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
                    background: white; padding: 30px; border-radius: 16px; box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    z-index: 1000; text-align: center; max-width: 400px; width: 90%;
                `;
                popup.innerHTML = `
                    <div style="font-size: 48px; margin-bottom: 16px;">🤝</div>
                    <h3 style="margin: 0 0 12px 0; color: #1e293b;">Connect with ${{userName}}!</h3>
                    <p style="color: #64748b; margin-bottom: 24px; line-height: 1.4;">
                        Connection feature is coming soon! For now, find ${{userName}} at the event and scan their QR code to connect instantly.
                    </p>
                    <button onclick="closePopup()" style="
                        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                        color: white; border: none; padding: 12px 24px; border-radius: 8px;
                        font-weight: 600; cursor: pointer; transition: all 0.3s ease;
                    ">Got it! 👍</button>
                `;
                
                const overlay = document.createElement('div');
                overlay.style.cssText = `
                    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
                    background: rgba(0,0,0,0.5); z-index: 999;
                `;
                overlay.onclick = closePopup;
                
                document.body.appendChild(overlay);
                document.body.appendChild(popup);
                
                window.closePopup = function() {{
                    document.body.removeChild(popup);
                    document.body.removeChild(overlay);
                    delete window.closePopup;
                }};
            }}
            
            function viewProfile(userId) {{
                alert('Profile viewing feature coming soon!');
            }}
            
            function filterAttendees() {{
                const searchTerm = document.getElementById('searchInput').value.toLowerCase();
                const cards = document.querySelectorAll('.attendee-card');
                let visibleCount = 0;
                
                cards.forEach(card => {{
                    const name = card.dataset.name || '';
                    const company = card.dataset.company || '';
                    const title = card.dataset.title || '';
                    const interests = card.dataset.interests || '';
                    
                    let shouldShow = false;
                    
                    if (currentFilter === 'all') {{
                        shouldShow = name.includes(searchTerm) || 
                                   company.includes(searchTerm) || 
                                   title.includes(searchTerm) || 
                                   interests.includes(searchTerm);
                    }} else if (currentFilter === 'company') {{
                        shouldShow = company.includes(searchTerm);
                    }} else if (currentFilter === 'title') {{
                        shouldShow = title.includes(searchTerm);
                    }} else if (currentFilter === 'interests') {{
                        shouldShow = interests.includes(searchTerm);
                    }}
                    
                    if (shouldShow) {{
                        card.style.display = 'flex';
                        visibleCount++;
                    }} else {{
                        card.style.display = 'none';
                    }}
                }});
                
                // Update attendee count
                document.getElementById('attendee-count').textContent = visibleCount;
                
                // Show/hide no results message
                const noResults = document.getElementById('noResults');
                const attendeesGrid = document.getElementById('attendeesGrid');
                
                if (visibleCount === 0) {{
                    noResults.style.display = 'block';
                    attendeesGrid.style.display = 'none';
                }} else {{
                    noResults.style.display = 'none';
                    attendeesGrid.style.display = 'grid';
                }}
            }}
            
            function filterByCategory(category) {{
                currentFilter = category;
                
                // Update active button
                document.querySelectorAll('.filter-btn').forEach(btn => {{
                    btn.classList.remove('active');
                }});
                event.target.classList.add('active');
                
                // Update search placeholder
                const searchInput = document.getElementById('searchInput');
                const placeholders = {{
                    'all': '🔍 Search attendees by name, company, title, or interests...',
                    'company': '🏢 Search by company name...',
                    'title': '💼 Search by job title...',
                    'interests': '⭐ Search by interests...'
                }};
                searchInput.placeholder = placeholders[category];
                
                // Re-filter with current search term
                filterAttendees();
            }}
            
            // Add some nice entrance animations
            window.addEventListener('load', function() {{
                const cards = document.querySelectorAll('.attendee-card');
                cards.forEach((card, index) => {{
                    card.style.opacity = '0';
                    card.style.transform = 'translateY(20px)';
                    setTimeout(() => {{
                        card.style.transition = 'all 0.6s ease';
                        card.style.opacity = '1';
                        card.style.transform = 'translateY(0)';
                    }}, index * 100);
                }});
            }});
            </script>
        </body>
        </html>
        '''
        
        return HttpResponse(html)
        
    except Exception as e:
        return HttpResponse(f"Error loading directory: {str(e)}", status=500)


@login_required
def networking_connections_page(request: HttpRequest, event_id: int) -> HttpResponse:
    """User-friendly connections management page showing real connections"""
    try:
        # Validate event_id parameter
        try:
            event_id = int(event_id)
        except (ValueError, TypeError):
            return HttpResponse("Invalid event ID", status=400)
            
        event = get_object_or_404(Event, id=event_id)
        current_user = request.user
        
        # Verify user has access to this event
        is_valid, error_message = validate_event_access(current_user, event)
        if not is_valid:
            return HttpResponse(error_message, status=403)
        
        # Get pagination parameters
        page_number = request.GET.get('page', 1)
        try:
            page_number = int(page_number)
        except (ValueError, TypeError):
            page_number = 1
            
        # Get all connections for this user at this event with pagination
        # Include both directions: where user is from_user OR to_user
        from django.db.models import Q
        connections_queryset = Connection.objects.filter(
            Q(from_user=current_user) | Q(to_user=current_user),
            event=event,
            status=ConnectionStatus.ACCEPTED
        ).select_related('from_user', 'to_user', 'from_user__networking_profile', 'to_user__networking_profile').order_by('-connected_at')
        
        # Debug logging to help troubleshoot
        logger.info(f"User {current_user.username} ({current_user.email}) viewing connections for event {event.id}")
        logger.info(f"Total connections found: {connections_queryset.count()}")
        
        # Paginate connections (20 per page)
        paginator = Paginator(connections_queryset, 20)
        connections_page = paginator.get_page(page_number)
        connections = connections_page.object_list
        
        logger.info(f"Connections on current page: {len(connections)}")
        for conn in connections:
            logger.info(f"Connection: {conn.from_user.username} -> {conn.to_user.username}, method: {conn.connection_method}, status: {conn.status}")
        
        # Build connections HTML using helper function
        connections_html = build_connection_html(connections, event, current_user)
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>My Connections - {event.name}</title>
            <style>
                body {{
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
                    min-height: 100vh;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 20px;
                    padding: 40px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 40px;
                }}
                .title {{
                    font-size: 28px;
                    font-weight: 700;
                    color: #1e293b;
                    margin-bottom: 10px;
                }}
                .subtitle {{
                    color: #64748b;
                    font-size: 16px;
                }}
                .stats {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 20px;
                    margin: 30px 0;
                    padding: 25px;
                    background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
                    border-radius: 16px;
                    border: 1px solid #3b82f6;
                }}
                .stat-item {{
                    text-align: center;
                }}
                .stat-number {{
                    font-size: 24px;
                    font-weight: 700;
                    color: #1d4ed8;
                    margin-bottom: 5px;
                }}
                .stat-label {{
                    font-size: 12px;
                    color: #64748b;
                    text-transform: uppercase;
                    font-weight: 500;
                }}
                .empty-state {{
                    text-align: center;
                    padding: 60px 20px;
                    color: #64748b;
                }}
                .empty-icon {{
                    font-size: 64px;
                    margin-bottom: 20px;
                }}
                .empty-title {{
                    font-size: 20px;
                    font-weight: 600;
                    color: #475569;
                    margin-bottom: 12px;
                }}
                .empty-subtitle {{
                    font-size: 14px;
                    line-height: 1.5;
                    margin-bottom: 30px;
                }}
                .btn {{
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    padding: 12px 24px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: 600;
                    font-size: 14px;
                    transition: all 0.3s ease;
                }}
                .btn-primary {{
                    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
                    color: white;
                }}
                .btn-secondary {{
                    background: #f1f5f9;
                    color: #475569;
                    border: 1px solid #e2e8f0;
                }}
                .btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(0,0,0,0.15);
                }}
                .actions {{
                    display: flex;
                    gap: 15px;
                    justify-content: center;
                    flex-wrap: wrap;
                    margin-top: 30px;
                }}
                @media (max-width: 640px) {{
                    body {{ padding: 10px; }}
                    .container {{ padding: 25px 20px; }}
                    .actions {{ flex-direction: column; align-items: stretch; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="title">🔗 My Connections</div>
                    <div class="subtitle">Professional network from {event.name}</div>
                </div>
                
                <div class="stats">
                    <div class="stat-item">
                        <div class="stat-number">0</div>
                        <div class="stat-label">Total Connections</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">0</div>
                        <div class="stat-label">This Event</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">0</div>
                        <div class="stat-label">Points Earned</div>
                    </div>
                </div>
                
                <div class="empty-state">
                    <div class="empty-icon">🤝</div>
                    <div class="empty-title">No connections yet</div>
                    <div class="empty-subtitle">
                        Start networking at the event! Scan QR codes of people you meet<br>
                        to build your professional network and earn gamification points.
                    </div>
                    
                    <div class="actions">
                        <a href="/networking/directory/{event.id}/" class="btn btn-primary">
                            <span>👥</span> Browse Attendees
                        </a>
                        <a href="javascript:history.back()" class="btn btn-secondary">
                            <span>←</span> Back to Ticket
                        </a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''
        
        return HttpResponse(html)
        
    except Exception as e:
        logger.error(f"Error loading connections for user {request.user.id if request.user.is_authenticated else 'anonymous'} at event {event_id}: {str(e)}")
        return HttpResponse(f"Error loading connections: {str(e)}", status=500)


@login_required
def networking_profile_page(request: HttpRequest, user_id: int, event_id: int) -> HttpResponse:
    """Attendee networking profile page with edit functionality"""
    try:
        user = get_object_or_404(User, id=user_id)
        event = get_object_or_404(Event, id=event_id)
        
        # Authorization check - users can only edit their own profile
        if request.user.id != user_id:
            return HttpResponse("Unauthorized: You can only view your own profile", status=403)
        
        # Validate event access
        is_valid, error_message = validate_event_access(request.user, event)
        if not is_valid:
            return HttpResponse(f"Access denied: {error_message}", status=403)
        
        # Get or create networking profile
        profile, created = NetworkingProfile.objects.get_or_create(
            user=user,
            defaults={
                'company': getattr(user, 'company', ''),
                'visible_in_directory': True,
                'allow_contact_sharing': True
            }
        )
        
        # Get networking stats
        total_connections = Connection.objects.filter(from_user=user).count()
        event_connections = Connection.objects.filter(from_user=user, event=event).count()
        
        # Calculate total points from networking
        total_points = sum(
            conn.points_awarded or 0 
            for conn in Connection.objects.filter(from_user=user, gamification_processed=True)
        )
        
        # Get CSRF token for form
        csrf_token = get_token(request)
        
        # Check if form was just submitted successfully
        show_success = request.GET.get('updated') == '1'
        
        html = f'''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Networking Profile - {escape(user.get_full_name() or user.username)}</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
                    min-height: 100vh;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 20px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
                    padding: 30px;
                    text-align: center;
                    color: white;
                }}
                .avatar {{
                    width: 80px;
                    height: 80px;
                    border-radius: 50%;
                    background: rgba(255,255,255,0.2);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 36px;
                    font-weight: bold;
                    margin: 0 auto 15px;
                    border: 3px solid rgba(255,255,255,0.3);
                }}
                .name {{
                    font-size: 24px;
                    font-weight: 700;
                    margin-bottom: 5px;
                }}
                .event {{
                    font-size: 14px;
                    opacity: 0.9;
                }}
                .content {{
                    padding: 30px;
                }}
                .stats {{
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 20px;
                    margin-bottom: 30px;
                    padding: 25px;
                    background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
                    border-radius: 16px;
                    border: 1px solid #3b82f6;
                }}
                .stat-item {{
                    text-align: center;
                }}
                .stat-number {{
                    font-size: 24px;
                    font-weight: 700;
                    color: #1d4ed8;
                    margin-bottom: 5px;
                }}
                .stat-label {{
                    font-size: 12px;
                    color: #64748b;
                    text-transform: uppercase;
                    font-weight: 500;
                }}
                .profile-section {{
                    margin-bottom: 25px;
                }}
                .section-title {{
                    font-size: 18px;
                    font-weight: 600;
                    color: #1e293b;
                    margin-bottom: 15px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }}
                .form-group {{
                    margin-bottom: 20px;
                }}
                .form-label {{
                    display: block;
                    font-size: 14px;
                    font-weight: 600;
                    color: #374151;
                    margin-bottom: 6px;
                }}
                .form-control {{
                    width: 100%;
                    padding: 12px 16px;
                    border: 2px solid #e5e7eb;
                    border-radius: 8px;
                    font-size: 14px;
                    transition: border-color 0.3s ease;
                    background: #f9fafb;
                }}
                .form-control:focus {{
                    outline: none;
                    border-color: #3b82f6;
                    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
                    background: white;
                }}
                .form-control.textarea {{
                    resize: vertical;
                    min-height: 100px;
                }}
                .checkbox-group {{
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    padding: 15px;
                    background: #f8fafc;
                    border-radius: 8px;
                    border: 1px solid #e2e8f0;
                    margin-bottom: 15px;
                }}
                .checkbox-group input[type="checkbox"] {{
                    width: 18px;
                    height: 18px;
                    accent-color: #3b82f6;
                }}
                .checkbox-group label {{
                    font-size: 14px;
                    color: #374151;
                    cursor: pointer;
                }}
                .btn {{
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    padding: 12px 24px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: 600;
                    font-size: 14px;
                    transition: all 0.3s ease;
                    cursor: pointer;
                    border: none;
                }}
                .btn-primary {{
                    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
                    color: white;
                }}
                .btn-secondary {{
                    background: #f1f5f9;
                    color: #475569;
                    border: 1px solid #e2e8f0;
                }}
                .btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(0,0,0,0.15);
                }}
                .actions {{
                    display: flex;
                    gap: 15px;
                    justify-content: center;
                    flex-wrap: wrap;
                    margin-top: 30px;
                    padding-top: 25px;
                    border-top: 1px solid #e2e8f0;
                }}
                .success-message {{
                    background: #dcfce7;
                    border: 1px solid #16a34a;
                    color: #15803d;
                    padding: 12px 16px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    font-size: 14px;
                }}
                @media (max-width: 640px) {{
                    body {{ padding: 10px; }}
                    .container {{ border-radius: 12px; }}
                    .header, .content {{ padding: 20px; }}
                    .stats {{ grid-template-columns: 1fr; gap: 15px; }}
                    .actions {{ flex-direction: column; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="avatar">
                        {escape(user.get_full_name() or user.username)[0].upper()}
                    </div>
                    <div class="name">{escape(user.get_full_name() or user.username)}</div>
                    <div class="event">Networking Profile for {escape(event.name)}</div>
                </div>
                
                <div class="content">
                    <div class="stats">
                        <div class="stat-item">
                            <div class="stat-number">{total_connections}</div>
                            <div class="stat-label">Total Connections</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">{event_connections}</div>
                            <div class="stat-label">This Event</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">{total_points}</div>
                            <div class="stat-label">Points Earned</div>
                        </div>
                    </div>
                    
                    {'<div class="success-message"><span>&#10004;</span> Your networking profile has been updated successfully!</div>' if show_success else ''}
                    
                    <form method="POST" action="/networking/profile/{user_id}/{event_id}/update/">
                        <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
                        
                        <div class="profile-section">
                            <div class="section-title">
                                <span>&#128100;</span> Profile Information
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label" for="company">Company</label>
                                <input type="text" id="company" name="company" class="form-control" 
                                       value="{escape(profile.company or '')}" placeholder="Your company name">
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label" for="industry">Industry</label>
                                <input type="text" id="industry" name="industry" class="form-control" 
                                       value="{escape(profile.industry or '')}" placeholder="e.g. Technology, Healthcare, Finance">
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label" for="interests">Interests</label>
                                <input type="text" id="interests" name="interests" class="form-control" 
                                       value="{escape(profile.interests or '')}" placeholder="e.g. AI, Marketing, Startups (comma separated)">
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label" for="bio">Bio</label>
                                <textarea id="bio" name="bio" class="form-control textarea" 
                                          placeholder="Tell others about yourself and what you do...">{escape(profile.bio or '')}</textarea>
                            </div>
                        </div>
                        
                        <div class="profile-section">
                            <div class="section-title">
                                <span>&#128274;</span> Privacy Settings
                            </div>
                            
                            <div class="checkbox-group">
                                <input type="checkbox" id="visible_in_directory" name="visible_in_directory" 
                                       {"checked" if profile.visible_in_directory else ""}>
                                <label for="visible_in_directory">Show my profile in the attendee directory</label>
                            </div>
                            
                            <div class="checkbox-group">
                                <input type="checkbox" id="allow_contact_sharing" name="allow_contact_sharing" 
                                       {"checked" if profile.allow_contact_sharing else ""}>
                                <label for="allow_contact_sharing">Allow others to see my contact information when we connect</label>
                            </div>
                        </div>
                        
                        <div class="actions">
                            <button type="submit" class="btn btn-primary">
                                <span>&#128190;</span> Save Profile
                            </button>
                            <a href="javascript:history.back()" class="btn btn-secondary">
                                <span>←</span> Back to Ticket
                            </a>
                        </div>
                    </form>
                </div>
            </div>
            
            <script>
                // Auto-hide success message after 5 seconds
                document.addEventListener('DOMContentLoaded', function() {{
                    const successMessage = document.querySelector('.success-message');
                    if (successMessage) {{
                        setTimeout(function() {{
                            successMessage.style.transition = 'opacity 0.5s ease-out';
                            successMessage.style.opacity = '0';
                            setTimeout(function() {{
                                successMessage.remove();
                            }}, 500);
                        }}, 5000);
                    }}
                }});
            </script>
        </body>
        </html>
        '''
        
        return HttpResponse(html)
        
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} not found for profile page")
        return HttpResponse("User not found", status=404)
    except Event.DoesNotExist:
        logger.error(f"Event with id {event_id} not found for profile page")
        return HttpResponse("Event not found", status=404)
    except Exception as e:
        logger.error(f"Error loading networking profile for user {user_id}, event {event_id}: {str(e)}")
        return HttpResponse("An error occurred while loading your profile. Please try again.", status=500)


@login_required
@require_http_methods(["POST"])
def update_networking_profile(request: HttpRequest, user_id: int, event_id: int) -> HttpResponse:
    """Handle profile updates"""
    try:
        user = get_object_or_404(User, id=user_id)
        event = get_object_or_404(Event, id=event_id)
        
        # Authorization check - users can only update their own profile
        if request.user.id != user_id:
            return HttpResponse("Unauthorized: You can only update your own profile", status=403)
        
        # Validate event access
        is_valid, error_message = validate_event_access(request.user, event)
        if not is_valid:
            return HttpResponse(f"Access denied: {error_message}", status=403)
        
        # Get or create networking profile
        profile, created = NetworkingProfile.objects.get_or_create(user=user)
        
        # Validate and sanitize input data with enhanced security checks
        import re
        
        company = request.POST.get('company', '').strip()
        industry = request.POST.get('industry', '').strip() 
        interests = request.POST.get('interests', '').strip()
        bio = request.POST.get('bio', '').strip()
        
        # Enhanced validation with security checks
        if len(company) > 200:
            return HttpResponse("Company name too long (max 200 characters)", status=400)
        if len(industry) > 100:
            return HttpResponse("Industry too long (max 100 characters)", status=400)
        if len(interests) > 500:
            return HttpResponse("Interests too long (max 500 characters)", status=400)
        if len(bio) > 500:
            return HttpResponse("Bio too long (max 500 characters)", status=400)
        
        # Check for suspicious patterns (basic XSS prevention)
        suspicious_patterns = [r'<script', r'javascript:', r'onclick=', r'onload=']
        for field, value in [('company', company), ('industry', industry), ('interests', interests), ('bio', bio)]:
            for pattern in suspicious_patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    logger.warning(f"Suspicious content detected in {field}: {value[:50]}...")
                    return HttpResponse(f"Invalid content in {field}", status=400)
        
        # Truncate after validation to ensure data integrity
        company = company[:200]
        industry = industry[:100] 
        interests = interests[:500]
        bio = bio[:500]
        
        # Update profile fields
        profile.company = company
        profile.industry = industry
        profile.interests = interests
        profile.bio = bio
        profile.visible_in_directory = 'visible_in_directory' in request.POST
        profile.allow_contact_sharing = 'allow_contact_sharing' in request.POST
        
        profile.save()
        logger.info(f"Profile updated successfully for user {user_id}")
        
        # Redirect back to profile page with success message
        return redirect(f'/networking/profile/{user_id}/{event_id}/?updated=1')
        
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} not found for profile update")
        return HttpResponse("User not found", status=404)
    except Event.DoesNotExist:
        logger.error(f"Event with id {event_id} not found for profile update")
        return HttpResponse("Event not found", status=404)
    except ValidationError as e:
        logger.warning(f"Validation error updating profile for user {user_id}: {str(e)}")
        return HttpResponse("Invalid data provided", status=400)
    except Exception as e:
        logger.error(f"Error updating networking profile for user {user_id}, event {event_id}: {str(e)}")
        return HttpResponse("An error occurred while updating your profile. Please try again.", status=500)


def networking_connect_page(request: HttpRequest, qr_token: str) -> HttpResponse:
    """Handle QR code scanning - connect users via QR token"""
    try:
        # Get event ID from query params
        event_id = request.GET.get('event')
        if not event_id:
            return HttpResponse("Event ID missing from QR code", status=400)
            
        event = get_object_or_404(Event, id=event_id)
        
        # Find the user with this QR token
        try:
            profile = NetworkingProfile.objects.get(networking_qr_token=qr_token)
            target_user = profile.user
            logger.info(f"QR code scan: qr_token={qr_token}, target_user={target_user.id} ({target_user.username})")
        except NetworkingProfile.DoesNotExist:
            logger.error(f"Invalid QR token: {qr_token}")
            return HttpResponse("Invalid QR code", status=404)
        
        # Create connection page HTML
        html = f'''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Connect with {escape(target_user.get_full_name() or target_user.username)}</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
                    min-height: 100vh;
                    padding: 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .container {{
                    max-width: 500px;
                    width: 100%;
                    background: white;
                    border-radius: 20px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                    overflow: hidden;
                    text-align: center;
                }}
                .header {{
                    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
                    padding: 40px 30px;
                    color: white;
                }}
                .qr-icon {{
                    font-size: 48px;
                    margin-bottom: 15px;
                }}
                .title {{
                    font-size: 24px;
                    font-weight: 700;
                    margin-bottom: 10px;
                }}
                .subtitle {{
                    font-size: 16px;
                    opacity: 0.9;
                }}
                .content {{
                    padding: 40px 30px;
                }}
                .avatar {{
                    width: 80px;
                    height: 80px;
                    border-radius: 50%;
                    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 32px;
                    font-weight: bold;
                    color: white;
                    margin: 0 auto 20px;
                }}
                .user-name {{
                    font-size: 20px;
                    font-weight: 600;
                    color: #1e293b;
                    margin-bottom: 5px;
                }}
                .user-company {{
                    color: #64748b;
                    margin-bottom: 30px;
                }}
                .message {{
                    background: #f1f5f9;
                    padding: 20px;
                    border-radius: 12px;
                    margin-bottom: 30px;
                    color: #475569;
                    line-height: 1.5;
                }}
                .actions {{
                    display: flex;
                    gap: 15px;
                    justify-content: center;
                    flex-wrap: wrap;
                }}
                .btn {{
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    padding: 12px 24px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: 600;
                    font-size: 14px;
                    transition: all 0.3s ease;
                    border: none;
                    cursor: pointer;
                }}
                .btn-primary {{
                    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
                    color: white;
                }}
                .btn-secondary {{
                    background: #f1f5f9;
                    color: #475569;
                    border: 1px solid #e2e8f0;
                }}
                .btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(0,0,0,0.15);
                }}
                @media (max-width: 640px) {{
                    .container {{ margin: 10px; }}
                    .actions {{ flex-direction: column; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="qr-icon">&#128241;</div>
                    <div class="title">QR Code Scanned!</div>
                    <div class="subtitle">Connect with this attendee</div>
                </div>
                
                <div class="content">
                    <div class="avatar">
                        {escape(target_user.get_full_name() or target_user.username)[0].upper()}
                    </div>
                    <div class="user-name">{escape(target_user.get_full_name() or target_user.username)}</div>
                    <div class="user-company">{escape(profile.company or "Attendee")} • {escape(event.name)}</div>
                    
                    <div class="message">
                        <strong>&#129309; Ready to connect?</strong><br>
                        This will add {escape(target_user.get_full_name() or target_user.username)} to your professional network 
                        and you'll both earn networking points!
                    </div>
                    
                    <div class="actions">
                        <a href="/networking/connect-action/?from_user={target_user.id}&to_user=self&event={event.id}&method=qr_scan" 
                           class="btn btn-primary">
                            <span>&#129309;</span> Connect Now
                        </a>
                        <a href="/networking/directory/{event.id}/" class="btn btn-secondary">
                            <span>👥</span> Browse Attendees
                        </a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''
        
        return HttpResponse(html)
        
    except Event.DoesNotExist:
        logger.error(f"Event with id {event_id} not found for QR connect")
        return HttpResponse("Event not found", status=404)
    except Exception as e:
        logger.error(f"Error handling QR connect for token {qr_token}: {str(e)}")
        return HttpResponse("An error occurred while processing the QR code", status=500)


@csrf_protect
def networking_connect_action(request: HttpRequest) -> HttpResponse:
    """Handle connection creation from QR scan with user-friendly response"""
    try:
        # Get parameters from query string
        from_user_id = request.GET.get('from_user')
        to_user = request.GET.get('to_user') 
        event_id = request.GET.get('event')
        method = request.GET.get('method', ConnectionMethod.QR_SCAN)
        
        # Debug the parameters received
        logger.info(f"Connection parameters: from_user_id={from_user_id}, to_user={to_user}, event_id={event_id}, method={method}")
        
        if not all([from_user_id, to_user, event_id]):
            return HttpResponse("Missing required parameters", status=400)
            
        # Get the event
        event = get_object_or_404(Event, id=event_id)
        
        # Get current user (person doing the connecting) - check auth first
        logger.info(f"Request user: {request.user}, is_authenticated: {request.user.is_authenticated}")
        
        if not request.user.is_authenticated:
            logger.warning("User not authenticated, redirecting to login")
            return redirect(f'/login/?next=/networking/connect-action/?from_user={from_user_id}&to_user={to_user}&event={event_id}&method={method}')
            
        current_user = request.user
        logger.info(f"Authenticated user: {current_user.id} ({current_user.username})")
        
        # Get the QR code owner (person being connected to)
        qr_code_owner = get_object_or_404(User, id=from_user_id)
        logger.info(f"QR code owner found: {qr_code_owner.id} ({qr_code_owner.username})")
        
        # Debug logging
        logger.info(f"Connection attempt: current_user={current_user.id} (type: {type(current_user.id)}, username: {current_user.username})")
        logger.info(f"QR code owner: qr_code_owner={qr_code_owner.id} (type: {type(qr_code_owner.id)}, username: {qr_code_owner.username})")
        logger.info(f"Comparison: {current_user.id} == {qr_code_owner.id} = {current_user.id == qr_code_owner.id}")
        
        # Prevent self-connection
        if int(current_user.id) == int(qr_code_owner.id):
            logger.warning(f"Self-connection attempt blocked: user {current_user.id} tried to connect to themselves")
            error_html = f'''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Cannot Connect</title>
                <style>
                    * {{
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }}
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
                        min-height: 100vh;
                        padding: 20px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }}
                    .container {{
                        max-width: 500px;
                        width: 100%;
                        background: white;
                        border-radius: 20px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                        overflow: hidden;
                        text-align: center;
                    }}
                    .header {{
                        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                        padding: 40px 30px;
                        color: white;
                    }}
                    .icon {{
                        font-size: 48px;
                        margin-bottom: 15px;
                    }}
                    .title {{
                        font-size: 24px;
                        font-weight: 700;
                        margin-bottom: 10px;
                    }}
                    .content {{
                        padding: 40px 30px;
                    }}
                    .message {{
                        background: #fee2e2;
                        padding: 20px;
                        border-radius: 12px;
                        margin-bottom: 30px;
                        color: #991b1b;
                        line-height: 1.5;
                    }}
                    .debug {{
                        background: #f3f4f6;
                        padding: 15px;
                        border-radius: 8px;
                        margin-bottom: 30px;
                        font-family: monospace;
                        font-size: 12px;
                        text-align: left;
                        color: #374151;
                    }}
                    .btn {{
                        display: inline-flex;
                        align-items: center;
                        gap: 8px;
                        padding: 12px 24px;
                        border-radius: 8px;
                        text-decoration: none;
                        font-weight: 600;
                        font-size: 14px;
                        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
                        color: white;
                        transition: all 0.3s ease;
                    }}
                    .btn:hover {{
                        transform: translateY(-2px);
                        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="icon">&#10060;</div>
                        <div class="title">Cannot Connect to Yourself</div>
                    </div>
                    
                    <div class="content">
                        <div class="message">
                            <strong>Oops!</strong><br>
                            This is your own QR code. You cannot connect to yourself.<br><br>
                            To make connections, scan another attendee's QR code instead!
                        </div>
                        
                        <div class="debug">
                            <strong>Debug Info:</strong><br>
                            Your User ID: {current_user.id}<br>
                            Your Username: {escape(current_user.username)}<br>
                            QR Code Owner ID: {qr_code_owner.id}<br>
                            QR Code Owner: {escape(qr_code_owner.username)}<br>
                        </div>
                        
                        <a href="/networking/directory/{event.id}/" class="btn">
                            <span>👥</span> Browse Attendees
                        </a>
                    </div>
                </div>
            </body>
            </html>
            '''
            return HttpResponse(error_html)
            
        # Check if connection already exists
        existing_connection = check_existing_connection(current_user, qr_code_owner, event)
        
        if existing_connection:
            # Connection already exists - show friendly message
            success_html = f'''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Already Connected</title>
                <style>
                    * {{
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }}
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
                        min-height: 100vh;
                        padding: 20px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }}
                    .container {{
                        max-width: 500px;
                        width: 100%;
                        background: white;
                        border-radius: 20px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                        overflow: hidden;
                        text-align: center;
                    }}
                    .header {{
                        background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
                        padding: 40px 30px;
                        color: white;
                    }}
                    .icon {{
                        font-size: 48px;
                        margin-bottom: 15px;
                    }}
                    .title {{
                        font-size: 24px;
                        font-weight: 700;
                        margin-bottom: 10px;
                    }}
                    .subtitle {{
                        font-size: 16px;
                        opacity: 0.9;
                    }}
                    .content {{
                        padding: 40px 30px;
                    }}
                    .message {{
                        background: #fef3c7;
                        padding: 20px;
                        border-radius: 12px;
                        margin-bottom: 30px;
                        color: #92400e;
                        line-height: 1.5;
                    }}
                    .actions {{
                        display: flex;
                        gap: 15px;
                        justify-content: center;
                        flex-wrap: wrap;
                    }}
                    .btn {{
                        display: inline-flex;
                        align-items: center;
                        gap: 8px;
                        padding: 12px 24px;
                        border-radius: 8px;
                        text-decoration: none;
                        font-weight: 600;
                        font-size: 14px;
                        transition: all 0.3s ease;
                        border: none;
                        cursor: pointer;
                    }}
                    .btn-primary {{
                        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
                        color: white;
                    }}
                    .btn:hover {{
                        transform: translateY(-2px);
                        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="icon">&#129309;</div>
                        <div class="title">Already Connected!</div>
                        <div class="subtitle">You're already in each other's network</div>
                    </div>
                    
                    <div class="content">
                        <div class="message">
                            <strong>Good news!</strong><br>
                            You and {escape(qr_code_owner.get_full_name() or qr_code_owner.username)} are already connected 
                            at {escape(event.name)}. Keep networking with other attendees!
                        </div>
                        
                        <div class="actions">
                            <a href="/networking/directory/{event.id}/" class="btn btn-primary">
                                <span>👥</span> Browse More Attendees
                            </a>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            '''
            return HttpResponse(success_html)
        
        # Create bidirectional connection using helper method
        try:
            connection, reverse_connection = create_bidirectional_connection(
                from_user=current_user,
                to_user=qr_code_owner,
                event=event,
                method=method
            )
        except Exception as e:
            logger.error(f"Failed to create connection: {str(e)}")
            return HttpResponse("An error occurred while creating the connection. Please try again.", status=500)
        
        # Create success page
        success_html = f'''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Connection Successful</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
                    min-height: 100vh;
                    padding: 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .container {{
                    max-width: 500px;
                    width: 100%;
                    background: white;
                    border-radius: 20px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                    overflow: hidden;
                    text-align: center;
                }}
                .header {{
                    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                    padding: 40px 30px;
                    color: white;
                }}
                .icon {{
                    font-size: 48px;
                    margin-bottom: 15px;
                }}
                .title {{
                    font-size: 24px;
                    font-weight: 700;
                    margin-bottom: 10px;
                }}
                .subtitle {{
                    font-size: 16px;
                    opacity: 0.9;
                }}
                .content {{
                    padding: 40px 30px;
                }}
                .avatar {{
                    width: 80px;
                    height: 80px;
                    border-radius: 50%;
                    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 32px;
                    font-weight: bold;
                    color: white;
                    margin: 0 auto 20px;
                }}
                .user-name {{
                    font-size: 20px;
                    font-weight: 600;
                    color: #1e293b;
                    margin-bottom: 30px;
                }}
                .message {{
                    background: #d1fae5;
                    padding: 20px;
                    border-radius: 12px;
                    margin-bottom: 30px;
                    color: #065f46;
                    line-height: 1.5;
                }}
                .points {{
                    background: #fef3c7;
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 30px;
                    color: #92400e;
                    font-weight: 600;
                }}
                .actions {{
                    display: flex;
                    gap: 15px;
                    justify-content: center;
                    flex-wrap: wrap;
                }}
                .btn {{
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    padding: 12px 24px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: 600;
                    font-size: 14px;
                    transition: all 0.3s ease;
                    border: none;
                    cursor: pointer;
                }}
                .btn-primary {{
                    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
                    color: white;
                }}
                .btn-secondary {{
                    background: #f1f5f9;
                    color: #475569;
                    border: 1px solid #e2e8f0;
                }}
                .btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(0,0,0,0.15);
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="icon">&#9989;</div>
                    <div class="title">Connected Successfully!</div>
                    <div class="subtitle">You've made a new connection</div>
                </div>
                
                <div class="content">
                    <div class="avatar">
                        {escape(qr_code_owner.get_full_name() or qr_code_owner.username)[0].upper()}
                    </div>
                    <div class="user-name">Connected with {escape(qr_code_owner.get_full_name() or qr_code_owner.username)}</div>
                    
                    <div class="message">
                        <strong>&#127881; Great job!</strong><br>
                        You and {escape(qr_code_owner.get_full_name() or qr_code_owner.username)} are now connected 
                        in your professional network for {escape(event.name)}.
                    </div>
                    
                    <div class="points">
                        <span>&#11088;</span> +10 Networking Points Earned!
                    </div>
                    
                    <div class="actions">
                        <a href="/networking/directory/{event.id}/" class="btn btn-primary">
                            <span>👥</span> Continue Networking
                        </a>
                        <a href="/networking/connections/{event.id}/" class="btn btn-secondary">
                            <span>&#129309;</span> My Connections
                        </a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''
        
        return HttpResponse(success_html)
        
    except User.DoesNotExist:
        return HttpResponse("User not found", status=404)
    except Event.DoesNotExist:
        return HttpResponse("Event not found", status=404)
    except Exception as e:
        logger.error(f"Error creating connection: {str(e)}")
        return HttpResponse("An error occurred while creating the connection. Please try again.", status=500)
