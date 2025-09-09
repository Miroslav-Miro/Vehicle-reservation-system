# api/permissions/role_required.py
from rest_framework import permissions


class RoleRequired(permissions.BasePermission):
    """
    Generic role-based permission.
    Usage:
        permission_classes = [RoleRequired("admin", "manager")]

    Checks if request.user has a role_id.role_name that matches
    one of the allowed roles.
    """

    def __init__(self, *roles):
        self.allowed_roles = [r.lower() for r in roles]

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        role = getattr(getattr(request.user, "role_id", None), "role_name", "")
        if not role:
            return False

        return role.lower() in self.allowed_roles
