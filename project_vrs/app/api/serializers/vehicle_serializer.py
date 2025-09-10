from rest_framework import serializers
from ..models import EngineType, Model, Vehicle, VehicleType


class VehicleSerializer(serializers.ModelSerializer):
    # READABLE names (read-only)
    vehicle_type_name = serializers.SlugRelatedField(
        source="vehicle_type", slug_field="vehicle_type", read_only=True
    )
    engine_type_name = serializers.SlugRelatedField(
        source="engine_type", slug_field="engine_type", read_only=True
    )
    model_name = serializers.SlugRelatedField(
        source="model", slug_field="model_name", read_only=True
    )

    # WRITABLE IDs (write-only) – keep only if you create/update via this serializer
    vehicle_type_id = serializers.PrimaryKeyRelatedField(
        source="vehicle_type", queryset=VehicleType.objects.all(), write_only=True
    )
    engine_type_id = serializers.PrimaryKeyRelatedField(
        source="engine_type", queryset=EngineType.objects.all(), write_only=True
    )
    model_id = serializers.PrimaryKeyRelatedField(
        source="model", queryset=Model.objects.all(), write_only=True
    )

    class Meta:
        model = Vehicle
        fields = [
            "id",
<<<<<<< Updated upstream
            # check "car_plate_number" before use
            # "car_plate_number",
=======
>>>>>>> Stashed changes
            "amount_seats",
            "price_per_day",
            # names for reading
            "vehicle_type_name",
            "engine_type_name",
            "model_name",
            # ids for writing
            "vehicle_type_id",
            "model_id",
            "engine_type_id",
        ]
