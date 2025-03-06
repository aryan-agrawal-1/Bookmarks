from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Bookmark
from .serializers import BookmarkSerializer

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
            "user": self.user.id  # When serializing, we typically use the user ID.
    }
    
    def test_valid_bookmark_serializer(self):
        # Create a serializer instance with the bookmark data.
        serializer = BookmarkSerializer(data=self.bookmark_data)
        # Validate the data.
        self.assertTrue(serializer.is_valid(), serializer.errors)
        # Save the serializer to create a Bookmark instance.
        bookmark = serializer.save()
        # Test that the instance was created and matches the input data.
        self.assertEqual(bookmark.url, self.bookmark_data['url'])
        self.assertEqual(bookmark.title, self.bookmark_data['title'])
        self.assertEqual(bookmark.description, self.bookmark_data['description'])
        self.assertEqual(bookmark.tags, self.bookmark_data['tags'])
        self.assertEqual(bookmark.user.id, self.bookmark_data['user'])