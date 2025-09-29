from datetime import date
from django.utils import timezone
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from api.models import Reservation, ReservationStatus
from api.constants import PENDING_PAYMENT, CONFIRMED, FAILED_PAYMENT
from api.custom_permissions.mixed_role_permissions import RoleRequired
from api.serializers.reservation_serializer import ReservationSerializer
from rest_framework import serializers
from api.serializers.payment_serializer import MockCardPaymentSerializer


def _status_id_ci(name: str) -> int:
    obj = ReservationStatus.objects.filter(status__iexact=name).first()
    if not obj:
        raise serializers.ValidationError(
            {"status": f"ReservationStatus('{name}') is missing. Seed it first."}
        )
    return obj.id


class MockPaymentView(APIView):
    """

    Body (JSON):
    {
      "name_on_card": "John Smith",
      "card_number": "4242 4242 4242 4242",
      "exp_month": 12,
      "exp_year": 2030,
      "cvv": "123",
    }

      Only works when reservation status == PENDING_PAYMENT and hold not expired.
      If success -> set CONFIRMED and clear hold_expires_at.
      -If fail    -> set FAILED_PAYMENT (hold remains so user can retry).
    """

    def get_permissions(self):
        return [IsAuthenticated(), RoleRequired("user", "manager", "admin")]

    @swagger_auto_schema(
        request_body=MockCardPaymentSerializer,
        responses={200: openapi.Response("OK", ReservationSerializer)},
        operation_summary="Mock card payment for a reservation",
        operation_description="Validates mock card data and flips status to CONFIRMED or FAILED_PAYMENT.",
    )
    @transaction.atomic
    def post(self, request, reservation_id: int):
        # Parse & validate body
        in_ser = MockCardPaymentSerializer(data=request.data)
        in_ser.is_valid(raise_exception=True)
        data = in_ser.validated_data

        # Load & lock reservation row (avoid races)
        res = (
            Reservation.objects.select_related("status", "user")
            .select_for_update()
            .filter(pk=reservation_id)
            .first()
        )
        if not res:
            return Response(
                {"detail": "Reservation not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # user pays only their own reservation unless manager/admin
        is_staffish = getattr(request.user, "is_staff", False)
        if res.user_id != request.user.id and not is_staffish:
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        current = (res.status.status or "").upper()
        if current != PENDING_PAYMENT:
            return Response(
                {
                    "detail": f"Mock payment allowed only from {PENDING_PAYMENT}, current is '{current}'."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # hold must still be valid
        now = timezone.now()
        if res.hold_expires_at and res.hold_expires_at <= now:
            return Response(
                {"detail": "Hold expired. Please start payment again."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # decision engine (mock)
        simulate = data.get("simulate")
        if simulate == "success":
            success = True
        elif simulate == "fail":
            success = False
        else:
            pan = data["card_number"]
            FAIL_PANS = {"4000000000000002", "4000000000009995"}
            success = pan not in FAIL_PANS

        # Apply transition
        target = CONFIRMED if success else FAILED_PAYMENT
        if success:
            res.hold_expires_at = None  # clear hold on success
        res.status_id = _status_id_ci(target)
        res.save(update_fields=["status", "hold_expires_at"])

        try:
            from api.email_sender.tasks import send_reservation_status_changed_email

            send_reservation_status_changed_email.delay(res.id, current, target)
        except Exception:
            pass

        return Response(ReservationSerializer(res).data, status=status.HTTP_200_OK)
