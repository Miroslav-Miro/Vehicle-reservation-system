from rest_framework import serializers
from ..models import *

class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    Converts JSON data to a User model instance.

    :param serializers: The Django REST framework serializers module.
    :type serializers: module
    :raises serializers.ValidationError: If the default role 'user' does not exist.
    :return: The created user instance.
    :rtype: User
    """
    class Meta:
        """
        Meta class for RegisterSerializer.
        Specifies the model and fields to be used in the serializer.
        """
        model = User
        fields = ["username", "email", "password", "first_name", "last_name", "address", "date_of_birth", "phone_number"]
    def create(self, validated_data):
        try:
            user_role = Role.objects.get(role_name="user")
        except:
            raise serializers.ValidationError("Default role 'user' does not exist. Please create it first.")
        
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            address=validated_data.get("address", ""),
            date_of_birth=validated_data.get("date_of_birth"),
            phone_number=validated_data.get("phone_number", ""),
            role_id=user_role
        )
        return user