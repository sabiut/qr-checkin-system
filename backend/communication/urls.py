from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MessageViewSet, AnnouncementViewSet, ForumThreadViewSet, ForumPostViewSet,
    QAQuestionViewSet, QAAnswerViewSet, IcebreakerActivityViewSet,
    IcebreakerResponseViewSet, NotificationPreferenceViewSet
)

router = DefaultRouter()
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'announcements', AnnouncementViewSet, basename='announcement')
router.register(r'forum/threads', ForumThreadViewSet, basename='forumthread')
router.register(r'forum/posts', ForumPostViewSet, basename='forumpost')
router.register(r'qa/questions', QAQuestionViewSet, basename='qaquestion')
router.register(r'qa/answers', QAAnswerViewSet, basename='qaanswer')
router.register(r'icebreakers', IcebreakerActivityViewSet, basename='icebreakerActivity')
router.register(r'icebreaker-responses', IcebreakerResponseViewSet, basename='icebreakerresponse')
router.register(r'notification-preferences', NotificationPreferenceViewSet, basename='notificationpreference')

urlpatterns = [
    path('api/communication/', include(router.urls)),
]
