from datetime import date
import re
from rest_framework import serializers


def luhn_ok(num: str) -> bool:
    total, alt = 0, False
    for ch in reversed(num):
        if not ch.isdigit():
            return False
        d = ord(ch) - 48
        if alt:
            d *= 2
            if d > 9:
                d -= 9
        total += d
        alt = not alt
    return (total % 10) == 0


BRAND_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("VISA", re.compile(r"^4\d{12}(\d{3})?$")),
    (
        "MASTERCARD",
        re.compile(
            r"^(5[1-5]\d{14}|2(2[2-9]\d{12}|[3-6]\d{13}|7[01]\d{12}|720\d{12}))$"
        ),
    ),
    ("AMEX", re.compile(r"^3[47]\d{13}$")),
    ("DISCOVER", re.compile(r"^6(?:011|5\d{2})\d{12}$")),
]


def detect_brand(digits: str) -> str:
    for brand, pat in BRAND_PATTERNS:
        if pat.match(digits):
            return brand
    return "UNKNOWN"


class MockCardPaymentSerializer(serializers.Serializer):
    """
    Mock card authorization request.
    Validates card data and returns 'approved' for success.
    """

    name_on_card = serializers.CharField(max_length=64)
    card_number = serializers.CharField(write_only=True, min_length=12, max_length=19)
    exp_month = serializers.IntegerField(min_value=1, max_value=12)
    exp_year = serializers.IntegerField(min_value=2000, max_value=2100)
    cvv = serializers.CharField(write_only=True, min_length=3, max_length=4)

    simulate = serializers.ChoiceField(choices=["success", "fail"], required=False)

    card_brand = serializers.CharField(read_only=True)
    card_last4 = serializers.CharField(read_only=True)

    def validate_card_number(self, value: str) -> str:
        digits = value.replace(" ", "").replace("-", "")
        if not (12 <= len(digits) <= 19) or not digits.isdigit():
            raise serializers.ValidationError("Card number must be 12–19 digits.")
        if not luhn_ok(digits):
            raise serializers.ValidationError("Invalid card number (Luhn failed).")
        return digits

    def validate(self, attrs):
        today = date.today()
        y, m = attrs["exp_year"], attrs["exp_month"]
        if (y < today.year) or (y == today.year and m < today.month):
            raise serializers.ValidationError({"exp_month": "Card is expired."})

        if not attrs["cvv"].isdigit():
            raise serializers.ValidationError({"cvv": "CVV must be digits."})

        brand = detect_brand(attrs["card_number"])
        if brand == "AMEX" and len(attrs["cvv"]) != 4:
            raise serializers.ValidationError({"cvv": "AMEX requires 4-digit CVV."})
        if brand != "AMEX" and len(attrs["cvv"]) != 3:
            raise serializers.ValidationError({"cvv": "CVV must be 3 digits."})

        attrs["card_brand"] = brand
        attrs["card_last4"] = attrs["card_number"][-4:]
        return attrs
