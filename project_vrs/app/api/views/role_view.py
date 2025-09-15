from ..serializers.role_serializer import *
from ..models import *
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from ..custom_permissions.admin_permission import IsAdmin
from ..custom_permissions.user_permission import IsNormalUser


class RoleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing roles. Only an admin user can access this view.

    :param viewsets: Django REST framework viewsets module.
    :type viewsets: module
    """

    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    permission_classes = [IsAdmin]
