from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
# Create your models here.

# Creating our user model
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)  # Ensure email is unique
    name = models.CharField(max_length=100, blank=False, null=False)  # Single name field
    email_verified = models.BooleanField(default=False)
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "name"]

    # Ensure no case insensitive dupes
    def save(self, *args, **kwargs):
        if CustomUser.objects.filter(email__iexact = self.email).exclude(pk = self.pk).exists():
             raise ValidationError({"email": "A user with this email already exists."})
        
        if CustomUser.objects.filter(username__iexact = self.username).exclude(pk = self.pk).exists():
             raise ValidationError({"username": "A user with this username already exists."})

        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.email})"
