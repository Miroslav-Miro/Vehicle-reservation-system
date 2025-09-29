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

from api.views.user_view import UserProfileViewSet, AdminUserProfilesViewSet
from api.views.reservation_view import ReservationViewSet
from rest_framework.routers import DefaultRouter
from .views.admin_ops_view import AdminKPIView, AdminReservationTransitionView
from api.views.payment_view import MockPaymentView
from .views.notification_view import NotificationViewSet



app_name = "api"

router = DefaultRouter()
router.register(r"roles", RoleViewSet, basename="roles")
router.register(r"vehicles", VehicleViewSet, basename="vehicles")
router.register(
    r"physical-vehicles", PhysicalVehicleViewSet, basename="physical-vehicles"
)
router.register(r"brands", BrandViewSet, basename="brand")
router.register(r"engine-types", EngineTypeViewSet, basename="engine-type")
router.register(r"vehicle-types", VehicleTypeViewSet, basename="vehicle-type")
router.register(r"models", ModelViewSet, basename="model")
# router.register(r"locations", LocationViewSet, basename="locations")

router.register(
    r"user-management", AdminUserProfilesViewSet, basename="user-management"
)
router.register(r"user-reservations", ReservationViewSet, basename="user-reservations")


##retrieving data for filtering options
router.register(r"locations_filter", LocationViewSetFiltering, basename="locations_filter")
router.register(r"brands_models_filter", BrandModelViewSetFiltering, basename="brands_models_filter")
router.register(r"vehicle_type_filter", VehicleTypeViewSetFiltering, basename="vehicle_type_filter")
router.register(r"engine_type_filter", EngineTypeViewSetFiltering, basename="engine_type_filter")

router.register(r"notifications", NotificationViewSet, basename="notification")

public_vehicle_list = PublicVehicleAvailabilityViewSet.as_view({"get": "list"})
public_vehicle_detail = PublicVehicleAvailabilityViewSet.as_view({"get": "retrieve"})


urlpatterns = [
    path("", include(router.urls)),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("user_profile/", UserProfileViewSet.as_view(), name="user_profile"),

    path(
        "ops/reservations/<int:pk>/transition/",
        AdminReservationTransitionView.as_view(),
        name="ops-reservation-transition",
    ),
    path("ops/kpis/", AdminKPIView.as_view(), name="ops-kpis"),
    path(
        "payments/mock/<int:reservation_id>/",
        MockPaymentView.as_view(),
        name="payments-mock",
    ),
   path("public/vehicles/available/", public_vehicle_list, name="public-vehicles-available"),
   path("public/vehicles/<int:pk>/", public_vehicle_detail, name="public-vehicle-detail")

   
]
