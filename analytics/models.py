from django.conf import settings
from django.db import models


class Event(models.Model):
    name = models.CharField(max_length=60)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    props = models.JSONField(default=dict, blank=True)
    at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self) -> str:
        return f"{self.name}@{self.at:%Y-%m-%d %H:%M:%S}"

class StatsDaily(models.Model):
    day = models.DateField(db_index=True, unique=True)
    rx_started = models.PositiveIntegerField(default=0)
    rx_delivered = models.PositiveIntegerField(default=0)
    pay_success = models.PositiveIntegerField(default=0)
    pay_tat_p50_ms = models.PositiveIntegerField(default=0)
    pay_tat_p95_ms = models.PositiveIntegerField(default=0)
    apk_downloads = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return f"StatsDaily({self.day})"
