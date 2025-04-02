from django.apps import AppConfig
import os


class InvitationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'invitations'
    
    def ready(self):
        """Set up necessary directories on app startup."""
        # Create media directories if they don't exist
        from django.conf import settings
        if hasattr(settings, 'MEDIA_ROOT'):
            # Ensure main media directory exists
            os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
            
            # Create subdirectories for tickets and QR codes
            tickets_html_dir = os.path.join(settings.MEDIA_ROOT, 'tickets', 'html')
            tickets_pdf_dir = os.path.join(settings.MEDIA_ROOT, 'tickets', 'pdf')
            qrcodes_dir = os.path.join(settings.MEDIA_ROOT, 'qrcodes')
            
            os.makedirs(tickets_html_dir, exist_ok=True)
            os.makedirs(tickets_pdf_dir, exist_ok=True)
            os.makedirs(qrcodes_dir, exist_ok=True)
            
            print(f"Created media directories: {tickets_html_dir}, {tickets_pdf_dir}, {qrcodes_dir}")
            
            # Try to make directories world-writable to avoid permission issues
            try:
                # This is not ideal for production but helps with development
                os.chmod(settings.MEDIA_ROOT, 0o777)
                os.chmod(tickets_html_dir, 0o777)
                os.chmod(tickets_pdf_dir, 0o777)
                os.chmod(qrcodes_dir, 0o777)
                print("Set media directories to be writable")
            except Exception as e:
                print(f"Could not set directory permissions: {e}")