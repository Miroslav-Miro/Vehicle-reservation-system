from rest_framework import viewsets, permissions
from ..models import Notification
from ..serializers.notification_serializer import NotificationSerializer
from ..custom_permissions.mixed_role_permissions import RoleRequired

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer

    def get_permissions(self):
        """
        Return a list of permission instances depending on the HTTP method
        """
        if self.request.method in ("GET", "HEAD", "OPTIONS", "POST", "PATCH"):
            return [RoleRequired("user", "manager", "admin")]
        return [RoleRequired("manager", "admin")]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by("-created_at")
