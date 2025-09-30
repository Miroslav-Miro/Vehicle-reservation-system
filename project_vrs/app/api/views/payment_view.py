from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from api.custom_permissions.mixed_role_permissions import RoleRequired
from api.serializers.payment_serializer import MockCardPaymentSerializer


class MockCardValidationView(APIView):
    """
    Validates mock card data using the serializer (Luhn, expiry, CVV).
    Returns 200 only if serializer passes and backend mock rules accept it.
    Does NOT touch reservations or the DB.
    """

    def get_permissions(self):
        return [IsAuthenticated(), RoleRequired("user", "manager", "admin")]

    @swagger_auto_schema(
        request_body=MockCardPaymentSerializer,
        responses={
            200: openapi.Response(
                "OK",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "ok": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "last4": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            400: "Validation error",
        },
        operation_summary="Validate mock card (serializer-driven)",
        operation_description="Uses MockCardPaymentSerializer to validate Luhn/expiry/CVV. "
                              "Backend decides acceptance; no reservation changes.",
    )
    def post(self, request):
        # 1) Run all field + object validations in the serializer
        ser = MockCardPaymentSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        vd = ser.validated_data  # <-- only trusted, normalized values beyond this point

        # 2) Backend-only decision (no 'simulate' from UI)
        #    You can tweak this list/rules as needed for demo declines.
        FAIL_PANS = {"4000000000000002", "4000000000009995"}  # classic Stripe-style test declines
        if vd["card_number"] in FAIL_PANS:
            # Surface a clean error message; serializer already guaranteed shape
            raise serializers.ValidationError({"detail": "Payment declined by mock gateway."})

        # 3) Success -> return minimal safe info (never echo full PAN)
        return Response(
            {"ok": True, "last4": vd["card_number"][-4:]},
            status=status.HTTP_200_OK,
        )

