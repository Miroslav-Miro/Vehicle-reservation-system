from ..serializers.role_serializer import *
from ..models import *
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated
from ..custom_permissions.admin_permission import IsAdmin
from ..serializers.user_serializer import UserProfileSerializer, AdminUserProfilesSerializer

class UserProfileViewSet(generics.RetrieveUpdateAPIView):
    """
    ViewSet for managing users. Only authenticated users can access this view.
    This view is used to retrieve and update the current logged-in user's profile.

    :param viewsets: _description_
    :type viewsets: _type_
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    def get_object(self):
        return self.request.user

class AdminUserProfilesViewSet(viewsets.ModelViewSet):
    """Admins can manage all users (full fields)."""

    queryset = User.objects.all()
    serializer_class = AdminUserProfilesSerializer
    permission_classes = [IsAdmin]