from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

class Log(models.Model):
    method = models.CharField(max_length=20, null=False)
    url = models.TextField(null=False)
    count = models.IntegerField(default=1)
    
    def __str__(self):
        return f"{self.method} {self.url} - Count: {self.count}"