"""
URL configuration for chatter project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('accounts.urls')),
    path('api/', include('groups.urls')),
    path('api/', include('messaging.urls')),
]
