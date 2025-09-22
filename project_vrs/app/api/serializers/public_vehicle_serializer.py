from rest_framework import serializers
from ..models import PhysicalVehicle, Location, Brand, Model, VehicleType, EngineType

class PublicVehicleAvailabilitySerializer(serializers.Serializer):
    vehicle_id = serializers.IntegerField()
    brand = serializers.CharField()
    model = serializers.CharField()
    vehicle_type = serializers.CharField()
    engine_type = serializers.CharField()
    seats = serializers.IntegerField()
    price_per_day = serializers.DecimalField(max_digits=10, decimal_places=2)
    available_count = serializers.IntegerField()


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
        fields = ["id","location_name", "address"]

class ModelSerializerForFilter(serializers.ModelSerializer):

    class Meta:
        model = Model
        fields = ["id", "model_name"]

class BrandModelSerializerForFilter(serializers.ModelSerializer):
    
    models = ModelSerializerForFilter(many=True, source="model_set")

    class Meta:
        model = Brand
        fields = ["id", "brand_name","models"]

class VehicleTypeSerializerForFilter(serializers.ModelSerializer):
    
    class Meta:
        model = VehicleType
        fields = ["id", "vehicle_type"]

class EngineTypeSerializerForFilter(serializers.ModelSerializer):

    class Meta:
        model = EngineType
        fields = ["id", "engine_type"]

