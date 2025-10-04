from __future__ import annotations

from django.conf import settings


def allowed_models() -> set[str]:
    return set(getattr(settings, "CHATBOT_ALLOWED_MODELS", set()))


def is_allowed(model: str | None) -> bool:
    if not model:
        return False
    return model in allowed_models()


def select_model(
    *,
    requested_model: str | None,
    has_images: bool,
    has_pdf_text: bool,
) -> str:
    if requested_model and is_allowed(requested_model):
        return requested_model
    if has_images and settings.CHATBOT_VISION_MODEL:
        return settings.CHATBOT_VISION_MODEL
    if has_pdf_text and settings.CHATBOT_REASONING_MODEL:
        return settings.CHATBOT_REASONING_MODEL
    return settings.CHATBOT_DEFAULT_MODEL


__all__ = ["allowed_models", "is_allowed", "select_model"]
