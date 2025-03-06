from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

class Bookmark(models.Model):
    url = models.URLField(max_length=500)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(blank=True, null=True)
    tags = models.CharField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add =True)
    updated_at = models.DateTimeField(auto_now =True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookmarks")

    def __str__(self):
        return self.title if self.title else self.url

