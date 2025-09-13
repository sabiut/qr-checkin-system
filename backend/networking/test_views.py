from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import NetworkingProfile, Connection, EventNetworkingSettings
from .services import NetworkingQRService
from events.models import Event
import json

def networking_test_page(request):
    """Simple HTML test page for networking features"""
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Networking Feature Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .section { margin: 30px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
            .qr-code { max-width: 200px; }
            .user-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .user-card { padding: 15px; border: 1px solid #ccc; border-radius: 8px; }
            button { background: #007cba; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #005a87; }
        </style>
    </head>
    <body>
        <h1>handshake Networking Feature Test Page</h1>
    '''
    
    # Show all users with networking profiles
    html += '''
        <div class="section">
            <h2>people Available Users for Testing</h2>
            <div class="user-list">
    '''
    
    profiles = NetworkingProfile.objects.all()[:10]
    for profile in profiles:
        user = profile.user
        html += f'''
            <div class="user-card">
                <h3>{user.get_full_name() or user.username}</h3>
                <p><strong>Email:</strong> {user.email}</p>
                <p><strong>Company:</strong> {profile.company or 'Not set'}</p>
                <p><strong>QR Token:</strong> <small>{profile.networking_qr_token}</small></p>
                <p><strong>Test QR URL:</strong> <br>
                <a href="http://localhost:3000/networking/connect/{profile.networking_qr_token}?event=1" target="_blank">
                    Connect Link
                </a></p>
            </div>
        '''
    
    html += '''
            </div>
        </div>
    '''
    
    # Show events with networking enabled
    html += '''
        <div class="section">
            <h2>📅 Events with Networking</h2>
    '''
    
    events = Event.objects.all()[:5]
    for event in events:
        settings = getattr(event, 'networking_settings', None)
        enabled = settings.enable_networking if settings else 'Not configured'
        html += f'''
            <div style="margin: 10px 0; padding: 10px; background: #f9f9f9; border-radius: 4px;">
                <strong>{event.name}</strong> (ID: {event.id})<br>
                Networking Enabled: {enabled}
            </div>
        '''
    
    html += '''
        </div>
        
        <div class="section">
            <h2>🧪 API Testing Examples</h2>
            <h3>1. Get User Profile</h3>
            <pre>GET /api/networking/profiles/my_profile/</pre>
            
            <h3>2. Browse Directory</h3>
            <pre>GET /api/networking/directory/?event=1</pre>
            
            <h3>3. Scan QR Code (Test Connection)</h3>
            <pre>POST /api/networking/connections/scan_qr/
{
  "networking_token": "b27743b5-931f-49a8-af16-5495e513ad7f",
  "event_id": 1,
  "meeting_location": "Test Location",
  "notes": "Test connection from browser"
}</pre>
            
            <h3>4. View My Connections</h3>
            <pre>GET /api/networking/connections/my_connections/</pre>
        </div>
        
        <div class="section">
            <h2>mobile QR Code Testing</h2>
            <p>You can test QR codes by:</p>
            <ul>
                <li>Scanning with your phone camera</li>
                <li>Using any QR code scanner app</li>
                <li>Clicking the "Connect Link" above</li>
                <li>Using browser dev tools to simulate API calls</li>
            </ul>
        </div>
    </body>
    </html>
    '''
    
    return HttpResponse(html)

def generate_networking_qr(request, user_id, event_id):
    """Generate networking QR code for testing"""
    user = get_object_or_404(User, id=user_id)
    event = get_object_or_404(Event, id=event_id)
    
    qr_code = NetworkingQRService.generate_networking_qr(user, event, format='png')
    
    if qr_code:
        html = f'''
        <!DOCTYPE html>
        <html>
        <head><title>Networking QR Code</title></head>
        <body style="text-align: center; font-family: Arial;">
            <h2>Networking QR Code for {user.get_full_name() or user.username}</h2>
            <h3>Event: {event.name}</h3>
            <img src="{qr_code}" style="max-width: 300px;" alt="Networking QR Code">
            <p>Scan this code to connect at the event!</p>
            <a href="/networking/test/">← Back to Test Page</a>
        </body>
        </html>
        '''
        return HttpResponse(html)
    else:
        return HttpResponse("Failed to generate QR code", status=500)
