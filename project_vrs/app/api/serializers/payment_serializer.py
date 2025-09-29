from datetime import date
from rest_framework import serializers


def luhn_ok(num: str) -> bool:
    total, alt = 0, False
    for ch in reversed(num):
        if not ch.isdigit():
            return False
        d = ord(ch) - 48
        if alt:
            d = d * 2
            if d > 9:
                d -= 9
        total += d
        alt = not alt
    return (total % 10) == 0


class MockCardPaymentSerializer(serializers.Serializer):
    """
    Mock payment request.
    """

    name_on_card = serializers.CharField(max_length=64)
    card_number = serializers.CharField(write_only=True, min_length=12, max_length=19)
    exp_month = serializers.IntegerField(min_value=1, max_value=12)
    exp_year = serializers.IntegerField(min_value=2000, max_value=2100)
    cvv = serializers.CharField(write_only=True, min_length=3, max_length=4)

    simulate = serializers.ChoiceField(choices=["success", "fail"], required=False)

    def validate_card_number(self, value: str) -> str:
        digits = value.replace(" ", "").replace("-", "")
        if not (12 <= len(digits) <= 19) or not digits.isdigit():
            raise serializers.ValidationError("Card number must be 12–19 digits.")
        if not luhn_ok(digits):
            raise serializers.ValidationError(
                "Invalid card number (Luhn check failed)."
            )
        return digits

    def validate(self, attrs):
        # Expiry: card valid through the END of the expiry month
        today = date.today()
        y, m = attrs["exp_year"], attrs["exp_month"]
        if (y < today.year) or (y == today.year and m < today.month):
            raise serializers.ValidationError({"exp_month": "Card is expired."})
        # Basic cvv check (digits only)
        if not attrs["cvv"].isdigit():
            raise serializers.ValidationError({"cvv": "CVV must be digits."})
        return attrs
