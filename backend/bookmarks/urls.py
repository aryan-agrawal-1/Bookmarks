from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookmarkViewSet

# DRF router to automatically generate RESTful routes for the viewset
router = DefaultRouter()
router.register(r'bookmarks', BookmarkViewSet, basename='bookmark') # register under bookmarks/ endpoint

urlpatterns = [
    path('', include(router.urls)),  # Includes all viewset routes
]

"""
GENERATED ENDPOINTS:
GET /bookmarks/ - Lists bookmarks
POST /bookmarks/ - Create bookmark
GET /bookmarks/{id} - Get bookmark
PUT/PATCH /bookmarks/{id} - Update bookmark
DELETE /bookmarks/{id} - Delete bookmark
GET /bookmarks/search/?q=keyword - Search bookmarks

"""
