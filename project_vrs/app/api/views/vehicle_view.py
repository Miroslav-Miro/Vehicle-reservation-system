from rest_framework import viewsets, permissions
from ..models import Vehicle
from ..serializers.vehicle_serializer import VehicleSerializer
from ..custom_permissions.mixed_role_permissions import RoleRequired
from rest_framework.permissions import IsAuthenticated


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            permission_classes = [RoleRequired("user", "manager", "admin")]
        else:
            permission_classes = [RoleRequired("manager", "admin")]
        return permission_classes