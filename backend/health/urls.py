from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health-check'),
    path('health/ready/', views.readiness_check, name='readiness-check'),
    path('health/live/', views.liveness_check, name='liveness-check'),
]