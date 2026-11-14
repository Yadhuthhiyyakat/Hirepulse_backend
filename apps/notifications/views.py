from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from .models import Notification
from .serializers import NotificationSerializer
from apps.common.utils import api_response

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = NotificationSerializer
    queryset = Notification.objects.all()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return Notification.objects.none()
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return api_response(
            success=True,
            data={'unread_count': count},
            message="Unread notification count retrieved"
        )

    @action(detail=True, methods=['patch'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return api_response(
            success=True,
            data=NotificationSerializer(notification).data,
            message="Notification marked as read"
        )

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return api_response(
            success=True,
            data={},
            message="All notifications marked as read"
        )
