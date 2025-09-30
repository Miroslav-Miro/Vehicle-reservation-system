from .base_permission import *

class IsManager(HasRole):
    """
    Custom permission to only allow manager users to access certain views.
    This permission if used in views where only manager users should have access.
    :param BasePermission: Django REST framework BasePermission class.
    :type BasePermission: class
    """

    def __init__(self):
        super().__init__(allowed_roles=["manager"])