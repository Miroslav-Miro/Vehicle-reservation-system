from rest_framework import viewsets, permissions
from ..models import Vehicle
from ..serializers.vehicle_serializer import VehicleSerializer
from ..custom_permissions.mixed_role_permissions import RoleRequired


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [RoleRequired("user", "manager", "admin")]
        return [RoleRequired("manager", "admin")]
