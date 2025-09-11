from django.urls import path, include
from .views.registration_view import RegisterView
from .views.role_view import RoleViewSet
from .views.vehicle_view import VehicleViewSet
from .views.user_view import UserProfileViewSet, AdminUserProfilesViewSet
from .views.reservation_view import ReservationViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

# router.register(r'users', User, basename = "users")
router.register(r"roles",RoleViewSet,basename="roles")
router.register(r"vehicles",VehicleViewSet,basename="vehicles")
router.register(r"user_management",AdminUserProfilesViewSet,basename="user_management")
router.register(r"user_reservations",ReservationViewSet,basename="user_reservations")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("user_profile/", UserProfileViewSet.as_view(), name="user_profile"),
]