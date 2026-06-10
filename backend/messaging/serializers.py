from rest_framework import serializers
from .models import Message, Attachment


# MIME type and size limits per attachment kind
ATTACHMENT_VALIDATION = {
    Attachment.Kind.IMAGE: {
        'mime_types': ['image/jpeg', 'image/png'],
        'max_size': 10 * 1024 * 1024,  # 10 MB
    },
    Attachment.Kind.VIDEO: {
        'mime_types': ['video/mp4'],
        'max_size': 50 * 1024 * 1024,  # 50 MB
    },
    Attachment.Kind.VOICE: {
        'mime_types': ['audio/aac', 'audio/mp4', 'audio/mpeg'],
        'max_size': 10 * 1024 * 1024,  # 10 MB
    },
}


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ('id', 'file', 'kind', 'created_at')
        read_only_fields = ('id', 'created_at')


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Message
        fields = ('id', 'group', 'sender', 'sender_username', 'body', 'attachments', 'created_at')
        read_only_fields = ('id', 'group', 'sender', 'created_at')


class MessageCreateSerializer(serializers.ModelSerializer):
    attachment = serializers.FileField(required=False, write_only=True)
    kind = serializers.ChoiceField(choices=Attachment.Kind.choices, required=False, write_only=True)

    class Meta:
        model = Message
        fields = ('body', 'attachment', 'kind')

    def validate(self, data):
        body = data.get('body')
        attachment = data.get('attachment')

        if not body and not attachment:
            raise serializers.ValidationError('Either body or attachment must be provided.')

        if attachment and not data.get('kind'):
            raise serializers.ValidationError('kind is required when attachment is provided.')

        # Validate attachment if provided
        if attachment:
            kind = data.get('kind')
            self._validate_attachment(attachment, kind)

        return data

    def _validate_attachment(self, file, kind):
        """Validate MIME type and size based on attachment kind."""
        validation_rules = ATTACHMENT_VALIDATION.get(kind)
        if not validation_rules:
            raise serializers.ValidationError(f'Invalid attachment kind: {kind}')

        # Check MIME type
        content_type = getattr(file, 'content_type', None)
        if content_type not in validation_rules['mime_types']:
            allowed = ', '.join(validation_rules['mime_types'])
            raise serializers.ValidationError(
                f'Invalid MIME type for {kind}: {content_type}. Allowed: {allowed}'
            )

        # Check file size
        if file.size > validation_rules['max_size']:
            max_mb = validation_rules['max_size'] / (1024 * 1024)
            raise serializers.ValidationError(
                f'File size exceeds maximum allowed for {kind}: {max_mb} MB'
            )

    def create(self, validated_data):
        attachment_file = validated_data.pop('attachment', None)
        kind = validated_data.pop('kind', None)

        message = Message.objects.create(**validated_data)

        if attachment_file:
            Attachment.objects.create(
                message=message,
                file=attachment_file,
                kind=kind
            )

        return message
