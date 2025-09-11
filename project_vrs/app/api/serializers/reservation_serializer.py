from rest_framework import serializers
from ..models import *


from rest_framework import serializers

class EngineTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EngineType
        fields = ['engine_type']
        ref_name = "EngineTypeForReservation"

class VehicleTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleType
        fields = ['vehicle_type']
        ref_name = "VehicleTypeForReservation"

class ModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Model
        fields = ['model_name']
        ref_name = "ModelForReservation"

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['brand_name']
        ref_name = "BrandForReservation"

class VehicleSerializer(serializers.ModelSerializer):
    engine_type = EngineTypeSerializer()
    vehicle_type = VehicleTypeSerializer()
    model = ModelSerializer()
    brand = BrandSerializer()

    class Meta:
        model = Vehicle
        fields = ["id", "amount_seats", "price_per_day","engine_type","vehicle_type","model","brand"]
        ref_name = "VehicleForReservation"

#  vehicle_type = models.ForeignKey(VehicleType, on_delete=models.CASCADE)
#  engine_type = models.ForeignKey(EngineType, on_delete=models.CASCADE)
#  model = models.ForeignKey(Model, on_delete=models.CASCADE)



class PhysicalVehicleSerializer(serializers.ModelSerializer):
    vehicle = VehicleSerializer()

    class Meta:
        model = PhysicalVehicle
        fields = ["id", "car_plate_number", "latitude", "longitude", "vehicle"]


class PhysicalVehicleReservationSerializer(serializers.ModelSerializer):
    physical_vehicle = PhysicalVehicleSerializer()

    class Meta:
        model = PhysicalVehicleReservation
        fields = [
            "id", "physical_vehicle", "start_date", "end_date",
            "pickup_latitude", "pickup_longitude",
            "dropoff_latitude", "dropoff_longitude", "unit_price"
        ]

class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReservationStatus
        fields = ['id', 'status']

class ReservationDetailSerializer(serializers.ModelSerializer):
    status = StatusSerializer()
    physical_vehicles = PhysicalVehicleReservationSerializer(
        source="physicalvehiclereservation_set", many=True, read_only=True
    )

    class Meta:
        model = Reservation
        fields = ["id", "status", "total_price", "created_at", "updated_at", "physical_vehicles"]
