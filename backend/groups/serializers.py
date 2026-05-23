from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Group, Membership, Invitation, Ban

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')


class MembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Membership
        fields = ('id', 'user', 'role')


class GroupDetailSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    memberships = MembershipSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = ('id', 'name', 'owner', 'created_at', 'memberships')


class GroupSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)

    class Meta:
        model = Group
        fields = ('id', 'name', 'owner', 'created_at')


class InvitationSerializer(serializers.ModelSerializer):
    group = GroupSerializer(read_only=True)
    invited_user = UserSerializer(read_only=True)
    invited_by = UserSerializer(read_only=True)

    class Meta:
        model = Invitation
        fields = ('id', 'group', 'invited_user', 'invited_by', 'status', 'created_at')


class CreateGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('name',)

    def create(self, validated_data):
        user = self.context['request'].user
        return Group.objects.create(owner=user, **validated_data)


class InviteUserSerializer(serializers.Serializer):
    username = serializers.CharField()

    def validate_username(self, value):
        try:
            User.objects.get(username=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('User does not exist.')
        return value


class PromoteUserSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=['admin', 'head_admin'])
