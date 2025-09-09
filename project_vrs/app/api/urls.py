from django.urls import path, include
from .views.registration_view import RegisterView
from .views.role_view import RoleViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

# router.register(r'users', User, basename = "users")
router.register(r"roles",RoleViewSet,basename="roles")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/register/", RegisterView.as_view(), name="register"),
]