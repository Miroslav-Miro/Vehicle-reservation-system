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


class ReservationCreateSerializer(serializers.Serializer):
    """
    POST /api/user_reservations/ (create)
    """

    start_date = serializers.DateField(help_text="Rental start date (YYYY-MM-DD).")
    end_date = serializers.DateField(help_text="Rental end date (YYYY-MM-DD).")
    vehicle_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
        help_text="List of PhysicalVehicle IDs to reserve.",
    )
    pickup_location_id = serializers.IntegerField(required=False)
    dropoff_location_id = serializers.IntegerField(required=False)

    def validate(self, attrs):
        if attrs["end_date"] <= attrs["start_date"]:
            raise serializers.ValidationError("end_date must be after start_date.")
        return attrs

    def _rental_days(self, start, end) -> int:
        days = (end - start).days
        if days < 1:
            raise serializers.ValidationError("Reservation must be at least 1 day.")
        return days

    @transaction.atomic
    def create(self, validated):
        user = self.context["request"].user
        start_date = validated["start_date"]
        end_date = validated["end_date"]
        ids = list(dict.fromkeys(validated["vehicle_ids"]))

        start = timezone.make_aware(datetime.combine(start_date, time.min))
        end = timezone.make_aware(datetime.combine(end_date, time.min))

        days = self._rental_days(start_date, end_date)

        # fetch selected physical vehicles
        units = list(
            PhysicalVehicle.objects.select_related(
                "vehicle", "vehicle__model", "vehicle__model__brand", "location"
            ).filter(id__in=ids)
        )
        found_ids = {u.id for u in units}
        missing = [vid for vid in ids if vid not in found_ids]
        if missing:
            raise serializers.ValidationError({"vehicle_ids": f"Not found: {missing}"})

        # resolve pickup/dropoff
        pickup = None
        dropoff = None
        pid = validated.get("pickup_location_id")
        did = validated.get("dropoff_location_id")

        if pid is not None:
            pickup = Location.objects.filter(pk=pid).first()
            if not pickup:
                raise serializers.ValidationError(
                    {"pickup_location_id": "Invalid location id."}
                )

        if did is not None:
            dropoff = Location.objects.filter(pk=did).first()
            if not dropoff:
                raise serializers.ValidationError(
                    {"dropoff_location_id": "Invalid location id."}
                )

        # if not provided, default to the single location of the chosen vehicles
        if not pickup or not dropoff:
            base_loc = units[0].location
            pickup = pickup or base_loc
            dropoff = dropoff or base_loc

        # prevent double booking
        blocking_res_ids = (
            Reservation.objects.select_for_update()
            .filter(
                Q(status__status__in=["CONFIRMED", "ACTIVE"])
                | Q(
                    status__status="PENDING_PAYMENT",
                    hold_expires_at__gt=timezone.now(),
                )
            )
            .values_list("id", flat=True)
        )

        taken_ids = set(
            PhysicalVehicleReservation.objects.filter(
                reservation_id__in=blocking_res_ids,
                reservation__start_date__lt=end,
                reservation__end_date__gt=start,
            ).values_list("physical_vehicle_id", flat=True)
        )
        clash = [u.id for u in units if u.id in taken_ids]
        if clash:
            raise serializers.ValidationError({"vehicle_ids": f"Unavailable: {clash}"})

        try:
            pending_status = ReservationStatus.objects.get(
                status__iexact="PENDING_PAYMENT"
            )
        except ReservationStatus.DoesNotExist:
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        "Seed ReservationStatus('PENDING_PAYMENT') first."
                    ]
                }
            )

        # create reservation
        res = Reservation.objects.create(
            user=user,
            start_date=start,
            end_date=end,
            status=pending_status,
            total_price=Decimal("0.00"),
            pickup_location=pickup,
            dropoff_location=dropoff,
        )

        # set short hold
        res.hold_expires_at = timezone.now() + timedelta(minutes=HOLD_MINUTES)
        res.save(update_fields=["hold_expires_at"])

        # attach items & compute total
        total = Decimal("0.00")
        for u in units:
            PhysicalVehicleReservation.objects.create(
                reservation=res,
                physical_vehicle=u,
            )
            total += u.vehicle.price_per_day * days

        res.total_price = total
        res.save(update_fields=["total_price"])

        # schedule auto expiry
        try:
            from email_sender.tasks import expire_unpaid_reservation

            expire_unpaid_reservation.apply_async(
                args=[res.id], countdown=HOLD_MINUTES * 60
            )
        except Exception:
            pass

        return res
