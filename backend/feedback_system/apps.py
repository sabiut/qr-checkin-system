from django.apps import AppConfig


class FeedbackSystemConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'feedback_system'
    verbose_name = 'Feedback System'
    
    def ready(self):
        import feedback_system.signals