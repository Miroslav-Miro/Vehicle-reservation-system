from rest_framework import serializers
from ..models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "recipient",
            "message",
            "type",
            "created_at",
            "is_read",
        ]
        read_only_fields = ["id", "recipient", "created_at"]

    def to_representation(self, instance):
        """Optional: make output cleaner for the frontend"""
        rep = super().to_representation(instance)
        # Ensure type always has a value
        rep["type"] = rep["type"] or "info"
        return rep
