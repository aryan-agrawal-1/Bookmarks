from rest_framework import serializers
from .models import Bookmark, Tag

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']

class BookmarkSerializer(serializers.ModelSerializer):
    # Nested serializer for tags with ability to create new tags
    tags = TagSerializer(many=True, required=False, read_only=True)

    # Field to accept a list of tag names from the client
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=50), # Each tag max length
        write_only=True,
        required=False
    )

    class Meta:
        model = Bookmark
        fields = [
            'id', 'url', 'title', 'description', 'created_at', 'updated_at',
            'user', 'tags', 'tag_names', 'source', 'source_id', 'content_type',
            'preview_image', 'favicon'
        ]
        read_only_fields = ('user', 'id', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        """
        Override create method to handle tag creation/assignment
        """
        # Extract tag_names from validated data (if present)
        tag_names = validated_data.pop('tag_names', [])
        
        # Create the bookmark
        bookmark = Bookmark.objects.create(**validated_data)
        
        # Add tags
        self._get_or_create_tags(bookmark, tag_names)
        
        return bookmark
    
    def update(self, instance, validated_data):
        """
        Override update method to handle tag updates
        """
        # Extract tag_names from validated data (if present)
        tag_names = validated_data.pop('tag_names', None)
        
        # Update the bookmark with all other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update tags if provided
        if tag_names is not None:
            # Clear existing tags
            instance.tags.clear()
            # Add new tags
            self._get_or_create_tags(instance, tag_names)
        
        return instance
    
    def _get_or_create_tags(self, bookmark, tag_names):
        """
        Helper method to get existing tags or create new ones
        and associate them with the bookmark
        """
        for tag_name in tag_names:
            tag_name = tag_name.strip().lower()
            if tag_name:
                tag, _ = Tag.objects.get_or_create(name=tag_name)
                bookmark.tags.add(tag)
