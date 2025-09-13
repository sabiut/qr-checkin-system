import qrcode
import qrcode.image.svg
from io import BytesIO
import base64
from django.conf import settings
from django.urls import reverse
from .models import NetworkingProfile
import logging

logger = logging.getLogger(__name__)


class NetworkingQRService:
    """Service for generating networking QR codes"""
    
    @staticmethod
    def generate_networking_qr(user, event, format='png'):
        """Generate QR code for networking contact exchange"""
        try:
            # Get or create networking profile
            profile, created = NetworkingProfile.objects.get_or_create(
                user=user,
                defaults={
                    'company': getattr(user, 'company', ''),
                    'visible_in_directory': True,
                    'allow_contact_sharing': True
                }
            )
            
            # Create QR code data URL
            qr_data = f"{getattr(settings, 'BASE_URL', 'http://localhost:3000')}/networking/connect/{profile.networking_qr_token}?event={event.id}"
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            if format == 'svg':
                # SVG format for web display
                factory = qrcode.image.svg.SvgPathImage
                img = qr.make_image(image_factory=factory)
                buffer = BytesIO()
                img.save(buffer)
                svg_data = buffer.getvalue().decode()
                return svg_data
            else:
                # PNG format for printing
                img = qr.make_image(fill_color="black", back_color="white")
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                img_data = buffer.getvalue()
                img_base64 = base64.b64encode(img_data).decode()
                return f"data:image/png;base64,{img_base64}"
                
        except Exception as e:
            logger.error(f"Failed to generate networking QR for user {user.id}: {str(e)}")
            return None
    
    @staticmethod
    def get_networking_info_from_token(token):
        """Get user networking info from QR token"""
        try:
            profile = NetworkingProfile.objects.select_related('user').get(
                networking_qr_token=token,
                allow_contact_sharing=True
            )
            return profile.get_shareable_info()
        except NetworkingProfile.DoesNotExist:
            return None
    
    @staticmethod
    def create_networking_badge_html(user, event):
        """Generate HTML for a printable networking badge"""
        try:
            profile, created = NetworkingProfile.objects.get_or_create(user=user)
            qr_code = NetworkingQRService.generate_networking_qr(user, event, format='png')
            
            badge_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Networking Badge - {user.get_full_name() or user.username}</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 20px;
                        background: #f5f5f5;
                    }}
                    .badge {{
                        width: 4in;
                        height: 6in;
                        background: white;
                        border: 2px solid #3B82F6;
                        border-radius: 10px;
                        padding: 20px;
                        text-align: center;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                        margin: 0 auto;
                    }}
                    .header {{
                        background: linear-gradient(135deg, #3B82F6, #1D4ED8);
                        color: white;
                        padding: 15px;
                        border-radius: 8px;
                        margin-bottom: 20px;
                    }}
                    .name {{
                        font-size: 24px;
                        font-weight: bold;
                        margin-bottom: 5px;
                    }}
                    .title {{
                        font-size: 14px;
                        opacity: 0.9;
                    }}
                    .company {{
                        font-size: 16px;
                        color: #374151;
                        margin-bottom: 20px;
                        font-weight: 500;
                    }}
                    .qr-section {{
                        margin: 20px 0;
                    }}
                    .qr-code {{
                        max-width: 150px;
                        height: auto;
                        margin: 0 auto;
                        display: block;
                    }}
                    .qr-text {{
                        font-size: 12px;
                        color: #6B7280;
                        margin-top: 10px;
                    }}
                    .event-info {{
                        margin-top: 20px;
                        padding-top: 15px;
                        border-top: 1px solid #E5E7EB;
                    }}
                    .event-name {{
                        font-size: 14px;
                        font-weight: 600;
                        color: #1F2937;
                    }}
                    .networking-text {{
                        font-size: 12px;
                        color: #059669;
                        font-weight: 500;
                        margin-top: 10px;
                    }}
                    @media print {{
                        body {{ margin: 0; padding: 0; background: white; }}
                        .badge {{ box-shadow: none; border: 2px solid #3B82F6; }}
                    }}
                </style>
            </head>
            <body>
                <div class="badge">
                    <div class="header">
                        <div class="name">{user.get_full_name() or user.username}</div>
                        {f'<div class="title">{profile.job_title}</div>' if profile.job_title else ''}
                    </div>
                    
                    {f'<div class="company">{profile.company}</div>' if profile.company else ''}
                    
                    <div class="qr-section">
                        <img src="{qr_code}" alt="Networking QR Code" class="qr-code">
                        <div class="qr-text">Scan to connect with me!</div>
                    </div>
                    
                    <div class="event-info">
                        <div class="event-name">{event.name}</div>
                        <div class="networking-text">handshake Let's Network!</div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return badge_html
            
        except Exception as e:
            logger.error(f"Failed to create networking badge for user {user.id}: {str(e)}")
            return None


class NetworkingAnalyticsService:
    """Service for networking analytics and insights"""
    
    @staticmethod
    def get_event_networking_stats(event):
        """Get comprehensive networking stats for an event"""
        from .models import Connection, NetworkingInteraction
        
        connections = Connection.objects.filter(event=event)
        interactions = NetworkingInteraction.objects.filter(event=event)
        
        stats = {
            'total_connections': connections.count(),
            'unique_networkers': connections.values('from_user').distinct().count(),
            'qr_scans': connections.filter(connection_method='qr_scan').count(),
            'directory_connections': connections.filter(connection_method='directory').count(),
            'avg_connections_per_user': 0,
            'most_connected_users': [],
            'networking_activity': {},
            'connection_timeline': [],
        }
        
        if connections.exists():
            # Calculate averages
            from django.db.models import Avg
            user_connections = connections.values('from_user').annotate(
                count=Count('id')
            ).aggregate(avg=Avg('count'))
            stats['avg_connections_per_user'] = round(user_connections.get('avg', 0), 2)
            
            # Most connected users
            most_connected = connections.values(
                'from_user__username', 
                'from_user__first_name', 
                'from_user__last_name'
            ).annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            stats['most_connected_users'] = [
                {
                    'username': item['from_user__username'],
                    'name': f"{item['from_user__first_name']} {item['from_user__last_name']}".strip() or item['from_user__username'],
                    'connections': item['count']
                }
                for item in most_connected
            ]
            
            # Activity by hour
            from django.db.models import Extract
            hourly_activity = connections.annotate(
                hour=Extract('connected_at', 'hour')
            ).values('hour').annotate(
                count=Count('id')
            ).order_by('hour')
            
            stats['networking_activity'] = {
                item['hour']: item['count'] for item in hourly_activity
            }
        
        return stats
    
    @staticmethod
    def get_user_networking_insights(user):
        """Get personalized networking insights for a user"""
        from .models import Connection
        
        connections = Connection.objects.filter(
            Q(from_user=user) | Q(to_user=user)
        )
        
        insights = {
            'total_connections': connections.count(),
            'recent_connections': connections.filter(
                connected_at__gte=timezone.now() - timedelta(days=7)
            ).count(),
            'favorite_method': None,
            'most_active_events': [],
            'networking_streak': 0,
            'recommendations': []
        }
        
        if connections.exists():
            # Favorite connection method
            methods = connections.values('connection_method').annotate(
                count=Count('connection_method')
            ).order_by('-count')
            
            if methods:
                insights['favorite_method'] = methods[0]['connection_method']
            
            # Most active events
            event_activity = connections.values('event__name').annotate(
                count=Count('id')
            ).order_by('-count')[:5]
            insights['most_active_events'] = list(event_activity)
            
            # Generate recommendations
            insights['recommendations'] = NetworkingAnalyticsService._generate_networking_recommendations(user, connections)
        
        return insights
    
    @staticmethod
    def _generate_networking_recommendations(user, connections):
        """Generate personalized networking recommendations"""
        recommendations = []
        
        total_connections = connections.count()
        qr_connections = connections.filter(connection_method='qr_scan').count()
        directory_connections = connections.filter(connection_method='directory').count()
        
        # Recommend using QR codes more
        if qr_connections < total_connections * 0.3:
            recommendations.append({
                'type': 'method',
                'title': 'Try QR Code Networking',
                'description': 'QR codes make connecting faster! Try using your networking QR code at events.',
                'action': 'Show me my QR code'
            })
        
        # Recommend exploring attendee directory
        if directory_connections < total_connections * 0.2:
            recommendations.append({
                'type': 'discovery',
                'title': 'Explore Attendee Directory',
                'description': 'Browse event attendee directories to find people with similar interests before networking.',
                'action': 'Browse directories'
            })
        
        # Recommend setting networking goals
        if total_connections < 10:
            recommendations.append({
                'type': 'goal',
                'title': 'Set a Networking Goal',
                'description': 'Try to make 3-5 new connections at your next event. Quality over quantity!',
                'action': 'Set networking goals'
            })
        
        return recommendations
