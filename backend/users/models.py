from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

# Creating our user model
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)  # Ensure email is unique
    name = models.CharField(max_length=100, blank=False, null=False)  # Single name field
    email_verified = models.BooleanField(default=False)
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "name"]
    
    def __str__(self):
        return f"{self.name} ({self.email})"
