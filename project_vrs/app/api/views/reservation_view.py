from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..custom_permissions.mixed_role_permissions import RoleRequired
from django.utils.timezone import now
from django.db.models import Prefetch

from ..models import Reservation, PhysicalVehicleReservation, PhysicalVehicle, ReservationStatus
from ..serializers.reservation_serializer import (
    ReservationSerializer, CancelReservationSerializer
)
from rest_framework.decorators import action
from rest_framework import status as drf_status

class ReservationViewSet(viewsets.ModelViewSet):
    serializer_class = ReservationSerializer
    http_method_names = ['get',"patch"]
    
    def get_permissions(self):
        return [RoleRequired("user")]

    def get_queryset(self):
        user_id = self.request.query_params.get("user_id")
        status = self.request.query_params.get("status")  
        qs = Reservation.objects.select_related(
            "status", "pickup_location", "dropoff_location", "user"
        ).prefetch_related(
            "physicalvehiclereservation_set__physical_vehicle__vehicle__brand",
            "physicalvehiclereservation_set__physical_vehicle__vehicle__model",
            "physicalvehiclereservation_set__physical_vehicle__vehicle__vehicle_type",
            "physicalvehiclereservation_set__physical_vehicle__vehicle__engine_type",
            "physicalvehiclereservation_set__physical_vehicle__location",
        )
        if user_id:
            qs = qs.filter(user_id=user_id)
        if status:
            if status.lower() == "history":
                qs = qs.filter(status__status__in=["cancelled", "completed"])
            else:
                qs = qs.filter(status__status__iexact=status)
        return qs
    
    def get_serializer_class(self):
        # Use CancelReservationSerializer only for PATCH
        if self.action == "partial_update":
            return CancelReservationSerializer
        return ReservationSerializer

    def partial_update(self, request, *args, **kwargs):
        serializer = CancelReservationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data["status"]
        if new_status.lower() != "cancelled":
            return Response(
                {"detail": "You can only change status to 'cancelled'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        reservation = self.get_object()
        cancelled_status = ReservationStatus.objects.get(status__iexact="cancelled")
        reservation.status = cancelled_status
        reservation.save(update_fields=["status"])

        return Response(self.get_serializer(reservation).data)

