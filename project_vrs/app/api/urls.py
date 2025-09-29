from django.urls import path, include

from api.views.registration_view import RegisterView
from api.views.role_view import RoleViewSet
from api.views.vehicle_view import (
    VehicleViewSet,
    PhysicalVehicleViewSet,
    BrandViewSet,
    EngineTypeViewSet,
    VehicleTypeViewSet,
    ModelViewSet,
)
from api.views.user_view import UserProfileViewSet, AdminUserProfilesViewSet
from api.views.reservation_view import ReservationViewSet
from rest_framework.routers import DefaultRouter
from .views.admin_ops_view import AdminKPIView, AdminReservationTransitionView
from api.views.payment_view import MockPaymentView


app_name = "api"

router = DefaultRouter()
router.register(r"roles", RoleViewSet, basename="roles")
router.register(r"vehicles", VehicleViewSet, basename="vehicles")
router.register(
    r"physical-vehicles", PhysicalVehicleViewSet, basename="physical-vehicles"
)
router.register(r"brands", BrandViewSet, basename="brands")
router.register(r"engine-types", EngineTypeViewSet, basename="engine-types")
router.register(r"vehicle-types", VehicleTypeViewSet, basename="vehicle-types")
router.register(r"models", ModelViewSet, basename="models")
router.register(
    r"user-management", AdminUserProfilesViewSet, basename="user-management"
)
router.register(r"user-reservations", ReservationViewSet, basename="user-reservations")


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
]
