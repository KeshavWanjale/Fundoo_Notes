from django.db import models
from django.conf import settings

class Note(models.Model):
    title = models.CharField(max_length=255, null=False, db_index=True)
    description = models.TextField(null=True, blank=True)
    color = models.CharField(max_length=50, null=True, blank=True)
    image = models.ImageField(upload_to='notes/images/', null=True, blank=True)
    is_archive = models.BooleanField(default=False, db_index=True)
    is_trash = models.BooleanField(default=False, db_index=True)
    reminder = models.DateTimeField(null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.title
