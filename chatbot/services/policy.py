from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Dict

from django.conf import settings
from django.core.cache import cache

from .redact import scrub_for_cache_key
from .triage import tag_message


@dataclass
class Decision:
    mode: str
    tags: Dict[str, bool]
    reason: str


def _allowed_default(default_mode: str) -> str:
    allowed = getattr(settings, "SMART_STORAGE_ALLOWED_STORE_VALUES", {"auto", "none", "summary", "full"})
    default_mode = (default_mode or "summary").lower()
    if default_mode not in allowed:
        return "summary"
    return default_mode


def decide_storage(
    message: str,
    images: int,
    pdf_text_len: int,
    consent: bool,
    requested: str | None,
    django_settings=settings,
) -> Decision:
    requested_value = (requested or "auto").lower()
    allowed = getattr(django_settings, "SMART_STORAGE_ALLOWED_STORE_VALUES", {"auto", "none", "summary", "full"})
    if requested_value not in allowed:
        requested_value = "auto"

    cache_key = None
    tags = None
    cache_ttl = getattr(django_settings, "SMART_STORAGE_CACHE_TTL_SECONDS", 0)
    if cache_ttl and message:
        scrubbed = scrub_for_cache_key(message)
        digest = hashlib.sha256(f"{scrubbed}|{images}|{pdf_text_len}".encode("utf-8")).hexdigest()
        cache_key = f"chatbot:smart:triage:{digest}"
        cached_tags = cache.get(cache_key)
        if isinstance(cached_tags, dict):
            tags = {key: bool(value) for key, value in cached_tags.items()}

    if tags is None:
        tags = tag_message(message, images=images, pdf_text_len=pdf_text_len)
        if cache_key:
            cache.set(cache_key, tags, cache_ttl)

    if not getattr(django_settings, "SMART_STORAGE_ENABLED", True):
        return Decision(mode="none", tags=tags, reason="disabled")

    if getattr(django_settings, "SMART_STORAGE_REQUIRE_CONSENT", True) and not consent:
        return Decision(mode="none", tags=tags, reason="consent_required")

    if requested_value in {"none", "summary", "full"}:
        return Decision(mode=requested_value, tags=tags, reason=f"user_requested_{requested_value}")

    default_mode = _allowed_default(getattr(django_settings, "SMART_STORAGE_DEFAULT_MODE", "summary"))
    mode = default_mode if default_mode in {"none", "summary", "full"} else "summary"
    reason = "default_policy"

    if not tags.get("medical_relevant", False):
        mode = "none"
        reason = "not_medical"
    else:
        if tags.get("critical", False):
            mode = "full"
            reason = "critical_signal"
        elif tags.get("admin", False) or tags.get("smalltalk", False):
            mode = "none"
            reason = "non_clinical"
        else:
            mode = "summary"
            reason = "medical_summary"

        approx_length = len(message) + pdf_text_len
        max_tokens = getattr(django_settings, "SMART_STORAGE_MAX_TOKENS", 3000)
        if mode == "full" and approx_length > max_tokens * 4:
            mode = "summary"
            reason = "length_capped"
        elif pdf_text_len >= max(400, getattr(django_settings, "CHATBOT_PDF_MAX_CHARS", 8000) // 2):
            if mode == "summary":
                reason = "pdf_summary"

    return Decision(mode=mode, tags=tags, reason=reason)


__all__ = ["Decision", "decide_storage"]
