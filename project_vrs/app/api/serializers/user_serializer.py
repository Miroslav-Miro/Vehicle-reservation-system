# api/serializers/user_serializer.py
from rest_framework import serializers
from ..models import User

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for normal users (limited fields).

    :param serializers: The Django REST framework serializers module.
    :type serializers: module
    """

    class Meta:
        """
        All fields that a user can change
        from profile settings
        """

        model = User
        fields = [
            "first_name",
            "last_name",
            "address",
            "date_of_birth",
            "phone_number",
        ]


class AdminUserProfilesSerializer(serializers.ModelSerializer):
    """
    Serializer for admins (full control).

    :param serializers: The Django REST framework serializers module.
    :type serializers: module
    """

    class Meta:
        model = User
        fields = "__all__"
