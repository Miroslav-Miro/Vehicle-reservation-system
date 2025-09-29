from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from ..models import Vehicle, Brand, EngineType, VehicleType, Model, PhysicalVehicle, Location
from ..serializers.vehicle_serializer import (
    VehicleSerializer,
    BrandSerializer,
    EngineTypeSerializer,
    VehicleTypeSerializer,
    ModelSerializer,
    PhysicalVehicleSerializer,
    LocationSerializer
)
from ..custom_permissions.mixed_role_permissions import RoleRequired
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated


# VvehicleView
class VehicleViewSet(viewsets.ModelViewSet):
    serializer_class = VehicleSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        "vehicle_type__vehicle_type": ["exact", "in"],
        "engine_type__engine_type": ["exact", "in"],
        "model__brand__brand_name": ["exact"],
        "model__model_name": ["exact", "icontains"],
        "price_per_day": ["gte", "lte"],
        "amount_seats": ["gte", "lte"],
    }
    search_fields = ["model__model_name", "model__brand__brand_name"]
    ordering_fields = ["price_per_day", "amount_seats", "id"]
    ordering = ["id"]

    def get_queryset(self):
        """
        select_related prefetches FK targets in the same query:
        - vehicle_type, engine_type, model, model.brand
        This avoids extra SQL per row.
        """
        return (
            Vehicle.objects.select_related(
                "vehicle_type", "engine_type", "model", "model__brand"
            )
            .all()
            .order_by("id")
        )

    def get_permissions(self):
        """
        Return a list of permission instances depending on the HTTP method.
        """
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [RoleRequired("user", "manager", "admin")]
        return [RoleRequired("manager", "admin")]


# BrandView
class BrandViewSet(viewsets.ModelViewSet):

    queryset = Brand.objects.all().order_by("id")
    serializer_class = BrandSerializer

    # Enable filtering capabilities
    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]
    filterset_fields = {"brand_name": ["exact", "icontains"]}
    search_fields = ["brand_name"]
    ordering_fields = ["brand_name", "id"]
    ordering = ["id"]

    def get_permissions(self):
        """
        Return a list of permission instances depending on the HTTP method.
        """
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [RoleRequired("user", "manager", "admin")]
        return [RoleRequired("manager", "admin")]


# EngineTypeView
class EngineTypeViewSet(viewsets.ModelViewSet):
    queryset = EngineType.objects.all().order_by("id")
    serializer_class = EngineTypeSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {"engine_type": ["exact", "icontains"]}
    search_fields = ["engine_type"]
    ordering_fields = ["engine_type", "id"]
    ordering = ["id"]

    def get_permissions(self):
        """
        Return a list of permission instances depending on the HTTP method
        """
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [RoleRequired("user", "manager", "admin")]
        return [RoleRequired("manager", "admin")]


# VehicleTypeView
class VehicleTypeViewSet(viewsets.ModelViewSet):
    queryset = VehicleType.objects.all().order_by("id")
    serializer_class = VehicleTypeSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {"vehicle_type": ["exact", "icontains"]}
    search_fields = ["vehicle_type"]
    ordering_fields = ["vehicle_type", "id"]
    ordering = ["id"]

    def get_permissions(self):
        """
        Return a list of permission instances depending on the HTTP method.
        """
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [RoleRequired("user", "manager", "admin")]
        return [RoleRequired("manager", "admin")]


# ModelView
class ModelViewSet(viewsets.ModelViewSet):
    serializer_class = ModelSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        "brand__brand_name": ["exact", "icontains"],  # filter by brand name
        "model_name": ["exact", "icontains"],  # filter by model name
    }
    search_fields = ["model_name", "brand__brand_name"]
    ordering_fields = ["model_name", "id"]
    ordering = ["id"]

    def get_queryset(self):
        """
        select_related('brand') joins the brand row in the same SQL query,
        preventing an extra query for each result row.
        """
        return Model.objects.select_related("brand").all().order_by("id")

    def get_permissions(self):
        """
        Return a list of permission instances depending on the HTTP method.
        """
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [RoleRequired("user", "manager", "admin")]
        return [RoleRequired("manager", "admin")]


# PhysicalVehicleView
"""
PhysicalVehicle ViewSet — CRUD for real car units with plates.

Common use cases:
- Search by plate
- Filter by brand/model through relations
- Use select_related for performance
"""


class PhysicalVehicleViewSet(viewsets.ModelViewSet):
    serializer_class = PhysicalVehicleSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        "car_plate_number": ["exact", "icontains"],
        "vehicle__model__brand__brand_name": [
            "exact",
            "icontains",
        ],  # filter by brand name
        "vehicle__model__model_name": ["exact", "icontains"],  # filter by model name
    }
    search_fields = [
        "car_plate_number",
        "vehicle__model__brand__brand_name",
        "vehicle__model__model_name",
    ]
    ordering_fields = ["car_plate_number", "id"]
    ordering = ["id"]

    def get_queryset(self):
        return (
            PhysicalVehicle.objects.select_related(
                "vehicle", "vehicle__model", "vehicle__model__brand"
            )
            .all()
            .order_by("id")
        )

    def get_permissions(self):
        """
        Return a list of permission instances depending on the HTTP method.
        """
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            permission_classes = [RoleRequired("user", "manager", "admin")]
        else:
            permission_classes = [RoleRequired("manager", "admin")]
        return permission_classes
