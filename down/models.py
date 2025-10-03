from django.db import models


class APKDownloadStat(models.Model):
    key = models.CharField(max_length=64, unique=True)
    count = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
