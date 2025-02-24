from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='user-profile'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('token-refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
]
