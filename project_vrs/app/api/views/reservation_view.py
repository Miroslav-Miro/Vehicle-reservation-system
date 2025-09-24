from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Prefetch

from ..custom_permissions.mixed_role_permissions import RoleRequired
from ..models import (
    Reservation,
    PhysicalVehicleReservation,
    PhysicalVehicle,
)
from ..serializers.reservation_serializer import (
    ReservationSerializer,
    CancelReservationSerializer,
    ReservationCreateSerializer,
)


# Allowed status
HISTORY_STATUSES = {"CANCELLED", "COMPLETED", "NO_SHOW", "FAILED_PAYMENT"}
ACTIVE_STATUSES = {"PENDING_PAYMENT", "CONFIRMED", "ACTIVE"}


class ReservationViewSet(viewsets.ModelViewSet):
    """
    User-facing reservations API.
    """

    permission_classes = [IsAuthenticated, RoleRequired("user")]
    serializer_class = ReservationSerializer

    def get_permissions(self):
        """
        Return a list of permission instances depending on the HTTP method
        """
        if self.request.method in ("GET", "HEAD", "OPTIONS", "POST", "PATCH"):
            return [RoleRequired("user", "manager", "admin")]
        return [RoleRequired("manager", "admin")]

    def get_queryset(self):
        """
        Always scope to the authenticated user's reservations.
        """
        user = self.request.user

        base = (
            Reservation.objects.select_related(
                "status", "pickup_location", "dropoff_location", "user"
            )
            .prefetch_related(
                Prefetch(
                    "physicalvehiclereservation_set",
                    queryset=PhysicalVehicleReservation.objects.select_related(
                        "physical_vehicle",
                        "physical_vehicle__vehicle",
                        "physical_vehicle__vehicle__model",
                        "physical_vehicle__vehicle__model__brand",
                        "physical_vehicle__location",
                    ),
                )
            )
            .filter(user_id=user.id)
            .order_by("-created_at")
        )

        status_filter = (self.request.query_params.get("status") or "").lower()
        if status_filter == "history":
            return base.filter(status__status__in=HISTORY_STATUSES)
        if status_filter == "active":
            return base.filter(status__status__in=ACTIVE_STATUSES)
        return base

    # Serializer dispatch

    def get_serializer_class(self):
        """
        Use a write serializer only for create; otherwise the read serializer.
        """
        if self.action == "create":
            return ReservationCreateSerializer
        if self.action == "partial_update":
            return CancelReservationSerializer
        return ReservationSerializer

    # Create (PENDING_PAYMENT)
    def create(self, request, *args, **kwargs):
        """
        Create a reservation in PENDING_PAYMENT with a short hold.
        Returns the canonical read shape.
        """
        write_ser = self.get_serializer(data=request.data, context={"request": request})
        write_ser.is_valid(raise_exception=True)
        reservation = write_ser.save()  # ReservationCreateSerializer.create()

        read_ser = ReservationSerializer(reservation, context={"request": request})
        headers = self.get_success_headers(read_ser.data)
        return Response(read_ser.data, status=status.HTTP_201_CREATED, headers=headers)

    # Quote (no writing)
    @action(detail=False, methods=["post"], url_path="quote")
    def quote(self, request):
        """
        POST /api/user_reservations/quote
        Body: { "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", "vehicle_ids": [..] }
        Returns {"days", "total", "lines":[...] } WITHOUT creating a reservation.
        """
        tmp = ReservationCreateSerializer(
            data=request.data, context={"request": request}
        )
        tmp.is_valid(raise_exception=True)

        start = tmp.validated_data["start_date"]
        end = tmp.validated_data["end_date"]
        ids = tmp.validated_data["vehicle_ids"]
        days = (end - start).days

        units = list(
            PhysicalVehicle.objects.select_related(
                "vehicle", "vehicle__model", "vehicle__model__brand"
            ).filter(id__in=ids)
        )

        # Simple price preview
        total = sum(u.vehicle.price_per_day * days for u in units)
        lines = [
            {
                "physical_vehicle_id": u.id,
                "brand": u.vehicle.model.brand.brand_name,
                "model": u.vehicle.model.model_name,
                "day_price": str(u.vehicle.price_per_day),
                "days": days,
                "line_total": str(u.vehicle.price_per_day * days),
            }
            for u in units
        ]
        return Response({"days": days, "total": str(total), "lines": lines})

    # Cancel (PATCH)

    def partial_update(self, request, *args, **kwargs):
        """
        Only allow a user to cancel their own reservation,
        and only from allowed states.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reservation = self.get_object()

        # ownership check
        if reservation.user_id != request.user.id:
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        # transition rules allow cancel from PENDING_PAYMENT or CONFIRMED
        current = (reservation.status.status or "").upper()
        if current not in {"PENDING_PAYMENT", "CONFIRMED"}:
            return Response(
                {"detail": f"Cannot cancel from status '{current}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Apply transition
        reservation.status_id = reservation.status.__class__.objects.get(
            status__iexact="cancelled"
        ).id
        reservation.save(update_fields=["status"])

        return Response(
            ReservationSerializer(reservation).data, status=status.HTTP_200_OK
        )
