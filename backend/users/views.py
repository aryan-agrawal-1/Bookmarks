from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from .serializers import *
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.conf import settings as s





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

class ForgotPasswordView(generics.GenericAPIView):
    serializer_class = ForgotPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data = request.data)
        serializer.is_valid(raise_exception = True)
        email = serializer.validated_data['email']

        user = User.objects.filter(email__iexact=email).first()

        if user:
            token_gen = PasswordResetTokenGenerator()
            token = token_gen.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            reset_link = f"{s.FRONTEND_URL}/reset-password/{uid}/{token}/"

            send_mail(
                'Password Reset Request',
                f'Click the link to reset your password: {reset_link}',
                s.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

        return Response(
            {"detail": "If an account exists with this email, a password reset link has been sent."},
            status=status.HTTP_200_OK
        )

class ResetPasswordView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data = request.data)
        serializer.is_valid(raise_exception = True)
        data = serializer.validated_data

        try:
            uid = force_str(urlsafe_base64_decode(data['uid']))
            user = User.objects.get(pk = uid)
        
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({"detail": "Invalid reset link"})

        token_gen = PasswordResetTokenGenerator()

        if not token_gen.check_token(user, data['token']):
            raise serializers.ValidationError({"detail": "Invalid or expired reset link"})
        
        user.set_password(data['new_pass'])
        user.save()

        return Response({"detail": "Password reset successfully"}, status=status.HTTP_200_OK)

