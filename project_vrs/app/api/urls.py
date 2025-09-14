from django.urls import path, include
from .views.registration_view import RegisterView
from .views.role_view import RoleViewSet
from api.views.vehicle_view import (
    VehicleViewSet,
    PhysicalVehicleViewSet,
    BrandViewSet,
    EngineTypeViewSet,
    VehicleTypeViewSet,
    ModelViewSet,
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

# router.register(r'users', User, basename = "users")
router.register(r"roles", RoleViewSet, basename="roles")
router.register(r"vehicles", VehicleViewSet, basename="vehicles")
router.register(
    r"physical-vehicles", PhysicalVehicleViewSet, basename="physical-vehicle"
)
router.register(r"brands", BrandViewSet, basename="brand")
router.register(r"engine-types", EngineTypeViewSet, basename="engine-type")
router.register(r"vehicle-types", VehicleTypeViewSet, basename="vehicle-type")
router.register(r"models", ModelViewSet, basename="model")


urlpatterns = [
    path("", include(router.urls)),
    path("auth/register/", RegisterView.as_view(), name="register"),
]
