from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.registration_view import RegisterView
from .views.role_view import RoleViewSet
from api.views.vehicle_view import (
    VehicleViewSet,
    PhysicalVehicleViewSet,
    BrandViewSet,
    EngineTypeViewSet,
    VehicleTypeViewSet,
    ModelViewSet
)
from .views.public_vehicle_view import (
    PublicVehicleAvailabilityViewSet,
    LocationViewSetFiltering, 
    BrandModelViewSetFiltering,
    VehicleTypeViewSetFiltering,
    EngineTypeViewSetFiltering
)
from .views.user_view import UserProfileViewSet, AdminUserProfilesViewSet
from .views.reservation_view import ReservationViewSet

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
# router.register(r"locations", LocationViewSet, basename="locations")

router.register(r"user_management",AdminUserProfilesViewSet,basename="user_management")
router.register(r"user_reservations",ReservationViewSet,basename="user_reservations")

##retrieving data for filtering options
router.register(r"locations_filter", LocationViewSetFiltering, basename="locations_filter")
router.register(r"brands_models_filter", BrandModelViewSetFiltering, basename="brands_models_filter")
router.register(r"vehicle_type_filter", VehicleTypeViewSetFiltering, basename="vehicle_type_filter")
router.register(r"engine_type_filter", EngineTypeViewSetFiltering, basename="engine_type_filter")


public_vehicle_availability = PublicVehicleAvailabilityViewSet.as_view({
    "get": "list",
})

urlpatterns = [
    path("", include(router.urls)),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("user_profile/", UserProfileViewSet.as_view(), name="user_profile"),
    path("public/vehicles/available/", public_vehicle_availability, name="public-vehicles-available")
]
