from django.test import TestCase, RequestFactory
from rest_framework import status
from rest_framework.test import APITestCase, force_authenticate, APIClient
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from .models import Bookmark
from .serializers import BookmarkSerializer
import json

# Create your tests here.
User = get_user_model()

class BookmarkModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
    
    def test_create_bookmark(self):

        bookmark = Bookmark.objects.create(
            url="https://example.com",
            title="Example",
            description="Example description",
            tags="example, test",
            user=self.user
        )

        self.assertEqual(bookmark.url, "https://example.com")
        self.assertEqual(bookmark.title, "Example")
        self.assertEqual(bookmark.description, "Example description")
        self.assertEqual(bookmark.tags, "example, test")
        self.assertEqual(bookmark.user, self.user)

        # The string representation should be the title.
        self.assertEqual(str(bookmark), "Example")

class BookmarkSerializerTest(TestCase):

    def setUp(self):
        # Create a test user.
        self.user = User.objects.create_user(username='testuser', password='testpass')

        # Define sample bookmark data.
        self.bookmark_data = {
            "url": "https://example.com",
            "title": "Example",
            "description": "Example description",
            "tags": "example, test",
            
        }
        self.request = RequestFactory().get('/')
        self.request.user = self.user
    
    def test_valid_bookmark_serializer(self):
        # Create a serializer instance with the bookmark data.
        serializer = BookmarkSerializer(data=self.bookmark_data)
        # Validate the data.
        self.assertTrue(serializer.is_valid(), serializer.errors)
        # Save the serializer to create a Bookmark instance.
        bookmark = serializer.save(user=self.user)
        # Test that the instance was created and matches the input data.
        self.assertEqual(bookmark.url, self.bookmark_data['url'])
        self.assertEqual(bookmark.title, self.bookmark_data['title'])
        self.assertEqual(bookmark.description, self.bookmark_data['description'])
        self.assertEqual(bookmark.tags, self.bookmark_data['tags'])
        self.assertEqual(bookmark.user.id, self.user.id)

class BookmarkAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client = APIClient()
        self.access_token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        self.bookmark = Bookmark.objects.create(
            url="https://example.com",
            title="Example",
            description="Test description",
            tags="test",
            user=self.user
        )

    def test_list_bookmarks(self):
        response = self.client.get("/api/bookmarks/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["url"], "https://example.com")

    def test_create_bookmark(self):
        data = {
            "url": "https://newsite.com",
            "title": "New Site",
            "description": "New bookmark",
            "tags": "new, bookmark"
        }

        response = self.client.post("/api/bookmarks/", json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Bookmark.objects.count(), 2)

    def test_update_bookmark(self):
        data = {"title": "Updated Example"}
        response = self.client.patch(f"/api/bookmarks/{self.bookmark.id}/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.bookmark.refresh_from_db()
        self.assertEqual(self.bookmark.title, "Updated Example")

    def test_delete_bookmark(self):
        response = self.client.delete(f"/api/bookmarks/{self.bookmark.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Bookmark.objects.count(), 0)

    def test_search_bookmarks(self):
        response = self.client.get("/api/bookmarks/search/?q=Example")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Example")
