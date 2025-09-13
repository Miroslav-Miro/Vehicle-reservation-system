from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims into the JWT itself
        token['role'] = user.role_id.role_name
        token['username'] = user.username

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # Add extra response data
        data['role'] = self.user.role_id.role_name
        data['username'] = self.user.username

        return data
