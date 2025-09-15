from rest_framework import serializers
from ..models import *


class CancelReservationSerializer(serializers.Serializer):
    status = serializers.CharField()
class VehicleTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleType
        fields = ['id', 'vehicle_type']

class EngineTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EngineType
        fields = ['id', 'engine_type']

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id',"brand_name"]

class ModelSerializer(serializers.ModelSerializer):
    brand = BrandSerializer()
    class Meta:
        model = Model
        fields = ['id',"brand",'model_name']





class VehicleSerializer(serializers.ModelSerializer):
    
    vehicle_type = VehicleTypeSerializer()
    engine_type = EngineTypeSerializer()
    model = ModelSerializer()

    class Meta:
        ref_name = "VehicleBaseUserReservations" 
        model = Vehicle
        fields = ['id', 'amount_seats', 'price_per_day', 'vehicle_type', 'engine_type', 'model']


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'location_name', 'address']


class PhysicalVehicleSerializer(serializers.ModelSerializer):
    vehicle = VehicleSerializer()
    location = LocationSerializer()

    class Meta:
        model = PhysicalVehicle
        fields = ['id', 'car_plate_number', 'vehicle', 'location']


class ReservationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReservationStatus
        fields = ['id', 'status']


class ReservationSerializer(serializers.ModelSerializer):
    status = ReservationStatusSerializer()
    pickup_location = LocationSerializer()
    dropoff_location = LocationSerializer()
    user = serializers.StringRelatedField()  # or a custom UserSerializer
    vehicles = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = [
            'id', 'user', 'status', 'total_price', 'start_date', 'end_date',
            'pickup_location', 'dropoff_location', 'created_at', 'updated_at',
            'vehicles'   # 👈 added here
        ]

    def get_vehicles(self, obj):
        # Get all PhysicalVehicleReservation entries for this reservation
        pvr = PhysicalVehicleReservation.objects.filter(reservation=obj)
        return PhysicalVehicleReservationSerializer(pvr, many=True).data

class PhysicalVehicleReservationSerializer(serializers.ModelSerializer):
    physical_vehicle = PhysicalVehicleSerializer()

    class Meta:
        model = PhysicalVehicleReservation
        fields = ['id', 'physical_vehicle']
