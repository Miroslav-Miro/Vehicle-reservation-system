from uuid import uuid4
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from api.serializers.payment_serializer import MockCardPaymentSerializer


class MockPaymentAuthorizeView(APIView):
    """
    Validates card fields only. Does not touch reservations.
    If simulate != "fail", returns approved.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=MockCardPaymentSerializer,
        responses={
            200: openapi.Response(
                "Authorized",
                examples={
                    "application/json": {
                        "approved": True,
                        "auth_id": "e8f2b0e6-6f12-4f8b-9d0c-8b2a2b9d5a2e",
                        "brand": "VISA",
                        "last4": "4242",
                        "exp_month": 12,
                        "exp_year": 2030,
                    }
                },
            ),
            402: "Payment required (simulated failure)",
            400: "Validation error",
        },
    )
    def post(self, request):
        ser = MockCardPaymentSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        simulate = ser.validated_data.get("simulate") or "success"
        if simulate == "fail":
            return Response(
                {"approved": False, "reason": "Simulated failure"},
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )

        payload = {
            "approved": True,
            "auth_id": str(uuid4()),
            "brand": ser.validated_data["card_brand"],
            "last4": ser.validated_data["card_last4"],
            "exp_month": ser.validated_data["exp_month"],
            "exp_year": ser.validated_data["exp_year"],
        }
        return Response(payload, status=status.HTTP_200_OK)
