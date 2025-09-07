from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'profiles', views.NetworkingProfileViewSet, basename='networking-profile')
router.register(r'directory', views.AttendeeDirectoryViewSet, basename='attendee-directory')
router.register(r'connections', views.ConnectionViewSet, basename='connection')
router.register(r'interactions', views.NetworkingInteractionViewSet, basename='networking-interaction')
router.register(r'settings', views.EventNetworkingSettingsViewSet, basename='networking-settings')
router.register(r'stats', views.NetworkingStatsViewSet, basename='networking-stats')

urlpatterns = [
    path('api/networking/', include(router.urls)),
]

# Test URLs for development
from .test_views import networking_test_page, generate_networking_qr

urlpatterns += [
    path('networking/test/', networking_test_page, name='networking-test'),
    path('networking/qr/<int:user_id>/<int:event_id>/', generate_networking_qr, name='networking-qr'),
]

# User-friendly HTML pages
from .html_views import networking_qr_page, networking_directory_page, networking_connections_page, networking_profile_page, update_networking_profile

urlpatterns += [
    path('networking/qr-code/<int:user_id>/<int:event_id>/', networking_qr_page, name='networking-qr-page'),
    path('networking/directory/<int:event_id>/', networking_directory_page, name='networking-directory-page'),
    path('networking/connections/<int:event_id>/', networking_connections_page, name='networking-connections-page'),
    path('networking/profile/<int:user_id>/<int:event_id>/', networking_profile_page, name='networking-profile-page'),
    path('networking/profile/<int:user_id>/<int:event_id>/update/', update_networking_profile, name='update-networking-profile'),
]
