from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Import admin customizations
from . import admin as admin_customizations

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/events/', include('events.urls')),
    path('api/invitations/', include('invitations.urls')),
    path('api/attendance/', include('attendance.urls')),
    path('api/auth/', include('users.urls')),
]

# Always serve media files in development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)