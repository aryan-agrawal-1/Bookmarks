from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookmarkViewSet, TagViewSet

# DRF router to automatically generate RESTful routes for the viewset
router = DefaultRouter()
router.register(r'bookmarks', BookmarkViewSet, basename='bookmark') # register under bookmarks/ endpoint
router.register(r'tags', TagViewSet, basename='tag') # register under tags/ endpoint

urlpatterns = [
    path('', include(router.urls)),  # Includes all viewset routes
]

"""
GENERATED ENDPOINTS (prepended by /api/):

Bookmark Endpoints:
GET /bookmarks/ - Lists bookmarks
POST /bookmarks/ - Create bookmark
GET /bookmarks/{id} - Get bookmark
PUT/PATCH /bookmarks/{id} - Update bookmark
DELETE /bookmarks/{id} - Delete bookmark
GET /bookmarks/search/?q=keyword - Search bookmarks
POST /bookmarks/bulk_delete/ - Delete multiple bookmarks
GET /bookmarks/by_tag/ - Get bookmarks grouped by tag

Tag Endpoints:
GET /tags/ - Lists tags used by the current user
GET /tags/{id} - Get specific tag
"""
