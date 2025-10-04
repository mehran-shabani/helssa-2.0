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
