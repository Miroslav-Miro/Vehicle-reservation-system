from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Sum, Q
from django.contrib.auth import get_user_model

from api.models import Reservation, ReservationStatus
from api.serializers.reservation_serializer import ReservationSerializer
from api.serializers.admin_ops_serializer import (
    ReservationTransitionInputSerializer,
    ReservationTransitionOptionsSerializer,
    AdminKPISerializer,
)
from api.custom_permissions.mixed_role_permissions import RoleRequired
from api.constants import (
    ACTIVE_STATUSES,
    OPS_ALLOWED_ACTIONS,
    ACTIVE,
    CONFIRMED,
    PENDING_PAYMENT,
    COMPLETED,
    CANCELLED,
    FINAL_STATUSES,
)
from django.conf import settings

HOLD_MINUTES = int(getattr(settings, "RESERVATION_HOLD_MINUTES", 15))

User = get_user_model()


class AdminKPIView(APIView):
    """
    Returns aggregated KPIs for users and reservations.
    """

    def get_permissions(self):
        return [IsAuthenticated(), RoleRequired("admin")]

    @swagger_auto_schema(
        responses={200: AdminKPISerializer},
        operation_summary="Admin: global KPIs",
        operation_description="Counts for users and reservations, plus 30-day revenue.",
    )
    def get(self, request):
        now = timezone.now()
        start_7d = now - timedelta(days=7)
        start_30d = now - timedelta(days=30)

        # Users KPIs
        users_total = User.objects.count()
        users_active = User.objects.filter(is_active=True).count()
        users_blocked = (
            getattr(User, "is_blocked", None)
            and User.objects.filter(is_blocked=True).count()
            or 0
        )
        users_new_7d = (
            User.objects.filter(created_at__gte=start_7d).count()
            if hasattr(User, "created_at")
            else 0
        )
        users_new_30d = (
            User.objects.filter(created_at__gte=start_30d).count()
            if hasattr(User, "created_at")
            else 0
        )

        # Reservations KPIs
        res_total = Reservation.objects.count()
        res_active = Reservation.objects.filter(
            status__status__in=ACTIVE_STATUSES
        ).count()
        res_final = Reservation.objects.filter(
            status__status__in=FINAL_STATUSES
        ).count()

        by_status_qs = Reservation.objects.values("status__status").annotate(
            c=Count("id")
        )
        status_counts = {row["status__status"]: row["c"] for row in by_status_qs}

        # consider revenue as total_price for new reservations in last 30d
        rev_30 = (
            Reservation.objects.filter(created_at__gte=start_30d)
            .aggregate(total=Sum("total_price"))
            .get("total")
            or 0
        )

        payload = {
            "users": {
                "total": users_total,
                "active": users_active,
                "blocked": users_blocked,
                "new_7d": users_new_7d,
                "new_30d": users_new_30d,
            },
            "reservations": {
                "total": res_total,
                "active": res_active,
                "final": res_final,
                "by_status": status_counts,
                "revenue_last_30d": str(rev_30),
            },
        }
        return Response(AdminKPISerializer(payload).data)


def _status_id_ci(name: str) -> int:
    obj = ReservationStatus.objects.filter(status__iexact=name).first()
    if not obj:
        # Let DRF convert this into a 400 automatically
        from rest_framework.exceptions import ValidationError

        raise ValidationError(
            {"status": f"ReservationStatus('{name}') is missing. Seed it first."}
        )
    return obj.id


class AdminReservationTransitionView(APIView):
    permission_classes = []

    def get_permissions(self):
        return [IsAuthenticated(), RoleRequired("admin")]

    @swagger_auto_schema(
        responses={200: ReservationTransitionOptionsSerializer, 404: "Not Found"},
        operation_summary="Admin: get allowed transitions",
        operation_description="Returns current status and allowed target statuses for this reservation.",
    )
    def get(self, request, pk: int):
        res = Reservation.objects.select_related("status").filter(pk=pk).first()
        if not res:
            return Response(
                {"detail": "Reservation not found."}, status=status.HTTP_404_NOT_FOUND
            )

        current = (res.status.status or "").upper()
        allowed = OPS_ALLOWED_ACTIONS.get(current, [])
        payload = {
            "id": res.id,
            "current": current,
            "allowed_targets": allowed,
            "is_final": current in FINAL_STATUSES,
        }
        return Response(
            ReservationTransitionOptionsSerializer(payload).data,
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        request_body=ReservationTransitionInputSerializer,  # <-- THIS makes Swagger show the 'to' field
        responses={200: ReservationSerializer, 400: "Bad Request", 404: "Not Found"},
        operation_summary="Admin: change reservation status",
        operation_description='Body example: {"to": "CONFIRMED"}',
    )
    @transaction.atomic
    def post(self, request, pk: int):
        in_ser = ReservationTransitionInputSerializer(data=request.data)
        in_ser.is_valid(raise_exception=True)
        target = in_ser.validated_data["to"]

        res = (
            Reservation.objects.select_related("status", "user")
            .select_for_update()
            .filter(pk=pk)
            .first()
        )
        if not res:
            return Response(
                {"detail": "Reservation not found."}, status=status.HTTP_404_NOT_FOUND
            )

        current = (res.status.status or "").upper()
        allowed = OPS_ALLOWED_ACTIONS.get(current, [])
        if target not in allowed:
            return Response(
                {
                    "detail": f"Cannot transition from {current} to {target}. Allowed: {allowed}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        now = timezone.now()
        if target == ACTIVE and res.start_date > now:
            return Response(
                {"detail": "Cannot mark ACTIVE before pickup time."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 4) Side effects
        if target == CONFIRMED:
            res.hold_expires_at = None
        elif target == PENDING_PAYMENT:
            res.hold_expires_at = now + timedelta(minutes=HOLD_MINUTES)
        elif target in (COMPLETED, CANCELLED):
            res.hold_expires_at = None

        # 5) Persist status
        res.status_id = _status_id_ci(target)
        res.save(update_fields=["status", "hold_expires_at"])

        # 6) Fire-and-forget email
        try:
            from api.email_sender.tasks import send_reservation_status_changed_email

            send_reservation_status_changed_email.delay(res.id, current, target)
        except Exception:
            pass

        # 7) Response
        return Response(ReservationSerializer(res).data, status=status.HTTP_200_OK)
