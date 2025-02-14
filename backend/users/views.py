from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer


User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all() # Ensure no duplicate users
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]