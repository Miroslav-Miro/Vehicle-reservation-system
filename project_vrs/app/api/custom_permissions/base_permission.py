from rest_framework.permissions import BasePermission


class HasRole(BasePermission):
    """
    Custom permission to only allow users with specific roles to access certain views.

    :param BasePermission: Django REST framework BasePermission class.
    :type BasePermission: class
    """

    def __init__(self, allowed_roles=None):
        self.allowed_roles = [r.lower() for r in (allowed_roles or [])]

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and hasattr(request.user, "role_id")
            and request.user.role_id.role_name in self.allowed_roles
        )
