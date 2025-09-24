from django.db.models import Count, Exists, OuterRef
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from rest_framework import viewsets, permissions
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from django.shortcuts import get_object_or_404

from ..models import PhysicalVehicle, PhysicalVehicleReservation, Location, Brand, Model, VehicleType, EngineType, Vehicle
from ..serializers.public_vehicle_serializer import (
    PublicVehicleAvailabilitySerializer,
    LocationSerializer,
    BrandModelSerializerForFilter,
    VehicleTypeSerializerForFilter,
    EngineTypeSerializerForFilter
)
class PublicVehicleAvailabilityViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def _parse_range(self, start_str, end_str):
        start = parse_datetime(start_str or "")
        end = parse_datetime(end_str or "")
        if not start or not end:
            raise ValueError(
                "start and end must be ISO8601 datetimes (e.g. 2025-09-20T10:00:00Z)."
            )
        if timezone.is_naive(start):
            start = timezone.make_aware(start, timezone.get_current_timezone())
        if timezone.is_naive(end):
            end = timezone.make_aware(end, timezone.get_current_timezone())
        if start >= end:
            raise ValueError("start must be before end")
        return start, end
    
    def retrieve(self, request, pk=None):
        """
        Detail endpoint for a conceptual Vehicle (pk = Vehicle.id).
        Optional query params: location_id, start, end (same rules as list).
        Returns one row with available_count for that vehicle.
        """
        # Make sure the vehicle exists
        vehicle = get_object_or_404(
            Vehicle.objects.select_related(
                "model__brand", "vehicle_type", "engine_type"
            ),
            pk=pk,
        )

        # Params
        location_id = request.query_params.get("location_id")
        start_str = request.query_params.get("start")
        end_str = request.query_params.get("end")

        if location_id and (not start_str or not end_str):
            return Response(
                {"detail": "When location_id is provided, start and end are required."},
                status=400,
            )
        if (start_str and not end_str) or (end_str and not start_str):
            return Response(
                {"detail": "Provide both start and end, or neither."},
                status=400,
            )

        start = end = None
        if start_str and end_str:
            try:
                start, end = self._parse_range(start_str, end_str)
            except ValueError as e:
                return Response({"detail": str(e)}, status=400)

        BLOCKING = ["active"]  # match your DB casing!

        # Base = physical units for this Vehicle
        base = PhysicalVehicle.objects.filter(vehicle_id=vehicle.id)

        if location_id:
            base = base.filter(location_id=location_id)

        if start and end:
            # Exclude any physical unit that has an overlapping blocking reservation
            overlapping = PhysicalVehicleReservation.objects.filter(
                physical_vehicle_id=OuterRef("pk"),
                reservation__start_date__lt=end,
                reservation__end_date__gt=start,
                reservation__status__status__in=BLOCKING,
            )
            base = base.annotate(is_blocked=Exists(overlapping)).filter(is_blocked=False)

        # Aggregate a single row
        row = base.values().aggregate(cnt=Count("id"))
        available_count = row["cnt"] or 0

        data = {
            "vehicle_id": vehicle.id,
            "brand": vehicle.model.brand.brand_name,
            "model": vehicle.model.model_name,
            "vehicle_type": vehicle.vehicle_type.vehicle_type,
            "engine_type": vehicle.engine_type.engine_type,
            "seats": vehicle.amount_seats,
            "price_per_day": vehicle.price_per_day,
            "available_count": available_count,
        }

        return Response(PublicVehicleAvailabilitySerializer(data).data)

    def list(self, request):
        location_id = request.query_params.get("location_id")
        start_str = request.query_params.get("start")
        end_str = request.query_params.get("end")

        # --- validate parameter combinations ---
        if location_id and (not start_str or not end_str):
            return Response(
                {"detail": "When location_id is provided, start and end are required."},
                status=400,
            )
        if (start_str and not end_str) or (end_str and not start_str):
            return Response(
                {"detail": "Provide both start and end, or neither."},
                status=400,
            )

        # Parse time range if both provided (used in the two availability branches)
        start = end = None
        if start_str and end_str:
            try:
                start, end = self._parse_range(start_str, end_str)
            except ValueError as e:
                return Response({"detail": str(e)}, status=400)

        BLOCKING = ["active"]

        # --- build base queryset in 3 scenarios ---
        if location_id and start and end:
            # A) Availability in a specific location (current behavior)
            overlapping = PhysicalVehicleReservation.objects.filter(
                physical_vehicle_id=OuterRef("pk"),
                reservation__start_date__lt=end,
                reservation__end_date__gt=start,
                reservation__status__status__in=BLOCKING,
            )
            qs = (
                PhysicalVehicle.objects.filter(location_id=location_id)
                .annotate(is_blocked=Exists(overlapping))
                .filter(is_blocked=False)
            )

        elif (not location_id) and start and end:
            # B) Availability across ALL locations (free units globally)
            overlapping = PhysicalVehicleReservation.objects.filter(
                physical_vehicle_id=OuterRef("pk"),
                reservation__start_date__lt=end,
                reservation__end_date__gt=start,
                reservation__status__status__in=BLOCKING,
            )
            qs = (
                PhysicalVehicle.objects.all()
                .annotate(is_blocked=Exists(overlapping))
                .filter(is_blocked=False)
            )

        else:
            # C) No dates → just inventory counts (no availability filtering)
            qs = PhysicalVehicle.objects.all()

        brand_id = request.query_params.get("brand_id")
        model_id = request.query_params.get("model_id")
        vehicle_type = request.query_params.get("vehicle_type")
        engine_type = request.query_params.get("engine_type")
        price_min = request.query_params.get("price_min")
        price_max = request.query_params.get("price_max")
        seats_min = request.query_params.get("seats_min")
        seats_max = request.query_params.get("seats_max")

        if brand_id:
            qs = qs.filter(vehicle__brand_id=brand_id)
        if model_id:
            qs = qs.filter(vehicle__model_id=model_id)
        if vehicle_type:
            qs = qs.filter(vehicle__vehicle_type__vehicle_type__icontains=vehicle_type)
        if engine_type:
            qs = qs.filter(vehicle__engine_type__engine_type__icontains=engine_type)
        if price_min:
            qs = qs.filter(vehicle__price_per_day__gte=price_min)
        if price_max:
            qs = qs.filter(vehicle__price_per_day__lte=price_max)
        if seats_min:
            qs = qs.filter(vehicle__amount_seats__gte=seats_min)
        if seats_max:
            qs = qs.filter(vehicle__amount_seats__lte=seats_max)

        
        
        # ------------------------------
        # Aggregate to conceptual vehicles
        # In all branches we keep the same payload shape with "available_count"
        # - In A/B it means free units in the time window
        # - In C it means total units (no availability window)
        # ------------------------------
        qs = (
            qs.values(
                "vehicle_id",
                "vehicle__model__brand__brand_name",
                "vehicle__model__model_name",
                "vehicle__vehicle_type__vehicle_type",
                "vehicle__engine_type__engine_type",
                "vehicle__amount_seats",
                "vehicle__price_per_day",
            )
            .annotate(available_count=Count("id"))
            .order_by("vehicle__model__brand__brand_name", "vehicle__model__model_name")
        )
        random_count = request.query_params.get("random")
        if random_count:
            try:
                random_count = int(random_count)
                qs = qs.order_by("?")[:random_count]
            except ValueError:
                pass

        data = [
            {
                "vehicle_id": row["vehicle_id"],
                "brand": row["vehicle__model__brand__brand_name"],
                "model": row["vehicle__model__model_name"],
                "vehicle_type": row["vehicle__vehicle_type__vehicle_type"],
                "engine_type": row["vehicle__engine_type__engine_type"],
                "seats": row["vehicle__amount_seats"],
                "price_per_day": row["vehicle__price_per_day"],
                "available_count": row["available_count"],
            }
            for row in qs
        ]
        return Response(PublicVehicleAvailabilitySerializer(data, many=True).data)


class LocationViewSetFiltering(viewsets.ReadOnlyModelViewSet):
    queryset = Location.objects.all().order_by("location_name", "address")
    serializer_class = LocationSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

class BrandModelViewSetFiltering(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for listing and retrieving brands.
    """
    queryset = Brand.objects.prefetch_related("model_set").all().order_by("brand_name")
    serializer_class = BrandModelSerializerForFilter
    permission_classes = [permissions.AllowAny]
    pagination_class = None

class VehicleTypeViewSetFiltering(viewsets.ReadOnlyModelViewSet):
    queryset = VehicleType.objects.all().order_by("vehicle_type")
    serializer_class = VehicleTypeSerializerForFilter
    permission_classes = [permissions.AllowAny]
    pagination_class = None

class EngineTypeViewSetFiltering(viewsets.ReadOnlyModelViewSet):
    queryset = EngineType.objects.all().order_by("engine_type")
    serializer_class = EngineTypeSerializerForFilter
    permission_classes = [permissions.AllowAny]
    pagination_class = None


