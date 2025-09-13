from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<event_id>\w+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/announcements/(?P<event_id>\w+)/$', consumers.AnnouncementConsumer.as_asgi()),
    re_path(r'ws/forum/(?P<thread_id>\w+)/$', consumers.ForumConsumer.as_asgi()),
    re_path(r'ws/qa/(?P<event_id>\w+)/$', consumers.QAConsumer.as_asgi()),
]
