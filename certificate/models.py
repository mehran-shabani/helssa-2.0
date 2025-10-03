from django.conf import settings
from django.db import models


class Certificate(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=120)
    body = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
