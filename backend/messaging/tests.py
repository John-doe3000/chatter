from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from io import BytesIO
from groups.models import Group, Membership
from .models import Message, Attachment

User = get_user_model()


class MessageAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create users
        self.user1 = User.objects.create_user(username='user1', password='pass1')
        self.user2 = User.objects.create_user(username='user2', password='pass2')
        self.user3 = User.objects.create_user(username='user3', password='pass3')

        # Create group and memberships
        self.group = Group.objects.create(name='Test Group', owner=self.user1)
        Membership.objects.create(user=self.user1, group=self.group, role=Membership.Role.HEAD_ADMIN)
        Membership.objects.create(user=self.user2, group=self.group, role=Membership.Role.MEMBER)

    def test_send_text_message(self):
        """Test creating a text-only message."""
        self.client.force_authenticate(user=self.user1)

        data = {'body': 'Hello, group!'}
        response = self.client.post(
            f'/api/groups/{self.group.id}/messages/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['body'], 'Hello, group!')
        self.assertEqual(response.data['sender_username'], 'user1')
        self.assertEqual(response.data['attachments'], [])

        # Verify message was created
        self.assertTrue(Message.objects.filter(group=self.group, body='Hello, group!').exists())

    def test_send_message_with_attachment(self):
        """Test creating a message with an attachment."""
        self.client.force_authenticate(user=self.user1)

        # Create a simple image file
        image_data = BytesIO(b'fake image data')
        image_data.name = 'test.jpg'

        data = {
            'body': 'Check this image',
            'attachment': image_data,
            'kind': 'image'
        }
        response = self.client.post(
            f'/api/groups/{self.group.id}/messages/',
            data,
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['body'], 'Check this image')
        self.assertEqual(len(response.data['attachments']), 1)
        self.assertEqual(response.data['attachments'][0]['kind'], 'image')

        # Verify attachment was created
        message = Message.objects.get(id=response.data['id'])
        self.assertEqual(message.attachments.count(), 1)
        self.assertEqual(message.attachments.first().kind, 'image')

    def test_send_attachment_only_message(self):
        """Test creating a message with only attachment (no body)."""
        self.client.force_authenticate(user=self.user1)

        audio_data = BytesIO(b'fake audio data')
        audio_data.name = 'test.mp3'

        data = {
            'attachment': audio_data,
            'kind': 'voice'
        }
        response = self.client.post(
            f'/api/groups/{self.group.id}/messages/',
            data,
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data['body'])
        self.assertEqual(len(response.data['attachments']), 1)
        self.assertEqual(response.data['attachments'][0]['kind'], 'voice')

    def test_message_requires_body_or_attachment(self):
        """Test that at least body or attachment is required."""
        self.client.force_authenticate(user=self.user1)

        data = {}
        response = self.client.post(
            f'/api/groups/{self.group.id}/messages/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_attachment_requires_kind(self):
        """Test that kind is required when attachment is provided."""
        self.client.force_authenticate(user=self.user1)

        image_data = BytesIO(b'fake image data')
        image_data.name = 'test.jpg'

        data = {
            'attachment': image_data
        }
        response = self.client.post(
            f'/api/groups/{self.group.id}/messages/',
            data,
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_poll_messages_without_since(self):
        """Test polling messages without since parameter."""
        self.client.force_authenticate(user=self.user1)

        # Create test messages
        Message.objects.create(group=self.group, sender=self.user1, body='Message 1')
        Message.objects.create(group=self.group, sender=self.user2, body='Message 2')
        Message.objects.create(group=self.group, sender=self.user1, body='Message 3')

        response = self.client.get(f'/api/groups/{self.group.id}/messages/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)

        # Verify ordering is by created_at descending
        self.assertEqual(response.data['results'][0]['body'], 'Message 3')
        self.assertEqual(response.data['results'][1]['body'], 'Message 2')
        self.assertEqual(response.data['results'][2]['body'], 'Message 1')

    def test_poll_messages_with_since(self):
        """Test polling messages with since parameter."""
        self.client.force_authenticate(user=self.user1)

        # Create messages with timestamps
        msg1 = Message.objects.create(group=self.group, sender=self.user1, body='Message 1')
        msg1.created_at = timezone.datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.UTC)
        msg1.save()

        msg2 = Message.objects.create(group=self.group, sender=self.user2, body='Message 2')
        msg2.created_at = timezone.datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.UTC)
        msg2.save()

        msg3 = Message.objects.create(group=self.group, sender=self.user1, body='Message 3')
        msg3.created_at = timezone.datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.UTC)
        msg3.save()

        # Poll since msg1's creation time
        since = timezone.datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.UTC).isoformat()
        response = self.client.get(
            f'/api/groups/{self.group.id}/messages/',
            {'since': since}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return msg2 and msg3 (created after msg1)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['body'], 'Message 3')
        self.assertEqual(response.data['results'][1]['body'], 'Message 2')

    def test_cursor_pagination(self):
        """Test cursor-based pagination."""
        self.client.force_authenticate(user=self.user1)

        # Create multiple messages (more than page_size)
        for i in range(25):
            Message.objects.create(group=self.group, sender=self.user1, body=f'Message {i}')

        response = self.client.get(f'/api/groups/{self.group.id}/messages/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 20)  # page_size is 20
        self.assertIsNotNone(response.data.get('next'))

        # Fetch next page
        next_url = response.data['next']
        self.assertIn('cursor=', next_url)

    def test_non_member_cannot_access_messages(self):
        """Test that non-members cannot access group messages."""
        self.client.force_authenticate(user=self.user3)

        Message.objects.create(group=self.group, sender=self.user1, body='Message 1')

        response = self.client.get(f'/api/groups/{self.group.id}/messages/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_member_cannot_post_messages(self):
        """Test that non-members cannot post messages to group."""
        self.client.force_authenticate(user=self.user3)

        data = {'body': 'Unauthorized message'}
        response = self.client.post(
            f'/api/groups/{self.group.id}/messages/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_access_messages(self):
        """Test that unauthenticated users cannot access messages."""
        response = self.client.get(f'/api/groups/{self.group.id}/messages/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_message_includes_sender_username(self):
        """Test that message response includes sender username."""
        self.client.force_authenticate(user=self.user1)

        Message.objects.create(group=self.group, sender=self.user1, body='Test message')

        response = self.client.get(f'/api/groups/{self.group.id}/messages/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['sender_username'], 'user1')

    def test_message_includes_attachments(self):
        """Test that message response includes attachments."""
        self.client.force_authenticate(user=self.user1)

        message = Message.objects.create(group=self.group, sender=self.user1, body='With attachment')
        Attachment.objects.create(message=message, file='test.jpg', kind=Attachment.Kind.IMAGE)

        response = self.client.get(f'/api/groups/{self.group.id}/messages/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results'][0]['attachments']), 1)

    # --- Attachment validation tests ---

    def _create_test_file(self, content, filename, content_type):
        """Helper to create a test file with specific content type."""
        file_obj = BytesIO(content)
        file_obj.name = filename
        file_obj.content_type = content_type
        return file_obj

    def test_image_attachment_valid_jpeg(self):
        """Test that valid JPEG image is accepted."""
        self.client.force_authenticate(user=self.user1)

        image_data = self._create_test_file(b'fake jpeg data', 'test.jpg', 'image/jpeg')

        data = {
            'body': 'JPEG image',
            'attachment': image_data,
            'kind': 'image'
        }
        response = self.client.post(
            f'/api/groups/{self.group.id}/messages/',
            data,
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['attachments'][0]['kind'], 'image')

    def test_image_attachment_valid_png(self):
        """Test that valid PNG image is accepted."""
        self.client.force_authenticate(user=self.user1)

        image_data = self._create_test_file(b'fake png data', 'test.png', 'image/png')

        data = {
            'body': 'PNG image',
            'attachment': image_data,
            'kind': 'image'
        }
        response = self.client.post(
            f'/api/groups/{self.group.id}/messages/',
            data,
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['attachments'][0]['kind'], 'image')

    def test_image_attachment_invalid_mime_type(self):
        """Test that invalid MIME type for image is rejected."""
        self.client.force_authenticate(user=self.user1)

        # Try to upload a GIF as image
        image_data = self._create_test_file(b'fake gif data', 'test.gif', 'image/gif')

        data = {
            'body': 'GIF image',
            'attachment': image_data,
            'kind': 'image'
        }
        response = self.client.post(
            f'/api/groups/{self.group.id}/messages/',
            data,
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid MIME type', str(response.data))

    def test_image_attachment_oversize(self):
        """Test that oversized image is rejected (max 10 MB)."""
        self.client.force_authenticate(user=self.user1)

        # Create a file larger than 10 MB
        large_content = b'x' * (11 * 1024 * 1024)  # 11 MB
        image_data = self._create_test_file(large_content, 'large.jpg', 'image/jpeg')

        data = {
            'body': 'Large image',
            'attachment': image_data,
            'kind': 'image'
        }
        response = self.client.post(
            f'/api/groups/{self.group.id}/messages/',
            data,
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('exceeds maximum allowed', str(response.data))

    def test_video_attachment_valid_mp4(self):
        """Test that valid MP4 video is accepted."""
        self.client.force_authenticate(user=self.user1)

        video_data = self._create_test_file(b'fake mp4 data', 'test.mp4', 'video/mp4')

        data = {
            'body': 'MP4 video',
            'attachment': video_data,
            'kind': 'video'
        }
        response = self.client.post(
            f'/api/groups/{self.group.id}/messages/',
            data,
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['attachments'][0]['kind'], 'video')

    def test_video_attachment_invalid_mime_type(self):
        """Test that invalid MIME type for video is rejected."""
        self.client.force_authenticate(user=self.user1)

        # Try to upload a WebM as video
        video_data = self._create_test_file(b'fake webm data', 'test.webm', 'video/webm')

        data = {
            'body': 'WebM video',
            'attachment': video_data,
            'kind': 'video'
        }
        response = self.client.post(
            f'/api/groups/{self.group.id}/messages/',
            data,
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid MIME type', str(response.data))

    def test_video_attachment_oversize(self):
        """Test that oversized video is rejected (max 50 MB)."""
        self.client.force_authenticate(user=self.user1)

        # Create a file larger than 50 MB
        large_content = b'x' * (51 * 1024 * 1024)  # 51 MB
        video_data = self._create_test_file(large_content, 'large.mp4', 'video/mp4')

        data = {
            'body': 'Large video',
            'attachment': video_data,
            'kind': 'video'
        }
        response = self.client.post(
            f'/api/groups/{self.group.id}/messages/',
            data,
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('exceeds maximum allowed', str(response.data))

    def test_voice_attachment_valid_aac(self):
        """Test that valid AAC audio is accepted."""
        self.client.force_authenticate(user=self.user1)

        audio_data = self._create_test_file(b'fake aac data', 'test.aac', 'audio/aac')

        data = {
            'body': 'AAC voice',
            'attachment': audio_data,
            'kind': 'voice'
        }
        response = self.client.post(
            f'/api/groups/{self.group.id}/messages/',
            data,
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['attachments'][0]['kind'], 'voice')

    def test_voice_attachment_valid_mp4(self):
        """Test that valid MP4 audio is accepted."""
        self.client.force_authenticate(user=self.user1)

        audio_data = self._create_test_file(b'fake mp4 audio data', 'test.m4a', 'audio/mp4')

        data = {
            'body': 'MP4 voice',
            'attachment': audio_data,
            'kind': 'voice'
        }
        response = self.client.post(
            f'/api/groups/{self.group.id}/messages/',
            data,
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['attachments'][0]['kind'], 'voice')

    def test_voice_attachment_valid_mpeg(self):
        """Test that valid MPEG audio is accepted."""
        self.client.force_authenticate(user=self.user1)

        audio_data = self._create_test_file(b'fake mpeg data', 'test.mp3', 'audio/mpeg')

        data = {
            'body': 'MPEG voice',
            'attachment': audio_data,
            'kind': 'voice'
        }
        response = self.client.post(
            f'/api/groups/{self.group.id}/messages/',
            data,
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['attachments'][0]['kind'], 'voice')

    def test_voice_attachment_invalid_mime_type(self):
        """Test that invalid MIME type for voice is rejected."""
        self.client.force_authenticate(user=self.user1)

        # Try to upload a WAV as voice
        audio_data = self._create_test_file(b'fake wav data', 'test.wav', 'audio/wav')

        data = {
            'body': 'WAV voice',
            'attachment': audio_data,
            'kind': 'voice'
        }
        response = self.client.post(
            f'/api/groups/{self.group.id}/messages/',
            data,
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid MIME type', str(response.data))

    def test_voice_attachment_oversize(self):
        """Test that oversized voice is rejected (max 10 MB)."""
        self.client.force_authenticate(user=self.user1)

        # Create a file larger than 10 MB
        large_content = b'x' * (11 * 1024 * 1024)  # 11 MB
        audio_data = self._create_test_file(large_content, 'large.mp3', 'audio/mpeg')

        data = {
            'body': 'Large voice',
            'attachment': audio_data,
            'kind': 'voice'
        }
        response = self.client.post(
            f'/api/groups/{self.group.id}/messages/',
            data,
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('exceeds maximum allowed', str(response.data))

    # --- Media file access tests ---

    def test_attachment_media_access_as_member(self):
        """Test that group member can access attachment media."""
        self.client.force_authenticate(user=self.user1)

        # Create message with attachment
        message = Message.objects.create(group=self.group, sender=self.user1, body='With attachment')
        attachment = Attachment.objects.create(
            message=message,
            file='test.jpg',
            kind=Attachment.Kind.IMAGE
        )

        # Access the attachment media
        response = self.client.get(f'/api/attachments/{attachment.id}/')

        # Should succeed (or 404 if file doesn't exist physically, but not 403)
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_attachment_media_access_as_non_member(self):
        """Test that non-member cannot access attachment media."""
        self.client.force_authenticate(user=self.user3)

        # Create message with attachment
        message = Message.objects.create(group=self.group, sender=self.user1, body='With attachment')
        attachment = Attachment.objects.create(
            message=message,
            file='test.jpg',
            kind=Attachment.Kind.IMAGE
        )

        # Access the attachment media
        response = self.client.get(f'/api/attachments/{attachment.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_attachment_media_access_unauthenticated(self):
        """Test that unauthenticated user cannot access attachment media."""
        # Create message with attachment
        message = Message.objects.create(group=self.group, sender=self.user1, body='With attachment')
        attachment = Attachment.objects.create(
            message=message,
            file='test.jpg',
            kind=Attachment.Kind.IMAGE
        )

        # Access the attachment media without authentication
        response = self.client.get(f'/api/attachments/{attachment.id}/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_attachment_media_not_found(self):
        """Test that accessing non-existent attachment returns 404."""
        self.client.force_authenticate(user=self.user1)

        response = self.client.get('/api/attachments/99999/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
