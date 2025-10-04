from __future__ import annotations

import json
import re
from typing import Dict

from django.conf import settings

from .client import get_client

MEDICAL_KEYWORDS = {
    "درد",
    "تب",
    "سرفه",
    "عفونت",
    "سرگیجه",
    "استفراغ",
    "اسهال",
    "خارش",
    "rash",
    "pain",
    "vomit",
    "nausea",
    "bleeding",
    "زخم",
    "فشار خون",
    "قند",
}

ADMIN_KEYWORDS = {
    "نوبت",
    "وقت ملاقات",
    "پیگیری پرداخت",
    "گواهی",
    "نسخه",
    "appointment",
    "insurance",
    "payment",
}

SMALLTALK_KEYWORDS = {
    "سلام",
    "درود",
    "مرسی",
    "تشکر",
    "how are you",
    "thank you",
    "خداحافظ",
}

CRITICAL_KEYWORDS = {
    "درد قفسه سینه",
    "بیهوشی ناگهانی",
    "خونریزی شدید",
    "سکته",
    "سخت نفس",
    "breathless",
    "severe bleeding",
    "chest pain",
    "suicide",
    "self harm",
}

SUICIDAL_PATTERNS = (
    re.compile(r"می ?خواهم خود(?:م)? را بکشم"),
    re.compile(r"قصد خودکشی"),
    re.compile(r"life isn['’]t worth"),
)


def _extract_text(response) -> str:
    text = getattr(response, "output_text", None)
    if text:
        return str(text)
    output = getattr(response, "output", None)
    if output and isinstance(output, list) and output:
        parts: list[str] = []
        first = output[0]
        content = first.get("content") if isinstance(first, dict) else None
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "output_text":
                    text_block = item.get("text")
                    if isinstance(text_block, list):
                        parts.extend(str(part) for part in text_block)
                    elif isinstance(text_block, str):
                        parts.append(text_block)
        if parts:
            return "".join(parts)
    choices = getattr(response, "choices", None)
    if choices:
        choice = choices[0]
        if isinstance(choice, dict):
            message = choice.get("message", {})
            if isinstance(message, dict):
                return str(message.get("content", ""))
    return ""


def classify_with_llm(message: str) -> Dict[str, bool]:
    client = get_client()
    system_prompt = (
        "You are a medical privacy classifier."
        " Respond with compact JSON containing boolean fields "
        "medical_relevant, critical, admin, smalltalk."
    )
    truncated = message[: settings.SMART_STORAGE_MAX_TOKENS * 4]
    response = client.responses.create(
        model=settings.CHATBOT_DEFAULT_MODEL,
        input=[
            {
                "role": "system",
                "content": [{"type": "input_text", "text": system_prompt}],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": truncated,
                    }
                ],
            },
        ],
        max_output_tokens=120,
        temperature=0,
    )
    text = _extract_text(response).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {}
    result: Dict[str, bool] = {}
    for key in ("medical_relevant", "critical", "admin", "smalltalk"):
        result[key] = bool(data.get(key, False))
    return result


def _has_suicidal_intent(text: str) -> bool:
    return any(pattern.search(text) for pattern in SUICIDAL_PATTERNS)


def _has_pediatric_fever(text: str) -> bool:
    pediatric_markers = ["نوزاد", "دو ماه", "2 ماه", "دوماه", "baby"]
    has_marker = any(marker in text for marker in pediatric_markers)
    has_fever = "تب" in text or "fever" in text
    return has_marker and has_fever


def tag_message(message: str, *, images: int, pdf_text_len: int) -> Dict[str, bool]:
    text = (message or "").lower()
    tags: Dict[str, bool] = {
        "medical_relevant": False,
        "critical": False,
        "admin": False,
        "smalltalk": False,
    }

    if any(keyword in text for keyword in CRITICAL_KEYWORDS) or _has_suicidal_intent(text) or _has_pediatric_fever(text):
        tags["critical"] = True
        tags["medical_relevant"] = True

    if any(keyword in text for keyword in MEDICAL_KEYWORDS) or images or pdf_text_len:
        tags["medical_relevant"] = True

    if any(keyword in text for keyword in ADMIN_KEYWORDS):
        tags["admin"] = True

    if not tags["medical_relevant"] and any(keyword in text for keyword in SMALLTALK_KEYWORDS):
        tags["smalltalk"] = True

    if settings.SMART_STORAGE_CLASSIFY_WITH_LLM:
        try:
            llm_tags = classify_with_llm(message)
        except Exception:  # pragma: no cover - defensive network/SDK issues
            llm_tags = {}
        for key in tags:
            if key in llm_tags:
                tags[key] = tags[key] or bool(llm_tags[key])

    if pdf_text_len >= max(400, settings.CHATBOT_PDF_MAX_CHARS // 2):
        tags["medical_relevant"] = True

    return tags


__all__ = ["tag_message", "classify_with_llm", "MEDICAL_KEYWORDS", "CRITICAL_KEYWORDS"]
