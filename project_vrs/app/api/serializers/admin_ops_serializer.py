from rest_framework import serializers
from ..constants import (
    PENDING_PAYMENT,
    FAILED_PAYMENT,
    CONFIRMED,
    NO_SHOW,
    ACTIVE,
    COMPLETED,
    CANCELLED,
)

ALL_STATUSES = (
    PENDING_PAYMENT,
    FAILED_PAYMENT,
    CONFIRMED,
    NO_SHOW,
    ACTIVE,
    COMPLETED,
    CANCELLED,
)


class AdminUserKPISerializer(serializers.Serializer):
    total = serializers.IntegerField()
    active = serializers.IntegerField()
    blocked = serializers.IntegerField()
    new_7d = serializers.IntegerField()
    new_30d = serializers.IntegerField()


class AdminReservationKPISerializer(serializers.Serializer):
    total = serializers.IntegerField()
    active = serializers.IntegerField()
    final = serializers.IntegerField()
    by_status = serializers.DictField(child=serializers.IntegerField())
    revenue_last_30d = serializers.CharField()


class AdminKPISerializer(serializers.Serializer):
    users = AdminUserKPISerializer()
    reservations = AdminReservationKPISerializer()


class ReservationTransitionInputSerializer(serializers.Serializer):
    """
    Request body for the admin transition endpoint.
    Example: { "to": "CONFIRMED" }
    """

    to = serializers.ChoiceField(
        choices=ALL_STATUSES, help_text="Target status (UPPERCASE)."
    )

    def validate_to(self, value: str) -> str:
        return value.strip().upper()


class ReservationTransitionOptionsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    current = serializers.ChoiceField(choices=ALL_STATUSES)
    allowed_targets = serializers.ListField(
        child=serializers.ChoiceField(choices=ALL_STATUSES)
    )
    is_final = serializers.BooleanField()
