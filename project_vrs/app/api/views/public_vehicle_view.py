from django.db.models import Count, Exists, OuterRef
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from rest_framework import viewsets, permissions
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

from ..models import PhysicalVehicle, PhysicalVehicleReservation, Location, Brand, Model, VehicleType, EngineType
from ..serializers.public_vehicle_serializer import (
    PublicVehicleAvailabilitySerializer,
    LocationSerializer,
    BrandModelSerializerForFilter,
    VehicleTypeSerializerForFilter,
    EngineTypeSerializerForFilter
)
from ..filters.public_vehicle_filters import PublicVehicleAvailabilityFilter

class PublicVehicleAvailabilityViewSet(viewsets.ViewSet):
    """
    Public endpoint: returns conceptual vehicles with counts
    of how many units are available in a location/time window.

    Required params:
      - location_id
      - start (ISO8601 datetime, e.g. 2025-09-20T10:00:00Z)
      - end   (ISO8601 datetime, e.g. 2025-09-22T10:00:00Z)

    Optional params:
      - brand
      - model
      - vehicle_type
      - engine_type
      - price_min / price_max
      - seats_min / seats_max
    """

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

    def list(self, request):
        location_id = request.query_params.get("location_id")
        start_str = request.query_params.get("start")
        end_str = request.query_params.get("end")

        if not location_id or not start_str or not end_str:
            return Response(
                {"detail": "location_id, start, end are required."}, status=400
            )

        try:
            start, end = self._parse_range(start_str, end_str)
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)

        # Which reservation statuses block availability
        BLOCKING = ["ACTIVE"]

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

        brand = request.query_params.get("brand")
        model = request.query_params.get("model")
        vehicle_type = request.query_params.get("vehicle_type")
        engine_type = request.query_params.get("engine_type")
        price_min = request.query_params.get("price_min")
        price_max = request.query_params.get("price_max")
        seats_min = request.query_params.get("seats_min")
        seats_max = request.query_params.get("seats_max")

        if brand:
            qs = qs.filter(vehicle__model__brand__brand_name__icontains=brand)
        if model:
            qs = qs.filter(vehicle__model__model_name__icontains=model)
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


