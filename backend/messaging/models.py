from django.db import models
from django.contrib.auth import get_user_model
from groups.models import Group

User = get_user_model()


class Message(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    body = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['group', '-created_at']),
        ]

    def __str__(self):
        return f'Message from {self.sender.username} in {self.group.name} at {self.created_at}'


class Attachment(models.Model):
    class Kind(models.TextChoices):
        IMAGE = 'image', 'Image'
        VIDEO = 'video', 'Video'
        VOICE = 'voice', 'Voice'

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='attachments/%Y/%m/%d/')
    kind = models.CharField(max_length=20, choices=Kind.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.kind} in Message {self.message.id}'
