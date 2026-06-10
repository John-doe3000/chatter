from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from .models import Group, Membership, Invitation, Ban
from .serializers import (
    GroupSerializer, GroupDetailSerializer, CreateGroupSerializer,
    MembershipSerializer, InvitationSerializer, InviteUserSerializer,
    PromoteUserSerializer
)
from .permissions import IsGroupMember, IsGroupAdmin, IsGroupHeadAdmin

User = get_user_model()


class GroupViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = GroupSerializer

    def get_queryset(self):
        from django.db.models import Q
        return Group.objects.filter(
            Q(memberships__user=self.request.user) | Q(owner=self.request.user)
        ).distinct()

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateGroupSerializer
        elif self.action == 'retrieve':
            return GroupDetailSerializer
        return GroupSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = serializer.save()
        Membership.objects.create(
            user=request.user,
            group=group,
            role=Membership.Role.HEAD_ADMIN
        )
        return Response(GroupSerializer(group).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsGroupAdmin])
    def invite(self, request, pk=None):
        group = self.get_object()
        self.check_object_permissions(request, group)

        serializer = InviteUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        invited_user = get_object_or_404(User, username=serializer.validated_data['username'])

        if Ban.objects.filter(group=group, user=invited_user).exists():
            return Response(
                {'detail': 'This user is banned from the group.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if Membership.objects.filter(group=group, user=invited_user).exists():
            return Response(
                {'detail': 'User is already a member of this group.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        invitation, created = Invitation.objects.get_or_create(
            group=group,
            invited_user=invited_user,
            invited_by=request.user
        )

        return Response(InvitationSerializer(invitation).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def accept_invitation(self, request):
        invitation_id = request.data.get('invitation_id')
        invitation = get_object_or_404(Invitation, id=invitation_id, invited_user=request.user)

        if invitation.status != Invitation.Status.PENDING:
            return Response(
                {'detail': 'Invitation is no longer pending.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        invitation.status = Invitation.Status.ACCEPTED
        invitation.save()

        Membership.objects.create(
            user=request.user,
            group=invitation.group,
            role=Membership.Role.MEMBER
        )

        return Response(
            {'detail': 'Invitation accepted.'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def decline_invitation(self, request):
        invitation_id = request.data.get('invitation_id')
        invitation = get_object_or_404(Invitation, id=invitation_id, invited_user=request.user)

        if invitation.status != Invitation.Status.PENDING:
            return Response(
                {'detail': 'Invitation is no longer pending.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        invitation.status = Invitation.Status.DECLINED
        invitation.save()

        return Response(
            {'detail': 'Invitation declined.'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsGroupAdmin])
    def kick(self, request, pk=None):
        group = self.get_object()
        self.check_object_permissions(request, group)

        username = request.data.get('username')
        user_to_kick = get_object_or_404(User, username=username)

        membership = get_object_or_404(Membership, group=group, user=user_to_kick)
        membership.delete()

        return Response(
            {'detail': f'{username} has been kicked from the group.'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsGroupAdmin])
    def promote(self, request, pk=None):
        group = self.get_object()
        self.check_object_permissions(request, group)

        username = request.data.get('username')
        user_to_promote = get_object_or_404(User, username=username)

        serializer = PromoteUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        membership = get_object_or_404(Membership, group=group, user=user_to_promote)
        membership.role = serializer.validated_data['role']
        membership.save()

        return Response(MembershipSerializer(membership).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsGroupHeadAdmin])
    def ban(self, request, pk=None):
        group = self.get_object()
        self.check_object_permissions(request, group)

        username = request.data.get('username')
        user_to_ban = get_object_or_404(User, username=username)

        Ban.objects.get_or_create(group=group, user=user_to_ban, banned_by=request.user)

        Membership.objects.filter(group=group, user=user_to_ban).delete()
        Invitation.objects.filter(group=group, invited_user=user_to_ban).delete()

        return Response(
            {'detail': f'{username} has been banned from the group.'},
            status=status.HTTP_200_OK
        )
