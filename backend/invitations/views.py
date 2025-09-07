from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Invitation
from .serializers import InvitationSerializer
from events.models import Event
from events.calendar_utils import create_event_calendar, generate_ics_filename
import logging
import os
import smtplib
from datetime import datetime

logger = logging.getLogger(__name__)

class InvitationViewSet(viewsets.ModelViewSet):
    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer
    permission_classes = [IsAuthenticated]  # Default to authenticated users only
    
    def get_permissions(self):
        """
        - Allow anyone to view tickets (for guest access)
        - Require authentication for other operations
        """
        if self.action == 'view_ticket':
            permission_classes = [AllowAny]  # Allow guests to view their tickets
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
        
    def get_qr_code_html(self, qr_code_data_uri, qr_code_url):
        """Generate HTML for the QR code with proper styling for all devices"""
        # Enhanced mobile-friendly styling
        img_style = (
            "display: block; "
            "max-width: 180px; "
            "width: 100%; "
            "height: auto; "
            "margin: 0 auto; "
            "border: 8px solid white; "
            "box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1); "
            "-webkit-box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1); " # Safari support
            "border-radius: 4px; "
        )
        
        # Add width and height attributes to help email clients with image rendering
        if qr_code_data_uri:
            logger.info(f"Using data URI for QR code in email (length: {len(qr_code_data_uri) if qr_code_data_uri else 0})")
            return f'<img src="{qr_code_data_uri}" width="180" height="180" alt="QR Code" style="{img_style}">'
        elif qr_code_url:
            logger.info(f"Using URL for QR code in email: {qr_code_url}")
            return f'<img src="{qr_code_url}" width="180" height="180" alt="QR Code" style="{img_style}">'
        else:
            logger.warning("No QR code available for email")
            placeholder_style = (
                "display: block; "
                "width: 180px; "
                "height: 180px; "
                "margin: 0 auto; "
                "background: #f1f1f1; "
                "border: 8px solid white; "
                "box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1); "
                "text-align: center; "
                "line-height: 180px; "
                "color: #888; "
                "font-size: 14px; "
            )
            return f'<div style="{placeholder_style}">(QR code not available)</div>'
    
    def _generate_gamification_html(self, invitation, user_account_exists, user_stats, is_authenticated):
        """Generate HTML section for gamification features."""
        if not invitation.guest_email:
            return ""
        
        base_style = """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        
        .gamification-section {
            margin: 40px auto;
            max-width: 800px;
            padding: 0;
            background: #ffffff;
            border-radius: 20px;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            box-shadow: 0 20px 60px rgba(0,0,0,0.1);
            overflow: hidden;
            animation: slideUp 0.5s ease-out;
        }
        
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .gamification-header-wrapper {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .gamification-header-wrapper::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: shimmer 3s infinite;
        }
        
        @keyframes shimmer {
            0%, 100% { transform: translate(0, 0); }
            50% { transform: translate(-50px, -50px); }
        }
        
        .gamification-header {
            color: white;
            font-size: 28px;
            font-weight: 700;
            margin: 0;
            position: relative;
            z-index: 1;
            letter-spacing: -0.5px;
        }
        
        .gamification-subtitle {
            color: rgba(255,255,255,0.9);
            font-size: 16px;
            margin-top: 8px;
            font-weight: 400;
        }
        
        .gamification-content {
            padding: 30px;
        }
        
        .account-prompt {
            background: linear-gradient(135deg, #f6f8fb 0%, #e9ecef 100%);
            padding: 25px;
            border-radius: 16px;
            margin-bottom: 20px;
            border: 1px solid rgba(0,0,0,0.05);
        }
        
        .account-prompt p {
            color: #2d3748;
            line-height: 1.6;
            margin: 10px 0;
        }
        
        .user-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 20px;
            margin: 25px 0;
        }
        
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 16px;
            text-align: center;
            border: 2px solid #e9ecef;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            border-color: #667eea;
            box-shadow: 0 10px 30px rgba(102,126,234,0.1);
        }
        
        .stat-number {
            font-size: 36px;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 5px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 5px;
        }
        
        .stat-label {
            font-size: 14px;
            color: #718096;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .badges-container {
            background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
            padding: 20px;
            border-radius: 16px;
            margin: 20px 0;
        }
        
        .badges-title {
            font-size: 14px;
            font-weight: 600;
            color: #4a5568;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 15px;
            text-align: center;
        }
        
        .badges {
            display: flex;
            justify-content: center;
            gap: 12px;
            flex-wrap: wrap;
        }
        
        .badge {
            font-size: 32px;
            background: white;
            padding: 12px 16px;
            border-radius: 12px;
            border: 2px solid #e9ecef;
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
        }
        
        .badge:hover {
            transform: scale(1.1) rotate(5deg);
            border-color: #667eea;
            box-shadow: 0 5px 20px rgba(102,126,234,0.2);
        }
        
        .badge-tooltip {
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: #2d3748;
            color: white;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 12px;
            white-space: nowrap;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s;
        }
        
        .badge:hover .badge-tooltip {
            opacity: 1;
        }
        
        .register-btn, .login-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 16px 32px;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            margin: 10px 5px;
            text-decoration: none;
            display: inline-block;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102,126,234,0.3);
            position: relative;
            overflow: hidden;
        }
        
        .register-btn::before, .login-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s;
        }
        
        .register-btn:hover::before, .login-btn:hover::before {
            left: 100%;
        }
        
        .register-btn:hover, .login-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102,126,234,0.4);
            color: white;
            text-decoration: none;
        }
        
        .login-btn {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }
        
        .feature-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin-top: 20px;
        }
        
        .feature-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px;
            background: white;
            border-radius: 10px;
            color: #4a5568;
            font-size: 14px;
            transition: all 0.3s ease;
        }
        
        .feature-item:hover {
            background: #f7fafc;
            transform: translateX(5px);
        }
        
        .feature-icon {
            font-size: 20px;
            width: 30px;
            text-align: center;
        }
        
        .progress-container {
            background: #f7fafc;
            border-radius: 16px;
            padding: 20px;
            margin-top: 20px;
        }
        
        .progress-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .progress-title {
            font-size: 16px;
            font-weight: 600;
            color: #2d3748;
        }
        
        .progress-percentage {
            font-size: 14px;
            font-weight: 600;
            color: #667eea;
        }
        
        .progress-bar-wrapper {
            background: #e9ecef;
            height: 12px;
            border-radius: 6px;
            overflow: hidden;
            position: relative;
        }
        
        .progress-bar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100%;
            border-radius: 6px;
            transition: width 1s ease-out;
            position: relative;
            overflow: hidden;
        }
        
        .progress-bar::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            animation: progressShine 2s infinite;
        }
        
        @keyframes progressShine {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        
        .progress-description {
            margin-top: 10px;
            font-size: 14px;
            color: #718096;
        }
        </style>
        """
        
        html_parts = [base_style]
        html_parts.append('<div class="gamification-section">')
        
        if not user_account_exists:
            # User doesn't have an account - encourage registration
            html_parts.extend([
                '<div class="gamification-header-wrapper">',
                '<div class="gamification-header">🎮 Unlock Event Rewards</div>',
                '<div class="gamification-subtitle">Join our exclusive rewards program</div>',
                '</div>',
                '<div class="gamification-content">',
                '<div class="account-prompt">',
                '<p style="font-size: 18px; font-weight: 600; color: #2d3748; margin-bottom: 15px;">Start earning points and badges today!</p>',
                '<p>Track your attendance, collect achievement badges, and compete with other attendees on our leaderboard.</p>',
                '<div style="text-align: center; margin: 25px 0;">',
                f'<a href="/api/auth/register-page/?email={invitation.guest_email}&next=/tickets/{invitation.id}/" class="register-btn">Create Your Account</a>',
                '</div>',
                '</div>',
                '<div class="feature-list">',
                '<div class="feature-item">',
                '<span class="feature-icon">🏆</span>',
                '<span>Earn exclusive badges for achievements</span>',
                '</div>',
                '<div class="feature-item">',
                '<span class="feature-icon">📊</span>',
                '<span>Track your progress on live leaderboards</span>',
                '</div>',
                '<div class="feature-item">',
                '<span class="feature-icon">🔥</span>',
                '<span>Build attendance streaks for bonus rewards</span>',
                '</div>',
                '<div class="feature-item">',
                '<span class="feature-icon">🎯</span>',
                '<span>Complete challenges and unlock special perks</span>',
                '</div>',
                '</div>',
                '</div>'
            ])
        elif not is_authenticated:
            # User has account but not logged in
            html_parts.extend([
                '<div class="gamification-header-wrapper">',
                '<div class="gamification-header">🔐 Welcome Back!</div>',
                '<div class="gamification-subtitle">Login to view your rewards</div>',
                '</div>',
                '<div class="gamification-content">',
                '<div class="account-prompt">',
                '<p style="font-size: 18px; font-weight: 600; color: #2d3748; margin-bottom: 15px;">Your account is waiting!</p>',
                '<p>Access your points, badges, and attendance streak by logging in.</p>',
                '<div style="text-align: center; margin: 25px 0;">',
                f'<a href="/api/auth/login-page/?email={invitation.guest_email}&next=/tickets/{invitation.id}/" class="login-btn">Login to Your Account</a>',
                '</div>',
                '</div>',
                '</div>'
            ])
        elif user_stats:
            # User is logged in and has stats
            profile = user_stats['profile']
            badges = user_stats['badges']
            
            html_parts.extend([
                '<div class="gamification-header-wrapper">',
                '<div class="gamification-header">🎮 Your Event Dashboard</div>',
                '<div class="gamification-subtitle">Track your achievements and progress</div>',
                '</div>',
                '<div class="gamification-content">',
                '<div class="user-stats">',
                f'<div class="stat-card">',
                f'<div class="stat-number">{profile.total_points}</div>',
                f'<div class="stat-label">Total Points</div>',
                f'</div>',
                f'<div class="stat-card">',
                f'<div class="stat-number">{profile.current_streak}<span style="margin-left: 5px;">🔥</span></div>',
                f'<div class="stat-label">Day Streak</div>',
                f'</div>',
                f'<div class="stat-card">',
                f'<div class="stat-number">{profile.total_events_attended}</div>',
                f'<div class="stat-label">Events</div>',
                f'</div>',
                f'<div class="stat-card">',
                f'<div class="stat-number">{profile.level}</div>',
                f'<div class="stat-label">Level</div>',
                f'</div>',
                '</div>'
            ])
            
            if badges.exists():
                html_parts.extend([
                    '<div class="badges-container">',
                    '<div class="badges-title">Your Achievements</div>',
                    '<div class="badges">'
                ])
                for user_badge in badges[:5]:  # Show first 5 badges
                    html_parts.append(f'<div class="badge"><span class="badge-tooltip">{user_badge.badge.name}</span>{user_badge.badge.icon}</div>')
                if badges.count() > 5:
                    html_parts.append(f'<div class="badge">+{badges.count() - 5}</div>')
                html_parts.extend(['</div>', '</div>'])
            
            # Next badge progress
            if user_stats.get('next_badge'):
                next_badge_data = user_stats['next_badge']
                if next_badge_data is None:
                    # No next badge available
                    pass
                elif isinstance(next_badge_data, dict) and 'badge' in next_badge_data:
                    next_badge = next_badge_data['badge']
                    progress = next_badge_data['progress']
                    
                    html_parts.extend([
                        '<div class="progress-container">',
                        '<div class="progress-header">',
                        f'<div class="progress-title">{next_badge.icon} Next: {next_badge.name}</div>',
                        f'<div class="progress-percentage">{progress:.0f}%</div>',
                        '</div>',
                        '<div class="progress-bar-wrapper">',
                        f'<div class="progress-bar" style="width: {progress:.1f}%;"></div>',
                        '</div>',
                        f'<div class="progress-description">{next_badge.description}</div>',
                        '</div>'
                    ])
                elif next_badge_data:
                    # Handle case where next_badge is the badge object directly
                    next_badge = next_badge_data
                    progress = 0
                    
                    html_parts.extend([
                        '<div class="progress-container">',
                        '<div class="progress-header">',
                        f'<div class="progress-title">{next_badge.icon} Next: {next_badge.name}</div>',
                        f'<div class="progress-percentage">{progress:.0f}%</div>',
                        '</div>',
                        '<div class="progress-bar-wrapper">',
                        f'<div class="progress-bar" style="width: {progress:.1f}%;"></div>',
                        '</div>',
                        f'<div class="progress-description">{next_badge.description}</div>',
                        '</div>'
                    ])
            
            html_parts.append('</div>')  # Close gamification-content
        
        html_parts.append('</div>')  # Close gamification-section
        return ''.join(html_parts)
    
    def _generate_networking_html(self, invitation, user_account_exists: bool, user_stats: dict, is_authenticated: bool) -> str:
        """Generate HTML section for networking features."""
        if not invitation.guest_email:
            return ""
        
        # Check if networking is enabled for this event
        try:
            networking_settings = getattr(invitation.event, 'networking_settings', None)
            if not networking_settings or not networking_settings.enable_networking:
                return ""  # Networking not enabled for this event
        except Exception as e:
            logger.warning(f"Could not check networking settings: {e}")
            return ""
        
        base_style = """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        
        .networking-section {
            margin: 40px auto;
            max-width: 800px;
            padding: 0;
            background: #ffffff;
            border-radius: 20px;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            box-shadow: 0 20px 60px rgba(0,0,0,0.1);
            overflow: hidden;
            animation: slideUp 0.5s ease-out;
        }
        
        .networking-header-wrapper {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            padding: 30px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .networking-header-wrapper::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: shimmer 3s infinite;
        }
        
        .networking-header {
            color: white;
            font-size: 28px;
            font-weight: 700;
            margin: 0;
            position: relative;
            z-index: 1;
            letter-spacing: -0.5px;
        }
        
        .networking-subtitle {
            color: rgba(255,255,255,0.9);
            font-size: 16px;
            margin-top: 8px;
            font-weight: 400;
        }
        
        .networking-content {
            padding: 40px;
        }
        
        .networking-features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        
        .feature-card {
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border: 1px solid #e2e8f0;
            transition: all 0.3s ease;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(99,102,241,0.15);
            border-color: #6366f1;
        }
        
        .feature-icon {
            font-size: 32px;
            margin-bottom: 12px;
            display: block;
        }
        
        .feature-title {
            font-size: 16px;
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 8px;
        }
        
        .feature-desc {
            font-size: 14px;
            color: #64748b;
            line-height: 1.4;
        }
        
        .networking-actions {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            justify-content: center;
            margin-top: 30px;
        }
        
        .networking-btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            font-size: 14px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .networking-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(99,102,241,0.4);
            color: white;
            text-decoration: none;
        }
        
        .networking-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s;
        }
        
        .networking-btn:hover::before {
            left: 100%;
        }
        
        .networking-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 20px;
            margin: 30px 0;
            padding: 25px;
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            border-radius: 16px;
            border: 1px solid #0ea5e9;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-number {
            font-size: 24px;
            font-weight: 700;
            color: #0ea5e9;
            margin-bottom: 5px;
        }
        
        .stat-label {
            font-size: 12px;
            color: #64748b;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        @media (max-width: 640px) {
            .networking-section { margin: 20px 10px; }
            .networking-content { padding: 25px 20px; }
            .networking-features { grid-template-columns: 1fr; }
            .networking-actions { flex-direction: column; align-items: stretch; }
            .networking-btn { justify-content: center; }
        }
        </style>
        """
        
        html_parts = [base_style]
        html_parts.append('<div class="networking-section">')
        
        if not user_account_exists:
            # User doesn't have an account - encourage registration for networking
            html_parts.extend([
                '<div class="networking-header-wrapper">',
                '<div class="networking-header">🤝 Connect & Network</div>',
                '<div class="networking-subtitle">Join to unlock professional networking</div>',
                '</div>',
                '<div class="networking-content">',
                '<div class="feature-card" style="margin: 0; max-width: none;">',
                '<div class="feature-icon">🌐</div>',
                '<div class="feature-title">Professional Networking Awaits</div>',
                '<p style="color: #64748b; margin: 15px 0;">Create your account to connect with other attendees, exchange contacts via QR codes, and build your professional network.</p>',
                '<div style="margin-top: 25px;">',
                f'<a href="/api/auth/register-page/?email={invitation.guest_email}&next=/tickets/{invitation.id}/" class="networking-btn">',
                '<span>🚀</span> Join & Start Networking',
                '</a>',
                '</div>',
                '</div>',
                '</div>'
            ])
        elif not is_authenticated:
            # User has account but not logged in
            html_parts.extend([
                '<div class="networking-header-wrapper">',
                '<div class="networking-header">🤝 Welcome Back!</div>',
                '<div class="networking-subtitle">Login to access networking features</div>',
                '</div>',
                '<div class="networking-content">',
                '<div class="feature-card" style="margin: 0; max-width: none;">',
                '<div class="feature-icon">🔐</div>',
                '<div class="feature-title">Your Networking Profile Awaits</div>',
                '<p style="color: #64748b; margin: 15px 0;">Access your networking QR code, browse attendee directory, and manage your professional connections.</p>',
                '<div style="margin-top: 25px;">',
                f'<a href="/api/auth/login-page/?email={invitation.guest_email}&next=/tickets/{invitation.id}/" class="networking-btn">',
                '<span>🔑</span> Login to Network',
                '</a>',
                '</div>',
                '</div>',
                '</div>'
            ])
        else:
            # User is logged in - show full networking features
            try:
                from django.contrib.auth.models import User
                from networking.models import NetworkingProfile, Connection
                from django.db import models
                
                user = User.objects.get(email=invitation.guest_email)
                profile, created = NetworkingProfile.objects.get_or_create(
                    user=user,
                    defaults={'visible_in_directory': True, 'allow_contact_sharing': True}
                )
                
                # Get networking stats
                connections_count = Connection.objects.filter(
                    models.Q(from_user=user) | models.Q(to_user=user),
                    event=invitation.event
                ).count()
                
                total_connections = Connection.objects.filter(
                    models.Q(from_user=user) | models.Q(to_user=user)
                ).count()
                
                html_parts.extend([
                    '<div class="networking-header-wrapper">',
                    '<div class="networking-header">🤝 Networking Hub</div>',
                    '<div class="networking-subtitle">Connect with fellow attendees</div>',
                    '</div>',
                    '<div class="networking-content">'
                ])
                
                # Show networking stats if user has connections
                if total_connections > 0:
                    html_parts.extend([
                        '<div class="networking-stats">',
                        '<div class="stat-item">',
                        f'<div class="stat-number">{total_connections}</div>',
                        '<div class="stat-label">Total Connections</div>',
                        '</div>',
                        '<div class="stat-item">',
                        f'<div class="stat-number">{connections_count}</div>',
                        '<div class="stat-label">This Event</div>',
                        '</div>',
                        '<div class="stat-item">',
                        f'<div class="stat-number">{total_connections * 5}</div>',
                        '<div class="stat-label">Points Earned</div>',
                        '</div>',
                        '</div>'
                    ])
                
                # Networking features
                html_parts.extend([
                    '<div class="networking-features">',
                    '<div class="feature-card">',
                    '<div class="feature-icon">📱</div>',
                    '<div class="feature-title">My QR Code</div>',
                    '<div class="feature-desc">Get your networking QR code for instant connections</div>',
                    '</div>',
                    '<div class="feature-card">',
                    '<div class="feature-icon">👥</div>',
                    '<div class="feature-title">Attendee Directory</div>',
                    '<div class="feature-desc">Browse and connect with other attendees</div>',
                    '</div>',
                    '<div class="feature-card">',
                    '<div class="feature-icon">🔗</div>',
                    '<div class="feature-title">My Connections</div>',
                    '<div class="feature-desc">View and manage your professional network</div>',
                    '</div>',
                    '<div class="feature-card">',
                    '<div class="feature-icon">⚙️</div>',
                    '<div class="feature-title">Profile Settings</div>',
                    '<div class="feature-desc">Update your networking preferences</div>',
                    '</div>',
                    '</div>'
                ])
                
                # Action buttons
                html_parts.extend([
                    '<div class="networking-actions">',
                    f'<a href="/networking/qr-code/{user.id}/{invitation.event.id}/" class="networking-btn">',
                    '<span>📱</span> Get My QR Code',
                    '</a>',
                    f'<a href="/networking/directory/{invitation.event.id}/" class="networking-btn">',
                    '<span>👥</span> Browse Attendees',
                    '</a>',
                    f'<a href="/networking/connections/{invitation.event.id}/" class="networking-btn">',
                    '<span>🔗</span> My Connections',
                    '</a>',
                    f'<a href="/networking/profile/{user.id}/{invitation.event.id}/" class="networking-btn">',
                    '<span>👤</span> My Profile',
                    '</a>',
                    '</div>'
                ])
                
                html_parts.append('</div>')  # Close networking-content
                
            except Exception as e:
                logger.error(f"Error generating networking features: {e}")
                # Fallback to basic message
                html_parts.extend([
                    '<div class="networking-header-wrapper">',
                    '<div class="networking-header">🤝 Networking Available</div>',
                    '</div>',
                    '<div class="networking-content">',
                    '<p style="text-align: center; color: #64748b;">Networking features are enabled for this event. Connect with other attendees!</p>',
                    '</div>'
                ])
        
        html_parts.append('</div>')  # Close networking-section
        return ''.join(html_parts)
    
    def _generate_feedback_html(self, invitation, is_event_ended=False):
        """Generate HTML section for event feedback."""
        from datetime import datetime
        from django.utils import timezone
        
        # Check if event has ended (allow feedback 1 hour after event end)
        if not is_event_ended:
            event_end = invitation.event.get_start_datetime()
            if event_end:
                # Assuming events last 4 hours on average
                estimated_end = event_end + timezone.timedelta(hours=4)
                is_event_ended = timezone.now() > estimated_end
        
        # Check if feedback already submitted
        has_feedback = False
        if invitation.guest_email:
            from feedback_system.models import EventFeedback
            has_feedback = EventFeedback.objects.filter(
                event=invitation.event,
                respondent_email=invitation.guest_email
            ).exists()
        
        if not invitation.guest_email:
            return ""  # No feedback without email
        
        base_style = """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        
        .feedback-section {
            margin: 40px auto;
            max-width: 800px;
            padding: 0;
            background: #ffffff;
            border-radius: 20px;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            box-shadow: 0 20px 60px rgba(0,0,0,0.1);
            overflow: hidden;
            animation: slideUp 0.5s ease-out;
        }
        
        .feedback-header-wrapper {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            padding: 30px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .feedback-header-wrapper::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: shimmer 3s infinite;
        }
        
        .feedback-header {
            color: white;
            font-size: 28px;
            font-weight: 700;
            margin: 0;
            position: relative;
            z-index: 1;
            letter-spacing: -0.5px;
        }
        
        .feedback-subtitle {
            color: rgba(255,255,255,0.9);
            font-size: 16px;
            margin-top: 8px;
            font-weight: 400;
        }
        
        .feedback-content {
            padding: 30px;
        }
        
        .feedback-prompt {
            background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
            padding: 25px;
            border-radius: 16px;
            margin-bottom: 20px;
            border: 1px solid rgba(16,185,129,0.1);
        }
        
        .feedback-prompt p {
            color: #2d3748;
            line-height: 1.6;
            margin: 10px 0;
        }
        
        .points-breakdown {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        
        .points-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px;
            background: white;
            border-radius: 10px;
            border: 1px solid #e5e7eb;
            transition: all 0.3s ease;
        }
        
        .points-item:hover {
            transform: translateX(5px);
            border-color: #10b981;
            box-shadow: 0 5px 15px rgba(16,185,129,0.1);
        }
        
        .points-icon {
            font-size: 20px;
            width: 30px;
            text-align: center;
        }
        
        .points-text {
            flex: 1;
            color: #4a5568;
            font-size: 14px;
        }
        
        .points-value {
            font-weight: 600;
            color: #10b981;
            font-size: 16px;
        }
        
        .feedback-btn {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 16px 32px;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            margin: 10px 5px;
            text-decoration: none;
            display: inline-block;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(16,185,129,0.3);
            position: relative;
            overflow: hidden;
        }
        
        .feedback-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s;
        }
        
        .feedback-btn:hover::before {
            left: 100%;
        }
        
        .feedback-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(16,185,129,0.4);
            color: white;
            text-decoration: none;
        }
        
        .feedback-completed-card {
            background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
            border-radius: 16px;
            padding: 30px;
            text-align: center;
            border: 2px solid #10b981;
        }
        
        .feedback-completed-icon {
            font-size: 64px;
            margin-bottom: 20px;
            animation: bounce 1s ease-out;
        }
        
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-20px); }
        }
        
        .feedback-completed-title {
            font-size: 24px;
            font-weight: 700;
            color: #059669;
            margin-bottom: 10px;
        }
        
        .feedback-completed-message {
            color: #4a5568;
            font-size: 16px;
            line-height: 1.6;
        }
        
        .feedback-pending-card {
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            border-radius: 16px;
            padding: 25px;
            text-align: center;
            border: 1px solid rgba(245,158,11,0.2);
        }
        
        .feedback-pending-icon {
            font-size: 48px;
            margin-bottom: 15px;
        }
        
        .feedback-pending-title {
            font-size: 20px;
            font-weight: 600;
            color: #92400e;
            margin-bottom: 10px;
        }
        
        .feedback-pending-message {
            color: #78350f;
            font-size: 15px;
            line-height: 1.5;
        }
        </style>
        """
        
        html_parts = [base_style]
        html_parts.append('<div class="feedback-section">')
        
        if has_feedback:
            # Already submitted feedback
            html_parts.extend([
                '<div class="feedback-header-wrapper">',
                '<div class="feedback-header">✅ Feedback Complete</div>',
                '<div class="feedback-subtitle">Thank you for your valuable input</div>',
                '</div>',
                '<div class="feedback-content">',
                '<div class="feedback-completed-card">',
                '<div class="feedback-completed-icon">🎉</div>',
                '<div class="feedback-completed-title">Your Feedback Has Been Received!</div>',
                '<div class="feedback-completed-message">',
                '<p>Thank you for taking the time to share your experience.</p>',
                '<p>Your feedback helps us create better events in the future.</p>',
                '<p style="margin-top: 15px; color: #10b981; font-weight: 600;">🎮 You earned gamification points for your feedback!</p>',
                '</div>',
                '</div>',
                '</div>'
            ])
        elif not is_event_ended:
            # Event hasn't ended yet
            html_parts.extend([
                '<div class="feedback-header-wrapper">',
                '<div class="feedback-header">📝 Feedback Coming Soon</div>',
                '<div class="feedback-subtitle">Share your experience after the event</div>',
                '</div>',
                '<div class="feedback-content">',
                '<div class="feedback-pending-card">',
                '<div class="feedback-pending-icon">⏰</div>',
                '<div class="feedback-pending-title">Feedback Opens After Event</div>',
                '<div class="feedback-pending-message">',
                '<p>We hope you\'re enjoying the event!</p>',
                '<p>You\'ll be able to share your feedback once the event concludes.</p>',
                '<p style="margin-top: 15px;">💡 <strong>Pro tip:</strong> Complete your feedback to earn bonus gamification points!</p>',
                '</div>',
                '</div>',
                '</div>'
            ])
        else:
            # Event ended, show feedback form
            feedback_url = f"/api/feedback/feedback/?event_id={invitation.event.id}&invitation_id={invitation.id}&email={invitation.guest_email}"
            html_parts.extend([
                '<div class="feedback-header-wrapper">',
                '<div class="feedback-header">📝 Share Your Experience</div>',
                '<div class="feedback-subtitle">Help us improve future events</div>',
                '</div>',
                '<div class="feedback-content">',
                '<div class="feedback-prompt">',
                '<p style="font-size: 18px; font-weight: 600; color: #2d3748; margin-bottom: 15px;">Your feedback matters to us!</p>',
                '<p>Take a moment to share your thoughts and earn rewards.</p>',
                '</div>',
                '<div class="points-breakdown">',
                '<div class="points-item">',
                '<span class="points-icon">⭐</span>',
                '<span class="points-text">Overall rating</span>',
                '<span class="points-value">15 pts</span>',
                '</div>',
                '<div class="points-item">',
                '<span class="points-icon">✍️</span>',
                '<span class="points-text">Detailed comments</span>',
                '<span class="points-value">+5 pts</span>',
                '</div>',
                '<div class="points-item">',
                '<span class="points-icon">🚀</span>',
                '<span class="points-text">NPS promoter</span>',
                '<span class="points-value">+5 pts</span>',
                '</div>',
                '<div class="points-item">',
                '<span class="points-icon">👍</span>',
                '<span class="points-text">Would recommend</span>',
                '<span class="points-value">+3 pts</span>',
                '</div>',
                '</div>',
                '<div style="text-align: center; margin-top: 25px;">',
                f'<a href="#" onclick="openFeedbackForm()" class="feedback-btn">Share Your Feedback</a>',
                '</div>',
                '</div>',
                '''
                <script>
                function openFeedbackForm() {
                    // Create and show feedback modal/form
                    showFeedbackModal();
                }
                
                function showFeedbackModal() {
                    // Simple modal implementation
                    const modal = document.createElement('div');
                    modal.style.cssText = `
                        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                        background: rgba(0,0,0,0.8); z-index: 1000; padding: 20px;
                        display: flex; align-items: center; justify-content: center;
                    `;
                    
                    modal.innerHTML = `
                        <div style="background: white; padding: 30px; border-radius: 10px; max-width: 500px; width: 100%; max-height: 90vh; overflow-y: auto;">
                            <h2 style="color: #333; margin-bottom: 20px;">📝 Event Feedback</h2>
                            <form id="feedbackForm">
                                <div style="margin-bottom: 15px;">
                                    <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #333;">Overall Rating:</label>
                                    <select name="overall_rating" required style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;">
                                        <option value="">Select rating...</option>
                                        <option value="5">⭐⭐⭐⭐⭐ Excellent</option>
                                        <option value="4">⭐⭐⭐⭐ Good</option>
                                        <option value="3">⭐⭐⭐ Average</option>
                                        <option value="2">⭐⭐ Poor</option>
                                        <option value="1">⭐ Very Poor</option>
                                    </select>
                                </div>
                                
                                <div style="margin-bottom: 15px;">
                                    <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #333;">What went well? (+5 bonus points)</label>
                                    <textarea name="what_went_well" rows="3" style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;" placeholder="Tell us what you enjoyed most..."></textarea>
                                </div>
                                
                                <div style="margin-bottom: 15px;">
                                    <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #333;">What could be improved? (+5 bonus points)</label>
                                    <textarea name="what_needs_improvement" rows="3" style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;" placeholder="How can we make future events better?"></textarea>
                                </div>
                                
                                <div style="margin-bottom: 15px;">
                                    <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #333;">Would you recommend this event?</label>
                                    <select name="would_recommend" style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;">
                                        <option value="">Select...</option>
                                        <option value="true">👍 Yes (+3 bonus points)</option>
                                        <option value="false">👎 No</option>
                                    </select>
                                </div>
                                
                                <div style="text-align: center; margin-top: 20px;">
                                    <button type="button" onclick="submitFeedback()" style="background: #10b981; color: white; padding: 12px 24px; border: none; border-radius: 6px; margin-right: 10px; cursor: pointer;">
                                        Submit Feedback
                                    </button>
                                    <button type="button" onclick="closeFeedbackModal()" style="background: #6b7280; color: white; padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer;">
                                        Cancel
                                    </button>
                                </div>
                            </form>
                        </div>
                    `;
                    
                    document.body.appendChild(modal);
                    modal.onclick = function(e) {
                        if (e.target === modal) closeFeedbackModal();
                    };
                }
                
                function closeFeedbackModal() {
                    const modal = document.querySelector('div[style*="position: fixed"]');
                    if (modal) modal.remove();
                }
                
                function submitFeedback() {
                    const form = document.getElementById('feedbackForm');
                    const formData = new FormData(form);
                    
                    // Convert to JSON
                    const data = {
                        event: ''' + str(invitation.event.id) + f''',
                        invitation: "{invitation.id}",
                        respondent_email: "{invitation.guest_email}",
                        respondent_name: "{invitation.guest_name}",
                        overall_rating: parseInt(formData.get('overall_rating')),
                        what_went_well: formData.get('what_went_well'),
                        what_needs_improvement: formData.get('what_needs_improvement'),
                        would_recommend: formData.get('would_recommend') === 'true',
                        submission_source: 'ticket'
                    }};
                    
                    // Submit to API
                    fetch('/api/feedback/feedback/', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify(data)
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        alert('Thank you for your feedback! You earned gamification points.');
                        closeFeedbackModal();
                        location.reload(); // Refresh to show updated stats
                    }})
                    .catch(error => {{
                        console.error('Error:', error);
                        alert('There was an error submitting your feedback. Please try again.');
                    }});
                }}
                </script>
                '''
            ])
        
        html_parts.append('</div>')
        return ''.join(html_parts)
    
    def perform_create(self, serializer):
        """Override create to send email with ticket."""
        invitation = None
        try:
            logger.info("Starting invitation creation process")
            
            # Save the invitation to database first
            invitation = serializer.save()
            logger.info(f"✅ Successfully created invitation {invitation.id} in database")
            
            # Verify the invitation exists in database
            if not Invitation.objects.filter(id=invitation.id).exists():
                logger.error(f"❌ CRITICAL: Invitation {invitation.id} was not saved to database!")
                raise ValueError(f"Invitation {invitation.id} was not saved to database")
            
            logger.info(f"✅ Verified invitation {invitation.id} exists in database")
            
            # Check if tickets were generated during save
            if not invitation.ticket_html or not invitation.ticket_pdf:
                logger.info(f"Tickets not found for invitation {invitation.id}, generating them now")
                try:
                    invitation.generate_tickets()
                    invitation.save()
                    logger.info(f"✅ Tickets generated for invitation {invitation.id}")
                except Exception as e:
                    logger.error(f"❌ Failed to generate tickets for invitation {invitation.id}: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    # Don't fail the entire creation just because tickets failed
            else:
                logger.info(f"✅ Tickets already exist for invitation {invitation.id}")
            
            # Send email if guest has email address
            if invitation.guest_email:
                logger.info(f"Invitation has email ({invitation.guest_email}), sending email...")
                
                try:
                    # Use the existing endpoint to send the email
                    self.get_object = lambda: invitation  # Temporarily set get_object to return our invitation
                    response = self.send_email(request=None, pk=invitation.id)
                    if response.status_code >= 400:
                        logger.error(f"❌ Failed to send email: {response.data}")
                    else:
                        logger.info(f"✅ Email sent successfully to {invitation.guest_email}")
                except Exception as e:
                    logger.error(f"❌ Failed to send invitation email: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    # Don't fail the entire creation just because email failed
            else:
                logger.info(f"No email address provided for invitation {invitation.id}, skipping email")
                
            logger.info(f"✅ Invitation creation process completed successfully for {invitation.id}")
            return invitation
            
        except Exception as e:
            logger.error(f"❌ CRITICAL ERROR in invitation creation: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            # If we have an invitation ID, log its status
            if invitation and hasattr(invitation, 'id'):
                exists = Invitation.objects.filter(id=invitation.id).exists()
                logger.error(f"Invitation {invitation.id} exists in database: {exists}")
            
            # Re-raise the exception so the API returns an error
            raise
    
    def get_queryset(self):
        """
        Filter invitations to only show those for events the user owns,
        or all invitations if the user is staff.
        For view_ticket action, allow access to all invitations for anonymous users.
        """
        user = self.request.user
        
        # For view_ticket action, allow anonymous users to access any invitation
        if self.action == 'view_ticket':
            return Invitation.objects.all()
        
        # Handle anonymous users (return empty queryset to prevent errors for other actions)
        if not user.is_authenticated:
            return Invitation.objects.none()
        
        # Staff can see all invitations
        if user.is_staff:
            queryset = Invitation.objects.all()
        else:
            # Regular users can only see invitations for events they own
            queryset = Invitation.objects.filter(event__owner=user)
            
        # Filter by event_id if provided
        event_id = self.request.query_params.get('event_id')
        if event_id:
            queryset = queryset.filter(event_id=event_id)
            
        return queryset
    
    @action(detail=True, methods=['get'])
    def qr_code(self, request, pk=None):
        invitation = self.get_object()
        if invitation.qr_code:
            qr_url = request.build_absolute_uri(invitation.qr_code.url)
            return Response({'qr_code_url': qr_url})
        return Response({'error': 'QR code not found'}, status=404)
    
    @action(detail=True, methods=['get'])
    def ticket_html(self, request, pk=None):
        """Get HTML ticket for an invitation."""
        invitation = self.get_object()
        if invitation.ticket_html:
            html_url = request.build_absolute_uri(invitation.ticket_html.url)
            return Response({'ticket_html_url': html_url})
        return Response({'error': 'HTML ticket not found'}, status=404)

    @action(detail=True, methods=['get'])
    def ticket_pdf(self, request, pk=None):
        """Get PDF ticket for an invitation."""
        invitation = self.get_object()
        if invitation.ticket_pdf:
            pdf_url = request.build_absolute_uri(invitation.ticket_pdf.url)
            return Response({'ticket_pdf_url': pdf_url})
        return Response({'error': 'PDF ticket not found'}, status=404)

    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def view_ticket(self, request, pk=None):
        """View HTML ticket directly with gamification info."""
        # Directly get the invitation by UUID without permission checks
        # since we allow anyone with the link to view the ticket
        try:
            invitation = Invitation.objects.get(pk=pk)
        except Invitation.DoesNotExist:
            return Response({'error': 'Ticket not found'}, status=404)
        
        # Gamification logic: only do database queries for authenticated users
        user_stats = None
        user_account_exists = False
        invitation_user = None
        
        # First check: is the current viewer authenticated?
        viewer_is_authenticated = (hasattr(request, 'user') and 
                                 request.user.is_authenticated and 
                                 hasattr(request.user, 'id'))
        
        if invitation.guest_email:
            from django.contrib.auth.models import User
            try:
                # Find the user account for this invitation's email
                invitation_user = User.objects.get(email=invitation.guest_email)
                user_account_exists = True
                
                # Only get stats if viewer is authenticated AND is the same user
                logger.info(f"Viewer authenticated: {viewer_is_authenticated}")
                if viewer_is_authenticated:
                    logger.info(f"Request user: {request.user.username} (email: {request.user.email})")
                    logger.info(f"Invitation user: {invitation_user.username} (email: {invitation_user.email})")
                    logger.info(f"Users match: {request.user == invitation_user}")
                
                # Check if the emails match (more reliable than username comparison)
                if (viewer_is_authenticated and 
                    (request.user == invitation_user or request.user.email == invitation.guest_email)):
                    try:
                        from gamification.services import GamificationStatsService
                        service = GamificationStatsService()
                        # Safe to call because we know request.user is authenticated
                        user_stats = service.get_user_stats(request.user)
                        logger.info(f"Got user stats: {user_stats is not None}")
                    except Exception as e:
                        logger.error(f"Failed to get gamification stats: {e}")
                        user_stats = None
                        
            except User.DoesNotExist:
                # No user account exists for this email
                pass
            except Exception as e:
                logger.error(f"Error checking user account: {e}")
        
        if invitation.ticket_html:
            with invitation.ticket_html.open('r') as f:
                content = f.read()
                # Handle both bytes and string content
                if isinstance(content, bytes):
                    html_content = content.decode('utf-8')
                else:
                    html_content = content
                
            # For direct browser viewing, we need to make sure QR code is visible
            # Try to regenerate and embed QR code directly into the HTML
            qr_code_data_uri = invitation.get_qr_code_base64()
            
            if qr_code_data_uri:
                logger.info(f"Generated base64 QR code for viewing ticket {invitation.id}")
                # Try to replace the QR code image with our data URI version
                if invitation.qr_code and invitation.qr_code.url:
                    qr_code_url = invitation.qr_code.url
                    if qr_code_url.startswith('/'):
                        from django.conf import settings
                        base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
                        absolute_qr_url = f"{base_url}{qr_code_url}"
                        # Replace the URL with our data URI
                        html_content = html_content.replace(f'src="{qr_code_url}"', f'src="{qr_code_data_uri}"')
                        html_content = html_content.replace(f'src="{absolute_qr_url}"', f'src="{qr_code_data_uri}"')
            else:
                # Fallback to making URLs absolute
                logger.warning(f"Could not generate QR code data URI for ticket {invitation.id}, using URL fallback")
                if invitation.qr_code and invitation.qr_code.url:
                    from django.conf import settings
                    base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
                    qr_code_url = invitation.qr_code.url
                    if qr_code_url.startswith('/'):
                        absolute_qr_url = f"{base_url}{qr_code_url}"
                        # Replace relative URL with absolute URL in the HTML
                        html_content = html_content.replace(f'src="{qr_code_url}"', f'src="{absolute_qr_url}"')
            
            # Add gamification section to the HTML
            try:
                # Simple logic: show stats if we have them, otherwise show prompts
                is_viewing_own_ticket = (user_stats is not None)
                
                logger.info(f"=== GAMIFICATION HTML GENERATION ===")
                logger.info(f"User account exists: {user_account_exists}")
                logger.info(f"User stats available: {user_stats is not None}")
                logger.info(f"Is viewing own ticket: {is_viewing_own_ticket}")
                logger.info(f"Viewer is authenticated: {viewer_is_authenticated}")
                
                gamification_html = self._generate_gamification_html(
                    invitation, user_account_exists, user_stats, is_viewing_own_ticket
                )
                
                # Insert gamification section before the closing body tag
                if '</body>' in html_content:
                    html_content = html_content.replace('</body>', f'{gamification_html}</body>')
                else:
                    html_content += gamification_html
            except Exception as e:
                logger.error(f"Gamification HTML generation failed: {e}")
                # Continue without gamification section
            
            # Add networking section to the HTML
            try:
                networking_html = self._generate_networking_html(invitation, user_account_exists, user_stats, is_viewing_own_ticket)
                
                # Insert networking section before the closing body tag
                if '</body>' in html_content:
                    html_content = html_content.replace('</body>', f'{networking_html}</body>')
                else:
                    html_content += networking_html
            except Exception as e:
                logger.error(f"Networking HTML generation failed: {e}")
                # Continue without networking section
            
            # Add feedback section to the HTML
            try:
                feedback_html = self._generate_feedback_html(invitation)
                
                # Insert feedback section before the closing body tag
                if '</body>' in html_content:
                    html_content = html_content.replace('</body>', f'{feedback_html}</body>')
                else:
                    html_content += feedback_html
            except Exception as e:
                logger.error(f"Feedback HTML generation failed: {e}")
                # Continue without feedback section
                        
            return HttpResponse(html_content)
        return Response({'error': 'Ticket not found'}, status=404)
    
    @action(detail=True, methods=['post'])
    def send_email(self, request, pk=None):
        """Manually send email with ticket for an invitation."""
        logger.info("=== SEND_EMAIL ACTION CALLED ===")
        invitation = self.get_object()
        logger.info(f"Invitation retrieved: {invitation.id}")
        if not invitation.guest_email:
            logger.error(f"No guest email for invitation {invitation.id}")
            return Response(
                {'error': 'Invitation has no email address'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logger.info(f"=== MANUAL EMAIL REQUEST for invitation {invitation.id} to {invitation.guest_email} ===")
        
        # Check if we have ticket files
        if not invitation.ticket_html and not invitation.ticket_pdf:
            logger.info(f"No tickets found for invitation {invitation.id}, generating them now")
            try:
                invitation.generate_tickets()
                invitation.save()
                logger.info(f"Tickets generated for invitation {invitation.id}")
            except Exception as e:
                logger.error(f"Failed to generate tickets for invitation {invitation.id}: {str(e)}")
        
        # Verify email configuration
        if settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
            if not settings.EMAIL_HOST or not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
                error_msg = "SMTP email settings are incomplete. Check EMAIL_HOST, EMAIL_HOST_USER, and EMAIL_HOST_PASSWORD."
                logger.error(error_msg)
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
        try:
            # Get the event details
            event = invitation.event
            
            # Build base URL for links - using a default for development
            base_url = settings.BASE_URL if hasattr(settings, 'BASE_URL') else "http://localhost:8000"
            
            # Get ticket URLs
            ticket_view_url = f"{base_url}/tickets/{invitation.id}/"
            
            # Email subject
            subject = f"Your Ticket for {event.name}"
            
            # Plain text message
            message = f"""
            Hello {invitation.guest_name},
            
            Your ticket for {event.name} is ready.
            
            Event Details:
            - Date: {event.date}
            - Time: {event.time}
            - Location: {event.location}
            
            We've attached a PDF version of your ticket to this email that you can download, print, or keep on your device.
            
            Please bring your ticket with the QR code to the event for quick check-in.
            You can view your ticket online at: {ticket_view_url}
            
            Thank you!
            """
            
            # Get QR code URL and data URI for embedding in email
            qr_code_url = None
            
            # Use the helper method to get a base64 encoded QR code
            qr_code_data_uri = invitation.get_qr_code_base64()
            if qr_code_data_uri:
                logger.info(f"Successfully created QR code data URI for email for invitation {invitation.id}")
            else:
                logger.warning(f"Could not create QR code data URI for email for invitation {invitation.id}")
            
            # Always set up URL as fallback
            if invitation.qr_code:
                qr_code_url = invitation.qr_code.url
                if qr_code_url.startswith('/'):
                    qr_code_url = f"{base_url}{qr_code_url}"
                logger.info(f"Using fallback QR code URL for email: {qr_code_url}")
                    
            # HTML message with embedded ticket
            html_message = f"""
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{ font-family: 'Helvetica', 'Arial', sans-serif; margin: 0; padding: 0; color: #333; background-color: #f9f9f9; }}
                    .email-container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .email-header {{ background: linear-gradient(135deg, #4f46e5 0%, #2e27c0 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .email-header h1 {{ margin: 0; font-size: 24px; font-weight: 700; }}
                    .email-content {{ background-color: #ffffff; padding: 30px; border-radius: 0 0 8px 8px; }}
                    .email-footer {{ margin-top: 20px; text-align: center; font-size: 12px; color: #888; }}
                    .email-greeting {{ margin-bottom: 25px; font-size: 16px; }}
                    
                    /* Ticket styles */
                    .ticket {{ background-color: white; border-radius: 16px; overflow: hidden; box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1); margin: 25px 0; border: 1px solid #e5e5e5; }}
                    .ticket-header {{ background: linear-gradient(135deg, #4f46e5 0%, #2e27c0 100%); color: white; padding: 20px; text-align: center; }}
                    .ticket-header h2 {{ margin: 0; font-size: 18px; font-weight: 700; }}
                    .ticket-header h3 {{ margin: 5px 0 0; font-size: 14px; font-weight: 400; opacity: 0.9; }}
                    .ticket-content {{ display: flex; flex-direction: column; }}
                    .ticket-details {{ padding: 20px; }}
                    .ticket-section {{ margin-bottom: 20px; }}
                    .ticket-section-title {{ font-size: 14px; text-transform: uppercase; color: #4f46e5; margin: 0 0 10px 0; font-weight: 600; letter-spacing: 1px; border-bottom: 1px solid #f0f0f0; padding-bottom: 5px; }}
                    .ticket-info-row {{ margin-bottom: 8px; }}
                    .ticket-info-label {{ font-weight: 600; color: #666; display: inline-block; width: 80px; }}
                    .ticket-qr {{ padding: 20px; text-align: center; background-color: #f9f9f9; }}
                    .ticket-qr img {{ max-width: 150px; height: auto; border: 8px solid white; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1); }}
                    .ticket-instructions {{ font-size: 12px; color: #666; margin-top: 10px; }}
                    .ticket-id {{ font-size: 11px; color: #999; margin-top: 5px; }}
                    .ticket-footer {{ background-color: #f8f8f8; padding: 15px; text-align: center; font-size: 11px; color: #888; border-top: 1px solid #eaeaea; }}
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="email-header">
                        <h1>Your Ticket for {event.name}</h1>
                    </div>
                    <div class="email-content">
                        <div class="email-greeting">
                            <p>Hello {invitation.guest_name},</p>
                            <p>Thank you for registering for <strong>{event.name}</strong>! Your e-ticket is below.</p>
                        </div>
                        
                        <!-- Embedded Ticket -->
                        <div class="ticket">
                            <div class="ticket-header">
                                <h2>{event.name}</h2>
                                <h3>Admission Ticket</h3>
                            </div>
                            <div class="ticket-content">
                                <div class="ticket-details">
                                    <div class="ticket-section">
                                        <h4 class="ticket-section-title">Guest Information</h4>
                                        <div class="ticket-info-row">
                                            <span class="ticket-info-label">Name:</span>
                                            <span>{invitation.guest_name}</span>
                                        </div>
                                        {f'<div class="ticket-info-row"><span class="ticket-info-label">Email:</span><span>{invitation.guest_email}</span></div>' if invitation.guest_email else ''}
                                        {f'<div class="ticket-info-row"><span class="ticket-info-label">Phone:</span><span>{invitation.guest_phone}</span></div>' if invitation.guest_phone else ''}
                                    </div>
                                    
                                    <div class="ticket-section">
                                        <h4 class="ticket-section-title">Event Details</h4>
                                        <div class="ticket-info-row">
                                            <span class="ticket-info-label">Date:</span>
                                            <span>{event.date}</span>
                                        </div>
                                        <div class="ticket-info-row">
                                            <span class="ticket-info-label">Time:</span>
                                            <span>{event.time}</span>
                                        </div>
                                        <div class="ticket-info-row">
                                            <span class="ticket-info-label">Location:</span>
                                            <span>{event.location}</span>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="ticket-qr">
                                    <!-- QR Code Image with improved visibility -->
                                    {self.get_qr_code_html(qr_code_data_uri, qr_code_url)}
                                    <div class="ticket-instructions">Scan for check-in</div>
                                    <div class="ticket-id">Ticket ID: {invitation.id}</div>
                                </div>
                                
                                <div class="ticket-footer">
                                    <p>Please present this QR code at the venue for quick check-in.</p>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Calendar Instructions -->
                        <div style="background-color: #f8f9ff; border: 1px solid #e0e4ff; border-radius: 8px; padding: 20px; margin: 20px 0;">
                            <h3 style="color: #4f46e5; margin: 0 0 10px 0; font-size: 16px;">📅 Add to Your Calendar</h3>
                            <p style="margin: 0 0 15px 0; color: #555;">Don't forget about this event! We've included a calendar file with this email.</p>
                            <div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">
                                <div style="background-color: white; padding: 10px 15px; border-radius: 6px; border: 1px solid #ddd;">
                                    <strong>📎 {generate_ics_filename(event)}</strong>
                                    <br><small style="color: #666;">Click this attachment to add the event to your calendar</small>
                                </div>
                                <div style="color: #666; font-size: 14px;">
                                    Works with Google Calendar, Outlook, Apple Calendar, and more!
                                    <br><br>
                                    <strong>Alternative:</strong> Add directly to 
                                    <a href="https://calendar.google.com/calendar/render?action=TEMPLATE&text={event.name}&dates={event.date.strftime('%Y%m%d')}&details=Event%20Details:%20{event.description or 'Check-in with your QR code ticket'}&location={event.location}" 
                                       style="color: #4285f4;">Google Calendar</a> | 
                                    <a href="https://outlook.live.com/calendar/0/deeplink/compose?subject={event.name}&startdt={event.date}T{event.time}&body=Check-in%20with%20your%20QR%20code%20ticket" 
                                       style="color: #0078d4;">Outlook</a>
                                </div>
                            </div>
                        </div>
                        
                        <p>Please save this email and present the QR code at the event entrance for quick check-in.</p>
                        <p>You can also access your ticket online at: <a href="{ticket_view_url}">{ticket_view_url}</a></p>
                        
                        <p>We look forward to seeing you!</p>
                    </div>
                    <div class="email-footer">
                        <p>This is an automated message from the QR Check-in System.</p>
                        <p>&copy; 2025 QR Check-in System. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Log email settings
            logger.info(f"Email settings for manual send - Backend: {settings.EMAIL_BACKEND}")
            logger.info(f"Email settings for manual send - Host: {settings.EMAIL_HOST}")
            logger.info(f"Email settings for manual send - Port: {settings.EMAIL_PORT}")
            logger.info(f"Email settings for manual send - TLS: {settings.EMAIL_USE_TLS}")
            logger.info(f"Email settings for manual send - User: {settings.EMAIL_HOST_USER}")
            logger.info(f"Email settings for manual send - From: {settings.DEFAULT_FROM_EMAIL}")
            
            # Verify needed settings before proceeding
            if settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
                # Check all required SMTP settings are present
                missing_settings = []
                if not settings.EMAIL_HOST:
                    missing_settings.append("EMAIL_HOST")
                if not settings.EMAIL_PORT:
                    missing_settings.append("EMAIL_PORT")
                if not settings.EMAIL_HOST_USER:
                    missing_settings.append("EMAIL_HOST_USER")
                if not settings.EMAIL_HOST_PASSWORD:
                    missing_settings.append("EMAIL_HOST_PASSWORD")
                
                if missing_settings:
                    error_msg = f"Missing required SMTP settings: {', '.join(missing_settings)}"
                    logger.error(error_msg)
                    return Response(
                        {'error': error_msg},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            
            # Try creating a direct SMTP connection to validate credentials
            if settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
                try:
                    logger.info("Testing direct SMTP connection before sending...")
                    server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
                    server.set_debuglevel(1)  # Verbose logging
                    
                    if settings.EMAIL_USE_TLS:
                        server.starttls()
                        
                    if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
                        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                        
                    server.quit()
                    logger.info("Direct SMTP connection successful.")
                except Exception as smtp_test_error:
                    error_msg = f"Failed to connect to SMTP server: {str(smtp_test_error)}"
                    logger.error(error_msg)
                    return Response(
                        {'error': error_msg},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                    
            # Now create the Django connection
            from django.core.mail import get_connection
            logger.info("Creating Django email connection...")
            connection = get_connection(
                backend=settings.EMAIL_BACKEND,
                host=settings.EMAIL_HOST,
                port=settings.EMAIL_PORT,
                username=settings.EMAIL_HOST_USER,
                password=settings.EMAIL_HOST_PASSWORD,
                use_tls=settings.EMAIL_USE_TLS,
                fail_silently=False,
            )
            
            # Create the email message
            from django.core.mail import EmailMultiAlternatives
            email = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[invitation.guest_email],
                connection=connection,
            )
            
            # Try to attach the QR code as a Content-ID (CID) attachment
            qr_cid = None
            if invitation.qr_code and hasattr(invitation.qr_code, 'path') and os.path.exists(invitation.qr_code.path):
                try:
                    with open(invitation.qr_code.path, 'rb') as f:
                        qr_image_data = f.read()
                    
                    # Generate a Content-ID for the image
                    qr_cid = f"<qrcode_{invitation.id}@qrticket.app>"
                    
                    # Attach the image with the Content-ID
                    from email.mime.image import MIMEImage
                    img = MIMEImage(qr_image_data)
                    img.add_header('Content-ID', qr_cid)
                    img.add_header('Content-Disposition', 'inline')
                    email.attach(img)
                    
                    logger.info(f"Attached QR code as CID: {qr_cid}")
                    
                    # Create a version of HTML with CID image reference
                    cid_html_message = html_message
                    
                    # Replace any QR code references with our CID reference
                    if qr_code_data_uri:
                        cid_html_message = cid_html_message.replace(
                            f'src="{qr_code_data_uri}"', 
                            f'src="cid:{qr_cid[1:-1]}"'
                        )
                    if qr_code_url:
                        cid_html_message = cid_html_message.replace(
                            f'src="{qr_code_url}"', 
                            f'src="cid:{qr_cid[1:-1]}"'
                        )
                    
                    # Use the CID version of the HTML
                    html_message = cid_html_message
                    logger.info("Using HTML with CID reference to QR code")
                except Exception as e:
                    logger.error(f"Failed to attach QR code as CID: {str(e)}")
                    # Continue with the original HTML that has data URI or URL
            
            # Attach HTML content
            email.attach_alternative(html_message, "text/html")
            
            # Attach PDF ticket to the email
            if invitation.ticket_pdf and hasattr(invitation.ticket_pdf, 'path') and os.path.exists(invitation.ticket_pdf.path):
                try:
                    with open(invitation.ticket_pdf.path, 'rb') as pdf_file:
                        pdf_data = pdf_file.read()
                        
                    logger.info(f"Attaching PDF ticket ({len(pdf_data)} bytes) to email")
                    email.attach(f"Ticket-{invitation.event.name}.pdf", pdf_data, 'application/pdf')
                    logger.info("PDF ticket attached successfully")
                except Exception as e:
                    logger.error(f"Failed to attach PDF ticket: {str(e)}")
            else:
                # Try to generate PDF if it doesn't exist
                logger.info("PDF ticket file not found, attempting to generate it")
                try:
                    success = invitation.generate_pdf_ticket()
                    if success and invitation.ticket_pdf and hasattr(invitation.ticket_pdf, 'path') and os.path.exists(invitation.ticket_pdf.path):
                        with open(invitation.ticket_pdf.path, 'rb') as pdf_file:
                            pdf_data = pdf_file.read()
                        logger.info(f"Attaching newly generated PDF ticket ({len(pdf_data)} bytes) to email")
                        email.attach(f"Ticket-{invitation.event.name}.pdf", pdf_data, 'application/pdf')
                        logger.info("Newly generated PDF ticket attached successfully")
                    else:
                        logger.warning("Could not generate and attach PDF ticket")
                except Exception as pdf_error:
                    logger.error(f"Error generating PDF for attachment: {str(pdf_error)}")
            
            # No need to attach HTML ticket separately since it's already in the email body
            
            # Attach calendar invite (ICS file)
            try:
                logger.info("=== STARTING CALENDAR GENERATION ===")
                logger.info(f"Event: {event.name} (ID: {event.id})")
                logger.info(f"Event date: {event.date}, time: {event.time}")
                logger.info(f"Invitation: {invitation.guest_name} ({invitation.guest_email})")
                
                calendar = create_event_calendar(event, invitation)
                logger.info("Calendar object created successfully")
                
                ics_data = calendar.to_ical()
                logger.info(f"ICS data generated: {len(ics_data)} bytes")
                
                ics_filename = generate_ics_filename(event)
                logger.info(f"ICS filename: {ics_filename}")
                
                # Attach calendar with proper headers for better email client support
                email.attach(ics_filename, ics_data, 'text/calendar; method=REQUEST')
                logger.info("=== CALENDAR INVITE ATTACHED SUCCESSFULLY ===")
            except Exception as cal_error:
                logger.error(f"=== CALENDAR ERROR: {str(cal_error)} ===")
                import traceback
                logger.error(f"=== CALENDAR TRACEBACK: {traceback.format_exc()} ===")
                # Continue without calendar attachment
            
            # Send the email
            logger.info(f"Sending email to {invitation.guest_email}...")
            logger.info(f"Email connection: {email.connection}")
            logger.info(f"Email subject: {email.subject}")
            logger.info(f"Email from: {email.from_email}")
            logger.info(f"Email to: {email.to}")
            
            try:
                result = email.send(fail_silently=False)
                logger.info(f"Email send result: {result}")
                
                # Log more details about the SMTP server response if available
                if hasattr(email.connection, 'last_response'):
                    logger.info(f"SMTP server last response: {email.connection.last_response}")
            except Exception as send_error:
                logger.error(f"Exception during email.send(): {str(send_error)}")
                # Re-raise to be caught by the outer try-except
                raise
            
            return Response({'message': f'Invitation email sent successfully to {invitation.guest_email}'})
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP Authentication Error: {str(e)}"
            logger.error(error_msg)
            logger.error("This is likely due to incorrect username/password or Gmail security settings.")
            logger.error("For Gmail, make sure you're using an App Password if 2FA is enabled.")
            return Response(
                {'error': error_msg},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except smtplib.SMTPException as e:
            error_msg = f"SMTP Error: {str(e)}"
            logger.error(error_msg)
            return Response(
                {'error': error_msg},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Failed to send invitation email: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {'error': f'Failed to send email: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def send_invitation_email(self, invitation):
        """Send invitation email with digital ticket."""
        if not invitation.guest_email:
            logger.info(f"No guest email for invitation {invitation.id}, skipping email")
            return
            
        # Get the event details
        event = invitation.event
        logger.info(f"Preparing email for invitation {invitation.id} to {invitation.guest_email}")
        
        # Build base URL for links - using a default for development
        base_url = settings.BASE_URL if hasattr(settings, 'BASE_URL') else "http://localhost:8000"
        logger.info(f"Using base URL: {base_url}")
        
        # Get ticket URLs
        ticket_view_url = f"{base_url}/tickets/{invitation.id}/"
        logger.info(f"Ticket view URL: {ticket_view_url}")
        
        # Email subject
        subject = f"Your Ticket for {event.name}"
        
        # Verify email config is set
        if not settings.EMAIL_HOST or not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            logger.warning("Email configuration is incomplete. Check EMAIL_HOST, EMAIL_HOST_USER, and EMAIL_HOST_PASSWORD settings.")
            if settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
                logger.warning("Using SMTP backend but credentials are missing. Email may fail to send.")
        
        # Plain text message
        message = f"""
        Hello {invitation.guest_name},
        
        Your ticket for {event.name} is ready.
        
        Event Details:
        - Date: {event.date}
        - Time: {event.time}
        - Location: {event.location}
        
        We've attached a PDF version of your ticket to this email that you can download, print, or keep on your device.
        
        Please bring your ticket with the QR code to the event for quick check-in.
        You can view your ticket online at: {ticket_view_url}
        
        Thank you!
        """
        
        # Get QR code URL and data URI for embedding in email
        qr_code_url = None
        
        # Use the helper method to get a base64 encoded QR code
        qr_code_data_uri = invitation.get_qr_code_base64()
        if qr_code_data_uri:
            logger.info(f"Successfully created QR code data URI for email for invitation {invitation.id}")
        else:
            logger.warning(f"Could not create QR code data URI for email for invitation {invitation.id}")
        
        # Always set up URL as fallback
        if invitation.qr_code:
            qr_code_url = invitation.qr_code.url
            if qr_code_url.startswith('/'):
                qr_code_url = f"{base_url}{qr_code_url}"
            logger.info(f"Using fallback QR code URL for email: {qr_code_url}")
                
        # HTML message with embedded ticket
        html_message = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: 'Helvetica', 'Arial', sans-serif; margin: 0; padding: 0; color: #333; background-color: #f9f9f9; }}
                .email-container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .email-header {{ background: linear-gradient(135deg, #4f46e5 0%, #2e27c0 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .email-header h1 {{ margin: 0; font-size: 24px; font-weight: 700; }}
                .email-content {{ background-color: #ffffff; padding: 30px; border-radius: 0 0 8px 8px; }}
                .email-footer {{ margin-top: 20px; text-align: center; font-size: 12px; color: #888; }}
                .email-greeting {{ margin-bottom: 25px; font-size: 16px; }}
                
                /* Ticket styles */
                .ticket {{ background-color: white; border-radius: 16px; overflow: hidden; box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1); margin: 25px 0; border: 1px solid #e5e5e5; }}
                .ticket-header {{ background: linear-gradient(135deg, #4f46e5 0%, #2e27c0 100%); color: white; padding: 20px; text-align: center; }}
                .ticket-header h2 {{ margin: 0; font-size: 18px; font-weight: 700; }}
                .ticket-header h3 {{ margin: 5px 0 0; font-size: 14px; font-weight: 400; opacity: 0.9; }}
                .ticket-content {{ display: flex; flex-direction: column; }}
                .ticket-details {{ padding: 20px; }}
                .ticket-section {{ margin-bottom: 20px; }}
                .ticket-section-title {{ font-size: 14px; text-transform: uppercase; color: #4f46e5; margin: 0 0 10px 0; font-weight: 600; letter-spacing: 1px; border-bottom: 1px solid #f0f0f0; padding-bottom: 5px; }}
                .ticket-info-row {{ margin-bottom: 8px; }}
                .ticket-info-label {{ font-weight: 600; color: #666; display: inline-block; width: 80px; }}
                .ticket-qr {{ padding: 20px; text-align: center; background-color: #f9f9f9; }}
                .ticket-qr img {{ max-width: 150px; height: auto; border: 8px solid white; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1); }}
                .ticket-instructions {{ font-size: 12px; color: #666; margin-top: 10px; }}
                .ticket-id {{ font-size: 11px; color: #999; margin-top: 5px; }}
                .ticket-footer {{ background-color: #f8f8f8; padding: 15px; text-align: center; font-size: 11px; color: #888; border-top: 1px solid #eaeaea; }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="email-header">
                    <h1>Your Ticket for {event.name}</h1>
                </div>
                <div class="email-content">
                    <div class="email-greeting">
                        <p>Hello {invitation.guest_name},</p>
                        <p>Thank you for registering for <strong>{event.name}</strong>! Your e-ticket is below.</p>
                    </div>
                    
                    <!-- Embedded Ticket -->
                    <div class="ticket">
                        <div class="ticket-header">
                            <h2>{event.name}</h2>
                            <h3>Admission Ticket</h3>
                        </div>
                        <div class="ticket-content">
                            <div class="ticket-details">
                                <div class="ticket-section">
                                    <h4 class="ticket-section-title">Guest Information</h4>
                                    <div class="ticket-info-row">
                                        <span class="ticket-info-label">Name:</span>
                                        <span>{invitation.guest_name}</span>
                                    </div>
                                    {f'<div class="ticket-info-row"><span class="ticket-info-label">Email:</span><span>{invitation.guest_email}</span></div>' if invitation.guest_email else ''}
                                    {f'<div class="ticket-info-row"><span class="ticket-info-label">Phone:</span><span>{invitation.guest_phone}</span></div>' if invitation.guest_phone else ''}
                                </div>
                                
                                <div class="ticket-section">
                                    <h4 class="ticket-section-title">Event Details</h4>
                                    <div class="ticket-info-row">
                                        <span class="ticket-info-label">Date:</span>
                                        <span>{event.date}</span>
                                    </div>
                                    <div class="ticket-info-row">
                                        <span class="ticket-info-label">Time:</span>
                                        <span>{event.time}</span>
                                    </div>
                                    <div class="ticket-info-row">
                                        <span class="ticket-info-label">Location:</span>
                                        <span>{event.location}</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="ticket-qr">
                                <!-- QR Code Image with improved visibility -->
                                {self.get_qr_code_html(qr_code_data_uri, qr_code_url)}
                                <div class="ticket-instructions">Scan for check-in</div>
                                <div class="ticket-id">Ticket ID: {invitation.id}</div>
                            </div>
                            
                            <div class="ticket-footer">
                                <p>Please present this QR code at the venue for quick check-in.</p>
                            </div>
                        </div>
                    </div>
                    
                    <p>Please save this email and present the QR code at the event entrance for quick check-in.</p>
                    <p><strong>We've attached a PDF version of your ticket to this email</strong> that you can download, print, or keep on your device.</p>
                    <p>You can also access your ticket online at: <a href="{ticket_view_url}">{ticket_view_url}</a></p>
                    
                    <p>We look forward to seeing you!</p>
                </div>
                <div class="email-footer">
                    <p>This is an automated message from the QR Check-in System.</p>
                    <p>&copy; 2025 QR Check-in System. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Log email settings
        logger.info(f"Email settings - Backend: {settings.EMAIL_BACKEND}")
        logger.info(f"Email settings - Host: {settings.EMAIL_HOST}")
        logger.info(f"Email settings - Port: {settings.EMAIL_PORT}")
        logger.info(f"Email settings - TLS: {settings.EMAIL_USE_TLS}")
        logger.info(f"Email settings - User: {settings.EMAIL_HOST_USER}")
        logger.info(f"Email settings - From: {settings.DEFAULT_FROM_EMAIL}")
        
        try:
            # Prepare email
            logger.info(f"Creating email message to {invitation.guest_email}")
            email = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[invitation.guest_email],
            )
            
            # Try to attach the QR code as a Content-ID (CID) attachment
            qr_cid = None
            if invitation.qr_code and hasattr(invitation.qr_code, 'path') and os.path.exists(invitation.qr_code.path):
                try:
                    with open(invitation.qr_code.path, 'rb') as f:
                        qr_image_data = f.read()
                    
                    # Generate a Content-ID for the image
                    qr_cid = f"<qrcode_{invitation.id}@qrticket.app>"
                    
                    # Attach the image with the Content-ID
                    from email.mime.image import MIMEImage
                    img = MIMEImage(qr_image_data)
                    img.add_header('Content-ID', qr_cid)
                    img.add_header('Content-Disposition', 'inline')
                    email.attach(img)
                    
                    logger.info(f"Attached QR code as CID: {qr_cid}")
                    
                    # Create a version of HTML with CID image reference
                    cid_html_message = html_message
                    
                    # Replace any QR code references with our CID reference
                    if qr_code_data_uri:
                        cid_html_message = cid_html_message.replace(
                            f'src="{qr_code_data_uri}"', 
                            f'src="cid:{qr_cid[1:-1]}"'
                        )
                    if qr_code_url:
                        cid_html_message = cid_html_message.replace(
                            f'src="{qr_code_url}"', 
                            f'src="cid:{qr_cid[1:-1]}"'
                        )
                    
                    # Use the CID version of the HTML
                    html_message = cid_html_message
                    logger.info("Using HTML with CID reference to QR code")
                except Exception as e:
                    logger.error(f"Failed to attach QR code as CID: {str(e)}")
                    # Continue with the original HTML that has data URI or URL
            
            # Attach HTML content
            logger.info("Attaching HTML content")
            email.attach_alternative(html_message, "text/html")
            
            # Attach PDF ticket to the email
            if invitation.ticket_pdf and hasattr(invitation.ticket_pdf, 'path') and os.path.exists(invitation.ticket_pdf.path):
                try:
                    with open(invitation.ticket_pdf.path, 'rb') as pdf_file:
                        pdf_data = pdf_file.read()
                        
                    logger.info(f"Attaching PDF ticket ({len(pdf_data)} bytes) to email")
                    email.attach(f"Ticket-{invitation.event.name}.pdf", pdf_data, 'application/pdf')
                    logger.info("PDF ticket attached successfully")
                except Exception as e:
                    logger.error(f"Failed to attach PDF ticket: {str(e)}")
            else:
                # Try to generate PDF if it doesn't exist
                logger.info("PDF ticket file not found, attempting to generate it")
                try:
                    success = invitation.generate_pdf_ticket()
                    if success and invitation.ticket_pdf and hasattr(invitation.ticket_pdf, 'path') and os.path.exists(invitation.ticket_pdf.path):
                        with open(invitation.ticket_pdf.path, 'rb') as pdf_file:
                            pdf_data = pdf_file.read()
                        logger.info(f"Attaching newly generated PDF ticket ({len(pdf_data)} bytes) to email")
                        email.attach(f"Ticket-{invitation.event.name}.pdf", pdf_data, 'application/pdf')
                        logger.info("Newly generated PDF ticket attached successfully")
                    else:
                        logger.warning("Could not generate and attach PDF ticket")
                except Exception as pdf_error:
                    logger.error(f"Error generating PDF for attachment: {str(pdf_error)}")
            
            # No need to attach HTML ticket separately since it's already in the email body
            
            # Attach calendar invite (ICS file)
            try:
                logger.info("=== STARTING CALENDAR GENERATION ===")
                logger.info(f"Event: {event.name} (ID: {event.id})")
                logger.info(f"Event date: {event.date}, time: {event.time}")
                logger.info(f"Invitation: {invitation.guest_name} ({invitation.guest_email})")
                
                calendar = create_event_calendar(event, invitation)
                logger.info("Calendar object created successfully")
                
                ics_data = calendar.to_ical()
                logger.info(f"ICS data generated: {len(ics_data)} bytes")
                
                ics_filename = generate_ics_filename(event)
                logger.info(f"ICS filename: {ics_filename}")
                
                # Attach calendar with proper headers for better email client support
                email.attach(ics_filename, ics_data, 'text/calendar; method=REQUEST')
                logger.info("=== CALENDAR INVITE ATTACHED SUCCESSFULLY ===")
            except Exception as cal_error:
                logger.error(f"=== CALENDAR ERROR: {str(cal_error)} ===")
                import traceback
                logger.error(f"=== CALENDAR TRACEBACK: {traceback.format_exc()} ===")
                # Continue without calendar attachment
                
            # Send email
            logger.info("Sending email...")
            
            # Add debugging information for connection
            if email.connection:
                try:
                    connection_debug = email.connection.open()
                    logger.info(f"Email connection opened: {connection_debug}")
                except Exception as conn_err:
                    logger.error(f"Error opening email connection: {str(conn_err)}")
            else:
                logger.error("Email connection is None. Creating a new connection.")
                from django.core.mail import get_connection
                email.connection = get_connection(
                    backend=settings.EMAIL_BACKEND,
                    host=settings.EMAIL_HOST,
                    port=settings.EMAIL_PORT,
                    username=settings.EMAIL_HOST_USER,
                    password=settings.EMAIL_HOST_PASSWORD,
                    use_tls=settings.EMAIL_USE_TLS,
                )
            
            result = email.send()
            logger.info(f"Email send result: {result}")
            return True
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication Error: {str(e)}")
            logger.error("This is likely due to incorrect username/password or Gmail security settings.")
            logger.error("For Gmail, make sure you're using an App Password if 2FA is enabled.")
            logger.error("Check: https://myaccount.google.com/apppasswords")
            import traceback
            logger.error(traceback.format_exc())
            raise
        except smtplib.SMTPException as e:
            logger.error(f"SMTP Error: {str(e)}")
            logger.error("This could be due to incorrect host/port or network connectivity issues.")
            import traceback
            logger.error(traceback.format_exc())
            raise
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise
        
    @action(detail=False, methods=['post'])
    def sync(self, request):
        """
        Synchronize offline invitations with the server
        
        Expects a list of invitations with temp_ids and the actual event_id
        """
        invitations_data = request.data
        id_mapping = {}
        
        for invitation_data in invitations_data:
            temp_id = invitation_data.pop('temp_id', None)
            event_id = invitation_data.get('event')
            
            if not temp_id or not event_id:
                continue
                
            try:
                # Verify the event exists
                Event.objects.get(id=event_id)
                
                # Remove any fields that shouldn't be set directly
                invitation_data.pop('id', None)
                invitation_data.pop('qr_code', None)
                invitation_data.pop('ticket_html', None)
                invitation_data.pop('ticket_pdf', None)
                invitation_data.pop('created_at', None)
                invitation_data.pop('updated_at', None)
                
                serializer = self.get_serializer(data=invitation_data)
                if serializer.is_valid():
                    invitation = serializer.save()
                    id_mapping[temp_id] = str(invitation.id)
            except Event.DoesNotExist:
                continue
                
        return Response({'id_mapping': id_mapping})


@api_view(['GET'])
@csrf_exempt
def debug_ticket_generation(request, invitation_id):
    """Debug endpoint to test ticket generation for an invitation"""
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': 'Authentication required'
        }, status=401)
    logger.info(f"Debug ticket generation called for invitation {invitation_id}")
    
    try:
        invitation = Invitation.objects.get(id=invitation_id)
        
        # Force generate tickets
        logger.info("Forcing ticket generation...")
        invitation.generate_tickets()
        invitation.save()
        
        # Check if tickets were created
        html_exists = bool(invitation.ticket_html)
        pdf_exists = bool(invitation.ticket_pdf)
        
        # Get ticket paths if they exist
        html_path = invitation.ticket_html.path if html_exists else None
        pdf_path = invitation.ticket_pdf.path if pdf_exists else None
        
        # Check if files actually exist on disk
        html_file_exists = html_exists and os.path.exists(html_path)
        pdf_file_exists = pdf_exists and os.path.exists(pdf_path)
        
        result = {
            'success': True,
            'invitation_id': str(invitation.id),
            'html_ticket': {
                'record_exists': html_exists,
                'file_exists': html_file_exists,
                'path': html_path,
                'url': invitation.ticket_html.url if html_exists else None
            },
            'pdf_ticket': {
                'record_exists': pdf_exists,
                'file_exists': pdf_file_exists,
                'path': pdf_path,
                'url': invitation.ticket_pdf.url if pdf_exists else None
            }
        }
        
        return JsonResponse(result)
    except Invitation.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'error': f'Invitation with ID {invitation_id} not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error in debug endpoint: {str(e)}")
        return JsonResponse({
            'success': False, 
            'error': str(e)
        }, status=500)
        
        
@api_view(['POST'])
def simple_test_email(request):
    """Super simple email test without any attachments or complex logic"""
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': 'Authentication required'
        }, status=401)
    # Get the test email from request or use a default
    email = request.data.get('email', None)
    if not email:
        return JsonResponse({
            'success': False,
            'error': 'Email address is required'
        }, status=400)
    
    logger.info(f"Simple test email requested for {email}")
    
    # Log email settings for debugging
    logger.info("=================== EMAIL SETTINGS ===================")
    logger.info(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    logger.info(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    logger.info(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    logger.info(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    logger.info(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    logger.info(f"EMAIL_HOST_PASSWORD: {'*****' if settings.EMAIL_HOST_PASSWORD else 'NOT SET'}")
    logger.info(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    logger.info("====================================================")
    
    try:
        # Create a simple email message
        from django.core.mail import EmailMessage
        
        # Create a direct connection
        from django.core.mail import get_connection
        connection = get_connection(
            backend=settings.EMAIL_BACKEND,
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            use_tls=settings.EMAIL_USE_TLS,
            fail_silently=False,
        )
        
        # Try to open the connection explicitly
        try:
            connection.open()
            logger.info("Connection opened successfully")
        except Exception as conn_error:
            logger.error(f"Error opening connection: {str(conn_error)}")
            return JsonResponse({
                'success': False,
                'error': f'Failed to connect to mail server: {str(conn_error)}'
            }, status=500)
        
        # Create and send the message
        subject = "Test Email from QR Check-in System"
        body = f"This is a test email sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
        email_msg = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
            connection=connection,
        )
        
        # Try to send
        logger.info(f"Sending simple test email to {email}...")
        result = email_msg.send(fail_silently=False)
        logger.info(f"Email sent result: {result}")
        
        # Finally close the connection
        connection.close()
        
        return JsonResponse({
            'success': True,
            'message': f'Simple test email sent to {email}'
        })
    except Exception as e:
        logger.error(f"Error in simple test email: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['POST'])
@csrf_exempt
def test_email_delivery(request, invitation_id):
    """Test endpoint to send an invitation email with ticket attachments"""
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': 'Authentication required'
        }, status=401)
    logger.info(f"Test email delivery called for invitation {invitation_id}")
    
    # Get the test email from request or use a default
    email = request.data.get('email', None)
    if not email:
        return JsonResponse({
            'success': False,
            'error': 'Email address is required'
        }, status=400)
    
    try:
        # Get the invitation
        invitation = Invitation.objects.get(id=invitation_id)
        
        # Store original email
        original_email = invitation.guest_email
        
        # Temporarily set the invitation email to the test email
        invitation.guest_email = email
        
        # Force generate tickets if they don't exist
        if not invitation.ticket_html or not invitation.ticket_pdf:
            logger.info(f"Generating tickets for invitation {invitation_id}")
            invitation.generate_tickets()
            invitation.save()
        
        # Send the email
        logger.info(f"Sending test email to {email}")
        view_set = InvitationViewSet()
        view_set.send_invitation_email(invitation)
        
        # Restore original email
        invitation.guest_email = original_email
        invitation.save(update_fields=['guest_email'])
        
        return JsonResponse({
            'success': True,
            'message': f'Test email sent to {email}',
            'html_ticket_url': invitation.ticket_html.url if invitation.ticket_html else None,
            'pdf_ticket_url': invitation.ticket_pdf.url if invitation.ticket_pdf else None
        })
    except Invitation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': f'Invitation with ID {invitation_id} not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error sending test email: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)