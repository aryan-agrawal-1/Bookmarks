from rest_framework import viewsets, permissions # Viewset provides built in CRUD
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Bookmark
from django.db.models import Q
from .serializers import BookmarkSerializer

# Create your views here.

class BookmarkViewSet(viewsets.ModelViewSet):
    serializer_class = BookmarkSerializer
    permission_classes = [permissions.IsAuthenticated] # Only authenticated users

    def get_queryset(self):
        # restrict results to bookmarks belonging to user
        return Bookmark.objects.filter(user = self.request.user)

    # Automatically set user field when a bookmark is created
    def perform_create(self, serializer):
        # Saves the bookmark with the authenticated user as the owner.
        serializer.save(user = self.request.user)
    
    # Add a search endpoint allowing users to find bookmarks by title, description, or URL.
    @action(detail= False, methods=["get"])
    def search(self, request):
        # Allows users to search bookmarks by title, description, or URL

        query = request.query_params.get("q", "")

        if query:
            results = Bookmark.objects.filter(user=request.user).filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query) |
                Q(url__icontains=query)
            )
            serializer = self.get_serializer(results, many=True)
            return Response(serializer.data)
        
        return Response({"detail": "No search query provided."}, status=400)