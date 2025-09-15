from rest_framework_simplejwt.views import TokenObtainPairView
from ..serializers.login_serializer import CustomTokenObtainPairSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
