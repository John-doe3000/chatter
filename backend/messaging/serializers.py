from rest_framework import serializers
from .models import Message, Attachment


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

        return data

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
