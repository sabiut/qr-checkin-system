from django.apps import AppConfig


class NetworkingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'networking'
    verbose_name = 'Networking & Contact Exchange'
    
    def ready(self):
        import networking.signals
