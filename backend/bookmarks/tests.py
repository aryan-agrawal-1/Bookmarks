from django.test import TestCase, RequestFactory
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from .models import Bookmark, Tag
from .serializers import BookmarkSerializer, TagSerializer
import json

# Create your tests here.
User = get_user_model()

class TagModelTest(TestCase):
    def test_create_tag(self):
        tag = Tag.objects.create(name="example")
        self.assertEqual(tag.name, "example")
        self.assertEqual(str(tag), "example")

class BookmarkModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.tag1 = Tag.objects.create(name="example")
        self.tag2 = Tag.objects.create(name="test")
    
    def test_create_bookmark(self):

        bookmark = Bookmark.objects.create(
            url="https://example.com",
            title="Example",
            description="Example description",
            user=self.user,
            source="manual",
            content_type="article"
        )

        bookmark.tags.add(self.tag1, self.tag2)

        self.assertEqual(bookmark.url, "https://example.com")
        self.assertEqual(bookmark.title, "Example")
        self.assertEqual(bookmark.description, "Example description")
        self.assertEqual(bookmark.user, self.user)
        self.assertEqual(bookmark.source, "manual")
        self.assertEqual(bookmark.content_type, "article")

        self.assertEqual(bookmark.tags.count(), 2)
        self.assertTrue(self.tag1 in bookmark.tags.all())
        self.assertTrue(self.tag2 in bookmark.tags.all())

        # The string representation should be the title.
        self.assertEqual(str(bookmark), "Example")
    
    def test_bookmark_url_validation(self):
        # Test with invalid URL
        with self.assertRaises(Exception):
            Bookmark.objects.create(
                url="invalid-url",
                title="Invalid",
                user=self.user
            )

class TagSerializerTest(TestCase):
    def test_valid_tag_serializer(self):
        tag_data = {"name": "example"}
        serializer = TagSerializer(data=tag_data)
        self.assertTrue(serializer.is_valid())

class BookmarkSerializerTest(TestCase):

    def setUp(self):
        # Create a test user.
        self.user = User.objects.create_user(username='testuser', password='testpass')

        # Define sample bookmark data.
        self.bookmark_data = {
            "url": "https://example.com",
            "title": "Example",
            "description": "Example description",
            "tag_names": ["example", "test"],
            "source": "manual",
            "content_type": "article"
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
        self.assertEqual(bookmark.source, self.bookmark_data['source'])
        self.assertEqual(bookmark.content_type, self.bookmark_data['content_type'])
        self.assertEqual(bookmark.user.id, self.user.id)
        # Check that tags were created
        self.assertEqual(bookmark.tags.count(), 2)
        tag_names = [tag.name for tag in bookmark.tags.all()]
        self.assertTrue("example" in tag_names)
        self.assertTrue("test" in tag_names)

class BookmarkAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client = APIClient()
        self.access_token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        # Create tags
        self.tag1 = Tag.objects.create(name="example")
        self.tag2 = Tag.objects.create(name="test")

        self.bookmark = Bookmark.objects.create(
            url="https://example.com",
            title="Example",
            description="Test description",
            user=self.user,
            source="manual",
            content_type="article"
        )
        self.bookmark.tags.add(self.tag1)

    def test_list_bookmarks(self):
        response = self.client.get("/api/bookmarks/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["url"], "https://example.com")
        self.assertEqual(len(response.data[0]["tags"]), 1)
        self.assertEqual(response.data[0]["tags"][0]["name"], "example")

    def test_update_bookmark_with_tags(self):

        data = {
            "title": "Updated Example",
            "tag_names": ["updated", "example"]
        }

        # Send patch (Update request)
        response = self.client.patch(
            f"/api/bookmarks/{self.bookmark.id}/", 
            json.dumps(data), 
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.bookmark.refresh_from_db()
        self.assertEqual(self.bookmark.title, "Updated Example")
        
        # Check that tags were updated
        self.assertEqual(self.bookmark.tags.count(), 2)
        tag_names = [tag.name for tag in self.bookmark.tags.all()]
        self.assertTrue("updated" in tag_names)
        self.assertTrue("example" in tag_names)

    def test_delete_bookmark(self):
        response = self.client.delete(f"/api/bookmarks/{self.bookmark.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Bookmark.objects.count(), 0)

    def test_search_bookmarks(self):
        response = self.client.get("/api/bookmarks/search/?q=Example")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Example")
        
        # Search by tag
        response = self.client.get("/api/bookmarks/search/?q=example")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
    def test_filter_bookmarks_by_source(self):
        response = self.client.get("/api/bookmarks/?source=manual")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        response = self.client.get("/api/bookmarks/?source=reddit")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
        
    def test_filter_bookmarks_by_tag(self):
        response = self.client.get("/api/bookmarks/?tag=example")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        response = self.client.get("/api/bookmarks/?tag=nonexistent")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
        
    def test_bulk_delete_bookmarks(self):
        # Create a second bookmark
        bookmark2 = Bookmark.objects.create(
            url="https://example2.com",
            title="Example 2",
            user=self.user
        )
        
        data = {"ids": [self.bookmark.id, bookmark2.id]}
        response = self.client.post(
            "/api/bookmarks/bulk_delete/", 
            json.dumps(data), 
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Bookmark.objects.count(), 0)
        
    def test_get_bookmarks_by_tag(self):
        # Create a second bookmark with different tag
        bookmark2 = Bookmark.objects.create(
            url="https://example2.com",
            title="Example 2",
            user=self.user
        )
        bookmark2.tags.add(self.tag2)
        
        response = self.client.get("/api/bookmarks/by_tag/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("example" in response.data)
        self.assertTrue("test" in response.data)
        self.assertEqual(len(response.data["example"]), 1)
        self.assertEqual(len(response.data["test"]), 1)