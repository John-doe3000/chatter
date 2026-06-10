from django.urls import path
from . import views
from .media_views import AttachmentMediaView

urlpatterns = [
    path('groups/<int:group_id>/messages/', views.MessageListCreateView.as_view(), name='message-list-create'),
    path('attachments/<int:attachment_id>/', AttachmentMediaView.as_view(), name='attachment-media'),
]
