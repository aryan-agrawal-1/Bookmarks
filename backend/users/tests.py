# users/tests.py
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch, call
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import EmailMultiAlternatives
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from users.backends import EmailOrUsernameModelBackend

User = get_user_model()


class TestRegistration(APITestCase):
    """Test user registration endpoint"""
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('user-profile')
        self.valid_payload = {
            'name': 'Test User',
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'securepassword123',
            'conf_password': 'securepassword123'
        }

    def test_successful_registration(self):
        """Test new user can register with valid data"""
        response = self.client.post(self.url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)  # Check JWT tokens are returned
        self.assertIn('refresh', response.data)
        self.assertEqual(User.objects.count(), 1)

    def test_password_mismatch(self):
        """Test registration fails when passwords don't match"""
        payload = self.valid_payload.copy()
        payload['conf_password'] = 'differentpassword'
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

    def test_short_password(self):
        """Test password length validation (min 6 chars)"""
        payload = self.valid_payload.copy()
        payload['password'] = 'short'
        payload['conf_password'] = 'short'
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_existing_email(self):
        """Test case-insensitive email uniqueness"""
        User.objects.create_user(
            email='Test@Example.com',  # Different case
            username='existing',
            name='Existing User',
            password='testpass123'
        )
        response = self.client.post(self.url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_existing_username(self):
        """Test case-insensitive username uniqueness"""
        User.objects.create_user(
            email='existing@example.com',
            username='TestUser',  # Different case
            name='Existing User',
            password='testpass123'
        )
        response = self.client.post(self.url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)


class TestLogin(APITestCase):
    """Test user login endpoint"""
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('login')
        self.user = User.objects.create_user(
            email='user@example.com',
            username='testuser',
            name='Test User',
            password='validpassword123'
        )

    def test_login_with_email(self):
        """Test login using email credentials"""
        data = {'email': 'user@example.com', 'password': 'validpassword123'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_with_username(self):
        """Test login using username credentials"""
        data = {'email': 'testuser', 'password': 'validpassword123'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_case_insensitive(self):
        """Test email/username case insensitivity"""
        data = {'email': 'USER@EXAMPLE.COM', 'password': 'validpassword123'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_password(self):
        """Test login fails with wrong password"""
        data = {'email': 'user@example.com', 'password': 'wrongpassword'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nonexistent_user(self):
        """Test login fails for non-existent user"""
        data = {'email': 'nonexistent@example.com', 'password': 'testpass'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestForgotPassword(APITestCase):
    """Test password reset initiation endpoint"""
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('forgot-password')
        self.user = User.objects.create_user(
            email='user@example.com',
            username='testuser',
            name='Test User',
            password='testpass123'
        )

    @patch('users.views.EmailMultiAlternatives.send')
    def test_existing_user(self, mock_send):
        """Test password reset flow for existing user"""
        data = {'email': 'user@example.com'}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(mock_send.called)

        # Check if email is sent with HTML
        _, kwargs = mock_send.call_args
        self.assertIn("text/html", kwargs.get("content_subtype", ""))

    def test_nonexistent_user(self):
        """Test password reset request for non-existent user (security measure)"""
        data = {'email': 'invalid@example.com'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reset_link_validity(self):
        """Test generated reset link works correctly"""
        token_generator = PasswordResetTokenGenerator()
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = token_generator.make_token(self.user)
        
        # Verify token validation
        self.assertTrue(token_generator.check_token(self.user, token))
        self.assertEqual(force_str(urlsafe_base64_decode(uid)), str(self.user.pk))


class TestResetPassword(APITestCase):
    """Test password reset completion endpoint"""
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('reset-password')
        self.user = User.objects.create_user(
            email='user@example.com',
            username='testuser',
            name='Test User',
            password='oldpassword'
        )
        self.token_generator = PasswordResetTokenGenerator()
        self.uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.token = self.token_generator.make_token(self.user)

    def test_valid_reset(self):
        """Test successful password reset with valid token"""
        data = {
            'uid': self.uid,
            'token': self.token,
            'new_pass': 'newsecurepassword123',
            'conf_pass': 'newsecurepassword123'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newsecurepassword123'))

    def test_invalid_token(self):
        """Test reset fails with invalid token"""
        data = {
            'uid': self.uid,
            'token': 'invalid-token',
            'new_pass': 'newpassword123',
            'conf_pass': 'newpassword123'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_mismatch(self):
        """Test reset fails when passwords don't match"""
        data = {
            'uid': self.uid,
            'token': self.token,
            'new_pass': 'newpassword123',
            'conf_pass': 'differentpassword'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_short_password(self):
        """Test password length validation during reset"""
        data = {
            'uid': self.uid,
            'token': self.token,
            'new_pass': 'short',
            'conf_pass': 'short'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestEmailOrUsernameModelBackend(TestCase):
    """Test custom authentication backend"""
    def setUp(self):
        self.backend = EmailOrUsernameModelBackend()
        self.user = User.objects.create_user(
            email='user@example.com',
            username='testuser',
            name='Test User',
            password='validpassword123'
        )

    def test_authenticate_with_email(self):
        """Test authentication using email"""
        user = self.backend.authenticate(
            request=None,
            username='user@example.com',
            password='validpassword123'
        )
        self.assertEqual(user, self.user)

    def test_authenticate_with_username(self):
        """Test authentication using username"""
        user = self.backend.authenticate(
            request=None,
            username='testuser',
            password='validpassword123'
        )
        self.assertEqual(user, self.user)

    def test_case_insensitive(self):
        """Test case-insensitive authentication"""
        user = self.backend.authenticate(
            request=None,
            username='USER@EXAMPLE.COM',
            password='validpassword123'
        )
        self.assertEqual(user, self.user)

    def test_invalid_password(self):
        """Test authentication fails with wrong password"""
        user = self.backend.authenticate(
            request=None,
            username='user@example.com',
            password='wrongpassword'
        )
        self.assertIsNone(user)

    def test_user_does_not_exist(self):
        """Test authentication for non-existent user"""
        user = self.backend.authenticate(
            request=None,
            username='nonexistent@example.com',
            password='testpass'
        )
        self.assertIsNone(user)