from __future__ import annotations

import re
from typing import Iterable

_PATTERNS: Iterable[tuple[re.Pattern[str], str]] = (
    (re.compile(r"\b\+?98\d{10}\b"), "<phone>"),
    (re.compile(r"\b0\d{10}\b"), "<phone>"),
    (re.compile(r"\b\d{10,16}\b"), "<national_code>"),
    (
        re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", re.IGNORECASE),
        "<email>",
    ),
    (re.compile(r"\b(?:token|otp|code)[:\s]*[A-Za-z0-9]{4,}\b", re.IGNORECASE), "<secret>"),
)


def redact_text(value: str) -> str:
    text = value or ""
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def scrub_for_cache_key(value: str) -> str:
    text = redact_text(value)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:256]


__all__ = ["redact_text", "scrub_for_cache_key"]
