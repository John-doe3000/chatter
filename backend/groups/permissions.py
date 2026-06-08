from rest_framework.permissions import BasePermission
from .models import Membership, Ban


class IsGroupMember(BasePermission):
    message = 'You must be a member of this group.'

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        return Membership.objects.filter(user=request.user, group=obj).exists()


class IsGroupAdmin(BasePermission):
    message = 'You must be an admin of this group.'

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        membership = Membership.objects.filter(user=request.user, group=obj).first()
        if not membership:
            return False
        return membership.role in [Membership.Role.ADMIN, Membership.Role.HEAD_ADMIN]


class IsGroupHeadAdmin(BasePermission):
    message = 'You must be the head admin of this group.'

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        membership = Membership.objects.filter(user=request.user, group=obj).first()
        if not membership:
            return False
        return membership.role == Membership.Role.HEAD_ADMIN
