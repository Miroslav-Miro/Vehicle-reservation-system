from rest_framework import serializers
from ..models import EngineType, Model, Vehicle, VehicleType, Brand, PhysicalVehicle, Location


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

    def validate_price_per_day(self, value):
        if value <= 0:
            raise serializers.ValidationError("price_per_day must be positive.")
        return value

    def validate(self, attrs):
        """
        Validate and normalize 'amount_seats'
        """

        seats = attrs.get("amount_seats", getattr(self.instance, "amount_seats", None))

        try:
            seats_int = int(seats)
        except (TypeError, ValueError):
            raise serializers.ValidationError(
                {"amount_seats": "Seats must be a number."}
            )

        if seats_int <= 0:
            raise serializers.ValidationError({"amount_seats": "Seats must be > 0."})

        return attrs


# Brand
class BrandSerializer(serializers.ModelSerializer):
    """
    Serializer for the Brand model.

    Fields:
      - id          (int, read-only): primary key (assigned by DB)
      - brand_name  (str, required)
    Behavior:
      - On input (create/update): expects 'brand_name'
      - On output (read): returns 'id' and 'brand_name'
    """

    class Meta:
        model = Brand
        fields = ["id", "brand_name"]
        extra_kwargs = {"brand_name": {"help_text": "Brand like 'BMW', 'Toyota'."}}

    def validate_brand_name(self, value: str) -> str:
        """
        Per-field validator for 'brand_name'.

        Steps:
        1. Strip whitespace ('  BMW  ' becomes 'BMW').
        2. Ensure it isn't empty after stripping.

        Raises:
          serializers.ValidationError if invalid.
        Returns:
          Cleaned brand_name.
        """
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Brand name cannot be empty.")
        return cleaned


# EngineType
"""
EngineType serializer
Examples: 'Petrol', 'Diesel', 'Hybrid', 'Electric'
"""


class EngineTypeSerializer(serializers.ModelSerializer):
    """
    Serializer for EngineType.

    Fields:
      - id          (int, read-only): primary key (assigned by DB)
      - engine_type  (str, required)
    Behavior:
      - On input (create/update): expects 'engine_type'
      - On output (read): returns 'id' and 'engine_type'
    """

    class Meta:
        model = EngineType
        fields = ["id", "engine_type"]

    # find way to reuse this code
    def validate_engine_type(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Engine type cannot be empty.")
        return cleaned


# VehicleType
"""
VehicleType serializer.

Examples: 'Sedan', 'SUV', 'Hatchback', 'Van'.
"""


class VehicleTypeSerializer(serializers.ModelSerializer):
    """
    Serializer for VehicleType.

    Fields:
      - id          (int, read-only): primary key (assigned by DB)
      - vehicle_type  (str, required)
    Behavior:
      - On input (create/update): expects 'vehicle_type'
      - On output (read): returns 'id' and 'vehicle_type'
    """

    class Meta:
        model = VehicleType
        fields = ["id", "vehicle_type"]

    def validate_vehicle_type(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Vehicle type cannot be empty.")
        return cleaned


# Model
"""
Model (car model) serializer

- A car "Model" belongs to a Brand (Brand='BMW', Model='3 Series')
- READ: show the 'brand_name' so responses are human-friendly
- WRITE: accept 'brand_id'(FK) to keep writes stable and explicit
"""


class ModelSerializer(serializers.ModelSerializer):
    # READ-ONLY field showing the brand name directly in responses.

    brand_name = serializers.SlugRelatedField(
        source="brand",
        slug_field="brand_name",
        read_only=True,
    )

    # WRITE-ONLY field accepting the brand by its ID to set 'brand' FK
    brand_id = serializers.PrimaryKeyRelatedField(
        source="brand",
        queryset=Brand.objects.all(),
        write_only=True,
    )

    class Meta:
        model = Model
        fields = ["id", "model_name", "brand_name", "brand_id"]

    def validate_model_name(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Model name cannot be empty.")
        return cleaned

    def validate(self, attrs: dict) -> dict:
        """
        Cross-field validation to ensure (brand, model_name)is unique.
        This prevents duplicates like ('BMW', '3 Series') appearing twice.

        - Pull intended brand + model_name from incoming attrs or, on update, from instance.
        - Query DB to see if any other row has the same combo.
        """
        brand = attrs.get("brand", getattr(self.instance, "brand", None))
        name = attrs.get("model_name", getattr(self.instance, "model_name", None))

        if brand and name:
            exists = (
                Model.objects.filter(brand=brand, model_name=name)
                .exclude(pk=getattr(self.instance, "pk", None))
                .exists()
            )
            if exists:
                raise serializers.ValidationError(
                    {"model_name": "This model already exists for this brand."}
                )
        return attrs


# PhysicalVehicle
"""
PhysicalVehicle serializer.

- Represents a specific, real car unit with a plate (e.g., 'PB1234KT')
- Belongs to a logical Vehicle
- READ: show brand/model names for convenience
- WRITE: accept the vehicle by ID
"""


class PhysicalVehicleSerializer(serializers.ModelSerializer):
    # READ: show the model name from related Vehicle -> Model
    vehicle_model_name = serializers.SlugRelatedField(
        source="vehicle.model",
        slug_field="model_name",
        read_only=True,
    )

    # READ: show the brand name from Vehicle -> Model -> Brand
    vehicle_brand_name = serializers.SlugRelatedField(
        source="vehicle.model.brand", slug_field="brand_name", read_only=True
    )

    # WRITE: accept the owning Vehicle by id
    vehicle_id = serializers.PrimaryKeyRelatedField(
        source="vehicle", queryset=Vehicle.objects.all(), write_only=True
    )

    class Meta:
        model = PhysicalVehicle
        fields = [
            "id",
            "car_plate_number",
            "vehicle_id",
            "vehicle_model_name",
            "vehicle_brand_name",
        ]
        extra_kwargs = {
            "car_plate_number": {
                "help_text": "Unique registration plate, e.g., 'PB1234KT'"
            },
        }

    def validate_car_plate_number(self, value: str) -> str:
        """
        Normalize and validate the plate.

        - Trim spaces, uppercase.
        - Ensure non-empty.
        """
        cleaned = value.strip().upper()
        if not cleaned:
            raise serializers.ValidationError("Car plate cannot be empty.")
        return cleaned
    
class LocationSerializer(serializers.ModelSerializer):
    """
    Locations details.

    :param serializers: The Django REST framework serializers module.
    :type serializers: module
    """
    class Meta:
        """
        City name (location_name) and address.
        """

        model = Location
        fields = ['location_name', 'address']
