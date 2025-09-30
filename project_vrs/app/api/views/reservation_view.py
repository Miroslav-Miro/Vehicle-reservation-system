from math import ceil
from decimal import Decimal

from django.db import transaction

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Prefetch
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from ..custom_permissions.mixed_role_permissions import RoleRequired
from ..models import (
    Reservation,
    PhysicalVehicleReservation,
    PhysicalVehicle,
    Location,
    ReservationStatus,
    Notification
)
from ..serializers.reservation_serializer import (
    ReservationSerializer,
    CancelReservationSerializer,
    ReservationCreateSerializer,
)
from ..utils.broadcast import broadcast_notification


# Allowed status
HISTORY_STATUSES = {"cancelled", "completed", "no_show", "failed_payment"}
ACTIVE_STATUSES = {"pending", "confirmed", "active"}

# def broadcast_notification(message, recipient_ids=None, roles=None):
#     channel_layer = get_channel_layer()

#     # Store in DB
#     if recipient_ids:
#         for uid in recipient_ids:
#             Notification.objects.create(
#                 recipient_id=uid,
#                 message=message.get("message") or message.get("action"),
#                 type=message.get("action"),
#             )

#     # Live push
#     if recipient_ids:
#         for uid in recipient_ids:
#             async_to_sync(channel_layer.group_send)(
#                 f"user_{uid}", {"type": "notify", "message": message}
#             )

#     if roles:
#         for role in roles:
#             async_to_sync(channel_layer.group_send)(
#                 role, {"type": "notify", "message": message}
#             )
class ReservationViewSet(viewsets.ModelViewSet):
    """
    User-facing reservations API.
    """
    
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
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Accepts payload:
        {
          "start": "...ISO...",
          "end": "...ISO...",
          "start_location_id": 1,
          "end_location_id": 2,   // optional, defaults to start_location_id
          "lines": [{ "vehicle_id": 7, "qty": 2 }, ...]
        }
        """
        write_ser = ReservationCreateSerializer(data=request.data)
        write_ser.is_valid(raise_exception=True)
        data = write_ser.validated_data

        start = data["start"]
        end = data["end"]
        pickup_id = data["start_location_id"]
        dropoff_id = data.get("end_location_id") or pickup_id
        lines = data["lines"]

        # locations
        pickup = Location.objects.filter(pk=pickup_id).first()
        if not pickup:
            return Response({"detail": "Invalid start_location_id."}, status=400)
        dropoff = Location.objects.filter(pk=dropoff_id).first()
        if not dropoff:
            return Response({"detail": "Invalid end_location_id."}, status=400)

        # merge duplicate conceptual vehicles
        qty_by_vid = {}
        for line in lines:
            vid = int(line["vehicle_id"])
            qty_by_vid[vid] = qty_by_vid.get(vid, 0) + int(line["qty"])

        # choose physical units at pickup location, excluding overlaps
        chosen_units = []
        BLOCKING_STATUSES = {"pending", "confirmed", "active"}
        for vid, qty in qty_by_vid.items():
            qs = (
                PhysicalVehicle.objects
                .filter(vehicle_id=vid, location_id=pickup_id)
                .exclude(
                    physicalvehiclereservation__reservation__start_date__lt=end,
                    physicalvehiclereservation__reservation__end_date__gt=start,
                    physicalvehiclereservation__reservation__status__status__in=BLOCKING_STATUSES,
                )
                .select_for_update(skip_locked=True)
                .order_by("id")
            )

            available = list(qs.values_list("id", flat=True))
            if len(available) < qty:
                return Response(
                    {
                        "detail": (
                            f"Need {qty}, only {len(available)} units of vehicle {vid} "
                            f"free at location {pickup_id} between {start.isoformat()} and {end.isoformat()}."
                        )
                    },
                    status=400,
                )

            # fetch the actual unit rows for attaching
            chosen_units.extend(list(PhysicalVehicle.objects.filter(id__in=available[:qty])))

        # status
        try:
            pending = ReservationStatus.objects.get(status__iexact="pending")
        except ReservationStatus.DoesNotExist:
            return Response({"detail": "Missing ReservationStatus 'pending'."}, status=500)

        # compute rental days (ceil to whole days, min 1)
        seconds = (end - start).total_seconds()
        days = max(1, ceil(seconds / 86400.0))

        # create reservation
        res = Reservation.objects.create(
            user=request.user,
            start_date=start,
            end_date=end,
            status=pending,
            pickup_location=pickup,
            dropoff_location=dropoff,
            total_price=Decimal("0.00"),
        )

        # attach items & compute total
        total = Decimal("0.00")
        # we need unit rows with vehicle fk; they were fetched above
        for u in chosen_units:
            PhysicalVehicleReservation.objects.create(reservation=res, physical_vehicle=u)
            total += u.vehicle.price_per_day * days

        res.total_price = total
        res.save(update_fields=["total_price"])

        read_ser = ReservationSerializer(res, context={"request": request})

        # Broadcast notification to user and managers
        payload = {
            "action": "created",
            "reservation": read_ser.data,
            "message": f"Reservation #{res.id} created",
        }
        broadcast_notification(payload, user_id=request.user.id, roles=["managers"])

        return Response(read_ser.data, status=status.HTTP_201_CREATED)

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

        # transition rules: allow cancel from pending or confirmed
        current = (reservation.status.status or "").lower()
        if current not in {"pending", "confirmed"}:
            return Response(
                {"detail": f"Cannot cancel from status '{current}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Apply transition
        cancel_status = ReservationStatus.objects.get(status__iexact="cancelled")
        reservation.status = cancel_status
        reservation.save(update_fields=["status"])

        payload = {
            "action": "cancelled",
            "reservation": ReservationSerializer(reservation, context={"request": request}).data,
            "message": f"Reservation #{reservation.id} cancelled",
        }

        # fire only after the DB row is committed so GET sees it
        transaction.on_commit(lambda: broadcast_notification(
            payload,
            user_id=request.user.id,      # persist for the creator
            roles=["managers"]            # live fanout to managers (persist for them is optional)
        ))

        return Response(
            ReservationSerializer(reservation, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )
