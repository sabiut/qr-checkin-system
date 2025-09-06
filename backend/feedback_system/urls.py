from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FeedbackTagViewSet, EventFeedbackViewSet

router = DefaultRouter()
router.register(r'tags', FeedbackTagViewSet)
router.register(r'feedback', EventFeedbackViewSet)

urlpatterns = [
    path('', include(router.urls)),
]