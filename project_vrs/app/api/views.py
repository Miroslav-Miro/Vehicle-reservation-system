from django.shortcuts import render
from .serializers import *
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework import status, viewsets, generics, permissions
from rest_framework.permissions import IsAuthenticated, IsAdminUser


class RegisterView(generics.CreateAPIView):
    """View for user registration.
    Generics is used because it provides a built-in way to
    handle only Post requests for creating new instances.
    No need for custom methods or viewsets here.

    Detailed flow of the operations for registration view:
    1. Client (POST /api/auth/register/) 
    2. urls.py  ->  matches "auth/register/" 
    3. views.py (RegisterView)  ->  uses RegisterSerializer 
    4. serializers.py (RegisterSerializer)  
    5. models.py (UserManager.create_user)  
    6. Database (new User row created)
    7. Response JSON (serializer data → back to client)

    :param generics: Django REST framework generics module.
    :type generics: module
    """

    #Tells DRF which model table this view is working with.
    queryset = User.objects.all()
    #Defines which serializer will be used            
    serializer_class = RegisterSerializer
    # Since anyone should be able to register, we set permission to AllowAny
    permission_classes = [permissions.AllowAny]
class RoleViewSet(viewsets.ModelViewSet):
    
    queryset = Role.objects.all()
    
    serializer_class = RoleSerializer
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    
