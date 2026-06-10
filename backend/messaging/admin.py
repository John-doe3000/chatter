from django.contrib import admin
from .models import Message, Attachment


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'group', 'sender', 'created_at')
    list_filter = ('group', 'created_at')
    search_fields = ('body', 'sender__username')
    readonly_fields = ('created_at',)


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'kind', 'created_at')
    list_filter = ('kind', 'created_at')
    readonly_fields = ('created_at',)
