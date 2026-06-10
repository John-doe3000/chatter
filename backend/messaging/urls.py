from django.urls import path
from . import views

urlpatterns = [
    path('groups/<int:group_id>/messages/', views.MessageListCreateView.as_view(), name='message-list-create'),
]
