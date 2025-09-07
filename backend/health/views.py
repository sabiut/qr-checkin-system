from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import time


def health_check(request):
    """
    Health check endpoint for deployment validation
    Returns 200 if all systems are operational
    """
    health_status = {
        'status': 'healthy',
        'timestamp': int(time.time()),
        'checks': {}
    }
    
    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_status['checks']['database'] = 'ok'
    except Exception as e:
        health_status['checks']['database'] = 'failed'
        health_status['status'] = 'unhealthy'
        return JsonResponse(health_status, status=503)
    
    # Check cache connectivity (if using cache)
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            health_status['checks']['cache'] = 'ok'
        else:
            health_status['checks']['cache'] = 'failed'
    except Exception:
        health_status['checks']['cache'] = 'not_configured'
    
    # Check critical imports
    try:
        from events.models import Event
        from invitations.models import Invitation
        from networking.models import NetworkingProfile
        health_status['checks']['models'] = 'ok'
    except ImportError as e:
        health_status['checks']['models'] = 'failed'
        health_status['status'] = 'unhealthy'
        return JsonResponse(health_status, status=503)
    
    # Add deployment color if available
    import os
    deployment_color = os.environ.get('DEPLOYMENT_COLOR', 'unknown')
    health_status['deployment'] = deployment_color
    
    return JsonResponse(health_status)


def readiness_check(request):
    """
    Readiness check for Kubernetes/Docker
    Returns 200 if the application is ready to serve traffic
    """
    try:
        # Quick database check
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        return JsonResponse({'status': 'ready'})
    except Exception:
        return JsonResponse({'status': 'not_ready'}, status=503)


def liveness_check(request):
    """
    Liveness check for Kubernetes/Docker
    Returns 200 if the application is alive
    """
    return JsonResponse({'status': 'alive'})