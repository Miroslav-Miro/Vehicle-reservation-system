from django.shortcuts import render
from .serializers import *
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    permission_classes = [IsAdminUser]
