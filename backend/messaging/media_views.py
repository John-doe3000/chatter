"""
Views for serving media files with authentication and authorization.
"""
import os
from django.http import FileResponse, Http404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from groups.models import Membership
from .models import Attachment


class AttachmentMediaView(APIView):
    """
    Serve attachment media files only to authenticated users who are members
    of the message's group.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, attachment_id):
        try:
            attachment = Attachment.objects.select_related('message__group').get(id=attachment_id)
        except Attachment.DoesNotExist:
            raise Http404("Attachment not found")

        # Check if user is a member of the message's group
        group = attachment.message.group
        if not Membership.objects.filter(user=request.user, group=group).exists():
            return Response(
                {'detail': 'You must be a member of this group to access this attachment.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if file exists
        file_path = attachment.file.path
        if not os.path.exists(file_path):
            raise Http404("File not found")

        # Serve the file
        response = FileResponse(
            open(file_path, 'rb'),
            content_type=attachment.file.content_type or 'application/octet-stream'
        )
        response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_path)}"'
        return response