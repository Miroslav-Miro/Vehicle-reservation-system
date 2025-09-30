from .base_permission import *

class IsAdmin(HasRole):
    """
    Custom permission to only allow admin users to access certain views.

    :param HasRole: BasePermission subclass for role-based access control.
    :type HasRole: class
    """
    def __init__(self):
        super().__init__(allowed_roles=["admin"])
