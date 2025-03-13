from rest_framework import viewsets, permissions, status, filters # Viewset provides built in CRUD
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend

from .models import Bookmark, Tag
from django.db.models import Q

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .serializers import BookmarkSerializer, TagSerializer
from .services.metadata_extractor import extract_url_metadata_sync

import asyncio
import datetime

# Helper function to get a date range from now
def get_date_range(days=None, months=None, years=None):
    today = datetime.datetime.now().date()
    if days:
        return today - datetime.timedelta(days=days)
    elif months:
        # Approximate months with days
        return today - datetime.timedelta(days=30*months)
    elif years:
        # Approximate years with days
        return today - datetime.timedelta(days=365*years)
    return None

class TagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Return only tags that are used by the current user's bookmarks
        """

        user = self.request.user
        return Tag.objects.filter(bookmarks__user=user).distinct()

class BookmarkViewSet(viewsets.ModelViewSet):

    serializer_class = BookmarkSerializer
    permission_classes = [permissions.IsAuthenticated] # Only authenticated users

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['source', 'content_type']
    search_fields = ['title', 'description', 'url', 'tags__name']
    
    ordering_fields = ['created_at', 'updated_at', 'title']
    ordering = ['-created_at']  # Default ordering

    def get_queryset(self):
        # Return bookmarks belonging to the current user with optional filtering by source or tag
        user = self.request.user
        queryset = Bookmark.objects.filter(user=user)

        # Filter by source
        source = self.request.query_params.get('source')
        if source:
            queryset = queryset.filter(source=source)
        
        # Filter by tag(s)
        tag = self.request.query_params.get('tag')
        if tag:
            # Support comma-separated list of tags
            tag_list = tag.split(',')
            # Filter bookmarks that have ALL of the specified tags
            for t in tag_list:
                queryset = queryset.filter(tags__name=t.strip())
        
        # Filter by time period
        time_period = self.request.query_params.get('period')
        if time_period:
            date_threshold = None
            
            if time_period == 'today':
                date_threshold = get_date_range(days=1)
            elif time_period == 'week':
                date_threshold = get_date_range(days=7)
            elif time_period == 'month':
                date_threshold = get_date_range(months=1)
            elif time_period == 'year':
                date_threshold = get_date_range(years=1)
            
            if date_threshold:
                queryset = queryset.filter(created_at__gte=date_threshold)
        
        # Filter by content type
        content_type = self.request.query_params.get('content_type')
        if content_type:
            queryset = queryset.filter(content_type=content_type)
    
        return queryset

    # Override create to extract metadata from URL
    def perform_create(self, serializer):
        url = serializer.validated_data.get('url')

        # Extract metadata from URL
        metadata = extract_url_metadata_sync(url)

        # Only set values that aren't already provided
        if 'title' not in serializer.validated_data or not serializer.validated_data['title']:
            serializer.validated_data['title'] = metadata.get('title')
        
        if 'description' not in serializer.validated_data or not serializer.validated_data['description']:
            serializer.validated_data['description'] = metadata.get('description')
            
        if 'preview_image' not in serializer.validated_data or not serializer.validated_data['preview_image']:
            serializer.validated_data['preview_image'] = metadata.get('preview_image')
            
        if 'favicon' not in serializer.validated_data or not serializer.validated_data['favicon']:
            serializer.validated_data['favicon'] = metadata.get('favicon')
            
        if 'content_type' not in serializer.validated_data or not serializer.validated_data['content_type']:
            serializer.validated_data['content_type'] = metadata.get('content_type')

        # Save with user
        serializer.save(user=self.request.user)
    
    # Add a new action to refresh metadata for existing bookmarks
    @action(detail=True, methods=['post'])
    def refresh_metadata(self, request, pk=None):
        """
        Refreshes metadata for an existing bookmark
        """
        bookmark = self.get_object() # Get the current bookmark
        
        # Extract new metadata
        metadata = extract_url_metadata_sync(bookmark.url)
        
        # Update bookmark with new metadata
        if metadata.get('title'):
            bookmark.title = metadata.get('title')
        if metadata.get('description'):
            bookmark.description = metadata.get('description')
        if metadata.get('preview_image'):
            bookmark.preview_image = metadata.get('preview_image')
        if metadata.get('favicon'):
            bookmark.favicon = metadata.get('favicon')
        if metadata.get('content_type'):
            bookmark.content_type = metadata.get('content_type')
        
        bookmark.save()
        
        # Return updated bookmark
        serializer = self.get_serializer(bookmark)
        return Response(serializer.data)

    # Add a search endpoint allowing users to find bookmarks by title, description, or URL.
    @action(detail= False, methods=["get"])
    def search(self, request):
        # Allows users to search bookmarks by title, description, URL or tags

        query = request.query_params.get("q", "") # Will be in the url

        if query:
            results = Bookmark.objects.filter(user=request.user).filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query) |
                Q(url__icontains=query) |
                Q(tags__name__icontains=query) 
            ).distinct()

            serializer = self.get_serializer(results, many=True)
            return Response(serializer.data)
        
        return Response({"detail": "No search query provided."}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=["post"])
    def bulk_delete(self, request):
        """
        Delete multiple bookmarks at once
        """
        ids = request.data.get('ids', [])

        if not ids:
            return Response({"detail": "No IDs provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure user can only delete their own bookmarks
        deleted_count = Bookmark.objects.filter(id__in=ids, user=request.user).delete()[0]

        return Response({
            "detail": f"Successfully deleted {deleted_count} bookmarks."
        })
    
    @action(detail=False, methods=["get"])
    def by_tag(self, request):
        """
        Get bookmarks organized by tag
        """

        user_tags = Tag.objects.filter(bookmarks__user=request.user).distinct()
        result = {}
        
        for tag in user_tags:
            bookmarks = Bookmark.objects.filter(user=request.user, tags=tag)
            serializer = self.get_serializer(bookmarks, many=True)
            result[tag.name] = serializer.data
            
        return Response(result)
        
