from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

User = get_user_model()

"""
Model to store tags that can be associated with bookmarks.
"""
class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class Bookmark(models.Model):

    url = models.URLField(max_length=500, validators=[URLValidator]) # Ensure proper url
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add =True)
    updated_at = models.DateTimeField(auto_now =True)

    tags = models.ManyToManyField(Tag, related_name="bookmarks", blank=True) # Relation table auto created
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookmarks")

    SOURCE_CHOICES = (
        ('manual', 'Manual Addition'),
        ('twitter', 'Twitter'),
        ('reddit', 'Reddit'),
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('pinterest', 'Pinterest'),
        ('pocket', 'Pocket'),
        ('tiktok', 'TikTok'),
        ('youtube', 'YouTube'),
    )

    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manual')
    source_id = models.CharField(max_length=255, blank=True, null=True)  # ID from the source platform

    content_type = models.CharField(max_length=50, blank=True, null=True)  # article, video, image, etc.
    preview_image = models.URLField(max_length=500, blank=True, null=True)
    favicon = models.URLField(max_length=500, blank=True, null=True)

    def clean(self):
        """
        Custom validation to ensure URL is valid and properly formatted
        """

        urlValidaitor = URLValidator()

        try:
            urlValidaitor(self.url)

        except ValidationError:
            raise ValidationError({'url': 'Enter a valid URL.'})
    
    def save(self, *args, **kwargs):
        # Ensure validation is run
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title if self.title else self.url

