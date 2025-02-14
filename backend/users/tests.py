from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import CustomUser
from .backends import EmailOrUsernameModelBackend
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.core.exceptions import ValidationError

User = get_user_model()

# Model Tests
class TestUserModel(TestCase):
    # Simple user creation check
    def test_create_user(self):
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            name='Test User',
            password='password'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.username, 'testuser')
        self.assertFalse(user.email_verified)
        self.assertTrue(user.check_password('password'))

    def test_email_uniqueness_case_insensitive(self):
        User.objects.create_user(
            email='test@example.com',
            username='user1',
            name='User 1',
            password='password'
        )
        with self.assertRaises(ValidationError):
            User.objects.create_user(
                email='TEST@EXAMPLE.COM',
                username='user2',
                name='User 2',
                password='password'
            )

    def test_username_uniqueness_case_insensitive(self):
        User.objects.create_user(
            email='user1@example.com',
            username='testuser',
            name='User 1',
            password='password'
        )
        with self.assertRaises(ValidationError):
            User.objects.create_user(
                email='user2@example.com',
                username='TESTUSER',
                name='User 2',
                password='password'
            )

    def test_string_representation(self):
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            name='Test User',
            password='password'
        )
        self.assertEqual(str(user), "Test User (test@example.com)")


# Authentication Backend Tests
class TestAuthenticationBackend(TestCase):
    # Create a User we can test on
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            name='Test User',
            password='password'
        )
        self.backend = EmailOrUsernameModelBackend()


    def test_authenticate_with_email(self):
        user = self.backend.authenticate(request=None, username='test@example.com', password='password')
        self.assertEqual(user, self.user)

    def test_authenticate_with_email_case_insensitive(self):
        user = self.backend.authenticate(None, username='TEST@EXAMPLE.COM', password='password')
        self.assertEqual(user, self.user)

    def test_authenticate_with_username(self):
        user = self.backend.authenticate(None, username='testuser', password='password')
        self.assertEqual(user, self.user)

    def test_authenticate_with_username_case_insensitive(self):
        user = self.backend.authenticate(None, username='TESTUSER', password='password')
        self.assertEqual(user, self.user)

    def test_authenticate_invalid_credentials(self):
        self.assertIsNone(self.backend.authenticate(None, username='test@example.com', password='wrong'))
        self.assertIsNone(self.backend.authenticate(None, username='nonexistent', password='password'))


# API Tests
class TestRegistrationAPI(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/auth/register/'
        self.valid_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'password',
            'conf_password': 'password'
        }

    def test_successful_registration(self):
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.first()
        self.assertEqual(user.email, self.valid_data['email'])
        self.assertEqual(user.username, self.valid_data['username'])

    def test_email_case_insensitive_uniqueness(self):
        # Create a user with the original email
        self.client.post(self.url, self.valid_data)

        # Attempt to register with the same email but different case
        data = {**self.valid_data, 'email': 'TEST@EXAMPLE.COM', 'username': 'newuser'}
        response = self.client.post(self.url, data)

        # Check that the response contains the expected error
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertEqual(response.data['email'][0], "A user with this email already exists.")

    def test_username_case_insensitive_uniqueness(self):
        # Create a user with the original username
        self.client.post(self.url, self.valid_data)

        # Attempt to register with the same username but different case
        data = {**self.valid_data, 'email': 'new@example.com', 'username': 'TESTUSER'}
        response = self.client.post(self.url, data)

        # Check that the response contains the expected error
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
        self.assertEqual(response.data['username'][0], "A user with this username already exists.")

    def test_password_mismatch(self):
        data = {**self.valid_data, 'conf_password': 'mismatch'}
        response = self.client.post(self.url, data)
        print(response.status_code)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('conf_password', response.data)


class TestLoginAPI(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/auth/login/'
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            name='Test User',
            password='password'
        )

    def test_login_with_email(self):
        response = self.client.post(self.url, {'email': 'test@example.com', 'password': 'password'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_login_with_email_case_insensitive(self):
        response = self.client.post(self.url, {'email': 'TEST@EXAMPLE.COM', 'password': 'password'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_with_username(self):
        response = self.client.post(self.url, {'email': 'testuser', 'password': 'password'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_with_username_case_insensitive(self):
        response = self.client.post(self.url, {'email': 'TESTUSER', 'password': 'password'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_credentials(self):
        response = self.client.post(self.url, {'email': 'test@example.com', 'password': 'wrong'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)