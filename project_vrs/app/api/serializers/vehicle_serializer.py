from rest_framework import serializers
from ..models import Vehicle

class VehicleSerializer(serializers.ModelSerializer):
    vehicle_type_name = serializers.CharField(source="vehicle_type.vehicle_type", read_only=True)
    engine_type_name = serializers.CharField(source="engine_type.engine_type", read_only=True)
    model_name = serializers.CharField(source="models.model_name", read_only=True)

    class Meta:
        model = Vehicle
        fields = [
            "id",
            "car_plate_number",
            "amount_seats",
            "price_per_day",
            "vehicle_type",
            "vehicle_type_name",
            "engine_type",
            "engine_type_name",
            "models",
            "model_name",
        ]
