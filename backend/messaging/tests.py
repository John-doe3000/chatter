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
