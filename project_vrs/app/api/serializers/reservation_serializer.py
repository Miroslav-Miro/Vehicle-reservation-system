from decimal import Decimal
from datetime import datetime, time, timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers

from ..models import (
    VehicleType,
    EngineType,
    Brand,
    Model,
    Vehicle,
    Location,
    PhysicalVehicle,
    PhysicalVehicleReservation,
    ReservationStatus,
    Reservation,
)


class CancelReservationSerializer(serializers.Serializer):
    """
    Serializer for cancelling a reservation.

    :param serializers: The Django REST framework serializers module.
    :type serializers: module
    """

    status = serializers.CharField()


class VehicleTypeSerializer(serializers.ModelSerializer):
    """
    Shows the type of the vihicle - sedan, suv, truck etc.

    :param serializers: The Django REST framework serializers module.
    :type serializers: module
    """

    class Meta:
        """
        Shows the id and vehicle type.
        """

        model = VehicleType
        fields = ["id", "vehicle_type"]


class EngineTypeSerializer(serializers.ModelSerializer):
    """
    Shows the engine type of the vehicle - petrol, diesel, electric etc.

    :param serializers: The Django REST framework serializers module.
    :type serializers: module
    """

    class Meta:
        """
        Shows the id and engine type.
        """

        model = EngineType
        fields = ["id", "engine_type"]


class BrandSerializer(serializers.ModelSerializer):
    """
    The brand of the vehicle - Toyota, Ford, BMW etc.

    :param serializers: The Django REST framework serializers module.
    :type serializers: module
    """

    class Meta:
        """
        Shows the id and brand name.
        """

        model = Brand
        fields = ["id", "brand_name"]


class ModelSerializer(serializers.ModelSerializer):
    """
    The model of the vehicle - Corolla, Mustang, X5 etc.

    :param serializers: The Django REST framework serializers module.
    :type serializers: module
    """

    brand = BrandSerializer()

    class Meta:
        """
        The class uses brand serializer to show the
        brand details along with model details. That ways it
        chains the model to brand using nested serializers.
        """

        model = Model
        fields = ["id", "brand", "model_name"]


class VehicleSerializer(serializers.ModelSerializer):
    """
    Combines all attributes that a vehicle has.

    :param serializers: The Django REST framework serializers module.
    :type serializers: module
    """

    vehicle_type = VehicleTypeSerializer()
    engine_type = EngineTypeSerializer()
    model = ModelSerializer()

    class Meta:
        """
        Shows all vehicle attributes along with
        related attributes using nested serializers.
        """

        ref_name = "VehicleBaseUserReservations"
        model = Vehicle
        fields = [
            "id",
            "amount_seats",
            "price_per_day",
            "vehicle_type",
            "engine_type",
            "model",
        ]


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
        ref_name = "LocationReservations"
        model = Location
        fields = ["id", "location_name", "address"]


class PhysicalVehicleSerializer(serializers.ModelSerializer):
    """
    Shows details of a physical vehicle.

    :param serializers: The Django REST framework serializers module.
    :type serializers: module
    """

    vehicle = VehicleSerializer()
    location = LocationSerializer()

    class Meta:
        """
        Shows car plate number, vehicle details and location details.
        Uses nested serializers to show vehicle and location details.
        """

        model = PhysicalVehicle
        fields = ["id", "car_plate_number", "vehicle", "location"]


class ReservationStatusSerializer(serializers.ModelSerializer):
    """
    Shows the status of a reservation.

    :param serializers: The Django REST framework serializers module.
    :type serializers: module
    """

    class Meta:
        """
        The status of the reservation.
        """

        model = ReservationStatus
        fields = ["id", "status"]


class ReservationSerializer(serializers.ModelSerializer):
    """
    Serializer for reservations.

    :param serializers: The Django REST framework serializers module.
    :type serializers: module
    :return: _serialized reservation_
    :rtype: _json_
    """

    status = ReservationStatusSerializer()
    pickup_location = LocationSerializer()
    dropoff_location = LocationSerializer()
    user = serializers.StringRelatedField()
    vehicles = serializers.SerializerMethodField()

    class Meta:
        """
        Uses all nested serializers to show
        related details of a reservation.
        """

        model = Reservation
        fields = [
            "id",
            "user",
            "status",
            "total_price",
            "start_date",
            "end_date",
            "pickup_location",
            "dropoff_location",
            "created_at",
            "updated_at",
            "vehicles",
        ]

    def get_vehicles(self, obj):
        """
        This method fetches the vehicles related to a reservation.

        :param obj: _the reservation object_
        :type obj: Reservation
        :return: _vehicles related to the reservation_
        :rtype: _list of PhysicalVehicleReservationSerializer_
        """

        # Get all PhysicalVehicleReservation entries for this reservation
        pvr = PhysicalVehicleReservation.objects.filter(reservation=obj)
        return PhysicalVehicleReservationSerializer(pvr, many=True).data


class PhysicalVehicleReservationSerializer(serializers.ModelSerializer):
    """
    Serializer for PhysicalVehicleReservation.

    :param serializers: The Django REST framework serializers module.
    :type serializers: module
    """

    physical_vehicle = PhysicalVehicleSerializer()

    class Meta:
        """
        Only the id and physical vehicle are shown since
        no vehicle reservation specific details are needed
        (that information is in the parent reservation).
        """

        model = PhysicalVehicleReservation
        fields = ["id", "physical_vehicle"]


HOLD_MINUTES = int(getattr(settings, "RESERVATION_HOLD_MINUTES", 15))

class LineItemSerializer(serializers.Serializer):
    vehicle_id = serializers.IntegerField(min_value=1)
    qty = serializers.IntegerField(min_value=1)

class ReservationCreateSerializer(serializers.Serializer):
    # match the frontend keys
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    start_location_id = serializers.IntegerField()
    end_location_id = serializers.IntegerField(required=False, allow_null=True)
    lines = serializers.ListField(child=LineItemSerializer(), allow_empty=False)

    def validate(self, attrs):
        start = attrs["start"]
        end = attrs["end"]

        # ensure tz-aware
        if timezone.is_naive(start):
            start = timezone.make_aware(start, timezone.get_current_timezone())
        if timezone.is_naive(end):
            end = timezone.make_aware(end, timezone.get_current_timezone())

        if end <= start:
            raise serializers.ValidationError("end must be after start.")

        attrs["start"] = start
        attrs["end"] = end
        return attrs