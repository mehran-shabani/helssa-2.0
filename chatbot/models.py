from __future__ import annotations

import hashlib

from django.conf import settings
from django.core.files.base import File
from django.db import models


class Attachment(models.Model):
    KIND_IMAGE = "image"
    KIND_PDF = "pdf"
    KIND_CHOICES = (
        (KIND_IMAGE, "Image"),
        (KIND_PDF, "PDF"),
    )

    file = models.FileField(upload_to="chatbot/")
    kind = models.CharField(max_length=10, choices=KIND_CHOICES)
    sha256 = models.CharField(max_length=64, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:  # pragma: no cover - repr helper
        return f"Attachment(kind={self.kind}, sha={self.sha256[:8]})"

    @staticmethod
    def compute_sha(file_obj: File) -> str:
        file_obj.seek(0)
        digest = hashlib.sha256()
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
            digest.update(chunk)
        file_obj.seek(0)
        return digest.hexdigest()

    @classmethod
    def maybe_persist(
        cls,
        *,
        file_obj: File,
        kind: str,
    ) -> None:
        if not getattr(settings, "CHATBOT_SAVE_UPLOADS", False):
            return
        sha = cls.compute_sha(file_obj)
        cls.objects.get_or_create(
            sha256=sha,
            defaults={"kind": kind, "file": file_obj},
        )


class ChatConsent(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    granted = models.BooleanField(default=False)
    scope = models.CharField(max_length=32, default="medical_history")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "scope")

    def __str__(self) -> str:  # pragma: no cover - repr helper
        user_display = getattr(self.user, "pk", "anonymous")
        return f"ChatConsent(user={user_display}, scope={self.scope}, granted={self.granted})"


class ChatNote(models.Model):
    """
    Purpose-limited medical summary (not a diagnosis): minimal fields extracted from a turn.
    """

    conversation_id = models.UUIDField(db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    title = models.CharField(max_length=200, blank=True)
    summary = models.TextField()
    tags = models.JSONField(default=dict)
    source_turn_id = models.CharField(max_length=64, blank=True)
    attachments_present = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    retention_at = models.DateTimeField(db_index=True)

    class Meta:
        indexes = [models.Index(fields=["conversation_id", "created_at"])]
        ordering = ("-created_at",)

    def __str__(self) -> str:  # pragma: no cover - repr helper
        return f"ChatNote({self.conversation_id}, tags={self.tags})"
