from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InvitationViewSet, debug_ticket_generation, test_email_delivery, simple_test_email
from django.views.decorators.csrf import csrf_exempt

router = DefaultRouter()
router.register(r'', InvitationViewSet, basename='invitation')

urlpatterns = [
    path('', include(router.urls)),
    # Debug endpoints
    path('debug/ticket-generation/<uuid:invitation_id>/', debug_ticket_generation, name='debug-ticket-generation'),
    path('debug/test-email/<uuid:invitation_id>/', test_email_delivery, name='test-email-delivery'),
    path('debug/simple-test-email/', csrf_exempt(simple_test_email), name='simple-test-email'),
]