# api/serializers/user_serializer.py
from rest_framework import serializers
from ..models import User

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for normal users (limited fields)."""

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "address",
            "date_of_birth",
            "phone_number",
        ]


class AdminUserProfilesSerializer(serializers.ModelSerializer):
    """Serializer for admins (full control)."""

    class Meta:
        model = User
        fields = "__all__"
