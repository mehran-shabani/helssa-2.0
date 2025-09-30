from __future__ import annotations

from django.db import models


class IdempotencyKey(models.Model):
    key = models.CharField(max_length=160, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Idempotency Key"
        verbose_name_plural = "Idempotency Keys"

    def __str__(self) -> str:
        return self.key
