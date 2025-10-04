from __future__ import annotations

from typing import Iterable

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class AskSerializer(serializers.Serializer):
    message = serializers.CharField(trim_whitespace=True)
    model = serializers.CharField(required=False, allow_blank=False)
    stream = serializers.BooleanField(required=False, default=False)
    images = serializers.ListField(
        child=serializers.FileField(), required=False, allow_empty=True, default=list
    )
    pdfs = serializers.ListField(
        child=serializers.FileField(), required=False, allow_empty=True, default=list
    )
    cache_ttl = serializers.IntegerField(required=False, min_value=1)
    store = serializers.ChoiceField(
        choices=tuple((choice, choice) for choice in sorted(settings.SMART_STORAGE_ALLOWED_STORE_VALUES)),
        required=False,
        default="auto",
    )
    consent = serializers.BooleanField(required=False)
    purge = serializers.BooleanField(required=False, default=False)
    source_turn_id = serializers.CharField(required=False, allow_blank=True, max_length=64)
    conversation_id = serializers.UUIDField(required=False)
    history = serializers.ListField(child=serializers.DictField(), required=False)
    reset = serializers.BooleanField(required=False, default=False)

    image_types = {"image/jpeg", "image/png", "image/webp"}
    pdf_types = {"application/pdf"}

    def validate_store(self, value: str) -> str:
        return (value or "auto").lower()

    def validate_source_turn_id(self, value: str) -> str:
        return value.strip()

    def validate_message(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError(_("Message cannot be empty."))
        return value

    def _validate_files(
        self,
        files: Iterable,
        *,
        allowed_types: set[str],
        max_files: int,
    ) -> list:
        files = list(files or [])
        if len(files) > max_files:
            raise serializers.ValidationError(
                _(f"Maximum of {max_files} files allowed."), code="max_files"
            )
        max_bytes = settings.CHATBOT_MAX_FILE_MB * 1024 * 1024
        for file in files:
            content_type = getattr(file, "content_type", None)
            if content_type not in allowed_types:
                raise serializers.ValidationError(
                    _("Unsupported file type."), code="invalid_type"
                )
            if file.size is not None and file.size > max_bytes:
                raise serializers.ValidationError(
                    _(f"Each file must be under {settings.CHATBOT_MAX_FILE_MB}MB."),
                    code="max_size",
                )
        return files

    def validate_images(self, files):
        return self._validate_files(
            files,
            allowed_types=self.image_types,
            max_files=settings.CHATBOT_MAX_IMAGE_FILES,
        )

    def validate_pdfs(self, files):
        return self._validate_files(
            files,
            allowed_types=self.pdf_types,
            max_files=settings.CHATBOT_MAX_PDF_FILES,
        )

    def validate(self, attrs):
        images = attrs.get("images") or []
        pdfs = attrs.get("pdfs") or []
        total_bytes = 0
        for file_list in (images, pdfs):
            for file in file_list:
                if getattr(file, "size", None) is None:
                    continue
                total_bytes += file.size
        max_payload = settings.CHATBOT_MAX_PAYLOAD_MB * 1024 * 1024
        if total_bytes > max_payload:
            raise serializers.ValidationError(
                {"non_field_errors": _(f"Total upload size must be under {settings.CHATBOT_MAX_PAYLOAD_MB}MB.")}
            )
        return attrs

