from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.pagination import CursorPagination
from django.utils.dateparse import parse_datetime
from django.shortcuts import get_object_or_404
from groups.models import Group
from groups.permissions import IsGroupMember
from .models import Message
from .serializers import MessageSerializer, MessageCreateSerializer


class MessageCursorPagination(CursorPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    ordering = '-created_at'
    cursor_query_param = 'cursor'


class MessageListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsGroupMember]
    pagination_class = MessageCursorPagination

    def get_queryset(self):
        group_id = self.kwargs['group_id']
        group = get_object_or_404(Group, id=group_id)
        self.check_object_permissions(self.request, group)

        queryset = Message.objects.filter(group=group).prefetch_related('attachments')

        since = self.request.query_params.get('since')
        if since:
            try:
                since_dt = parse_datetime(since)
                if since_dt:
                    queryset = queryset.filter(created_at__gt=since_dt)
            except (ValueError, TypeError):
                pass

        return queryset

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MessageCreateSerializer
        return MessageSerializer

    def get_group(self):
        group_id = self.kwargs['group_id']
        group = get_object_or_404(Group, id=group_id)
        self.check_object_permissions(self.request, group)
        return group

    def create(self, request, *args, **kwargs):
        group = self.get_group()
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = serializer.save(group=group, sender=request.user)
        output_serializer = MessageSerializer(message)

        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
