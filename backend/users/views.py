from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer, CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response





User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all() # Ensure no duplicate users
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serialiser = self.get_serializer(data = request.data)
        serialiser.is_valid(raise_exception=True)
        user = serialiser.save()

        # Generate JWT tokens for the newly created user
        refresh = RefreshToken.for_user(user)

        data = serialiser.data
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)

        headers = self.get_success_headers(serialiser.data)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer