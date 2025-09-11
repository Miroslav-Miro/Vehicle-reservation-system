from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..custom_permissions.mixed_role_permissions import RoleRequired
from django.utils.timezone import now
from django.db.models import Prefetch

from ..models import Reservation, PhysicalVehicleReservation, PhysicalVehicle, ReservationStatus
from ..serializers.reservation_serializer import (
    ReservationDetailSerializer,
)

class ReservationViewSet(viewsets.ModelViewSet):
    """
    User-facing reservation management.
    - Create reservation
    - Cancel reservation
    - List active reservations
    - List history of reservations
    """
    serializer_class = ReservationDetailSerializer
    
    def get_permissions(self):
        return [RoleRequired("user")]

    def get_queryset(self):
        return (
            Reservation.objects.filter(user=self.request.user)
            .select_related("status")  
            .prefetch_related(
                Prefetch(
                    "physicalvehiclereservation_set",
                    queryset=PhysicalVehicleReservation.objects.select_related(
                        "physical_vehicle__vehicle"
                    ),
                )
            )
        )

