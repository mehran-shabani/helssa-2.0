from __future__ import annotations

import json
import re
from typing import Iterable, Tuple

from django.conf import settings

from .client import get_client
from .redact import redact_text
from .triage import MEDICAL_KEYWORDS

DISCLAIMER = "این خلاصه‌ی اطلاعاتی است و جایگزین تشخیص یا نسخه پزشکی نیست."

DURATION_PATTERN = re.compile(
    r"(\d+\s*(?:روز|هفته|ماه|سال|day|days|week|weeks|month|months|year|years))",
    re.IGNORECASE,
)
MED_PATTERN = re.compile(
    r"(آنتی بیوتیک|آموکسی|استامینوفن|مسکن|بروفن|دارو|قرص|antibiotic|ibuprofen|acetaminophen)",
    re.IGNORECASE,
)


def _first_sentence(text: str, limit: int = 120) -> str:
    for separator in ("\n", "؟", "?", "!", "!", "،", "."):
        if separator in text:
            fragment = text.split(separator)[0]
            if fragment:
                return fragment.strip()[:limit]
    return text.strip()[:limit]


def _collect_keywords(text: str, keywords: Iterable[str]) -> list[str]:
    found: list[str] = []
    lowered = text.lower()
    for keyword in keywords:
        if keyword.lower() in lowered:
            found.append(keyword)
    return list(dict.fromkeys(found))


def _rule_based_summary(message: str, answer: str | None) -> Tuple[str, str]:
    message = message.strip()
    answer = (answer or "").strip()
    title = _first_sentence(message) or "گفتگوی پزشکی"

    symptoms = _collect_keywords(message, MEDICAL_KEYWORDS)
    durations = DURATION_PATTERN.findall(message)
    meds = MED_PATTERN.findall(message + " " + answer)

    lines = []
    if title:
        lines.append(f"- شکایت اصلی: {title}")
    if symptoms:
        lines.append(f"- علائم ذکر شده: {', '.join(dict.fromkeys(symptoms))}")
    if durations:
        lines.append(f"- مدت علائم: {', '.join(dict.fromkeys(durations))}")
    if meds:
        cleaned_meds = {redact_text(med).strip() for med in meds}
        lines.append(f"- دارو/مداخلات اشاره شده: {', '.join(sorted(cleaned_meds))}")

    if not lines:
        lines.append("- توضیح مشخصی ارائه نشد؛ لطفاً در مراجعه حضوری جزئیات بیشتری بیان کنید.")

    summary_text = "\n".join(lines)
    return title, summary_text


def _summarize_with_llm(message: str, answer: str | None) -> Tuple[str, str]:
    client = get_client()
    system_prompt = (
        "You produce very short Persian medical intake notes."
        " Respond in JSON with keys title, complaint, symptoms (list), duration, meds (list)."
    )
    truncated = (message or "")[: settings.SMART_STORAGE_MAX_TOKENS * 4]
    answer_snippet = (answer or "")[:400]
    user_blocks = [
        {"type": "input_text", "text": f"پیام کاربر:\n{truncated}"},
    ]
    if answer_snippet:
        user_blocks.append({"type": "input_text", "text": f"پاسخ فعلی:\n{answer_snippet}"})
    response = client.responses.create(
        model=settings.CHATBOT_DEFAULT_MODEL,
        input=[
            {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
            {"role": "user", "content": user_blocks},
        ],
        max_output_tokens=180,
        temperature=0,
    )
    text = getattr(response, "output_text", "")
    if isinstance(text, (list, tuple)):
        text = "".join(text)
    text = str(text).strip()
    data = {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return _rule_based_summary(message, answer)

    title = str(data.get("title") or data.get("complaint") or "گفتگوی پزشکی")
    lines = []
    complaint = data.get("complaint")
    if complaint:
        lines.append(f"- شکایت اصلی: {complaint}")
    symptoms = data.get("symptoms") or []
    if isinstance(symptoms, list) and symptoms:
        lines.append(f"- علائم ذکر شده: {', '.join(map(str, symptoms))}")
    duration = data.get("duration")
    if duration:
        lines.append(f"- مدت علائم: {duration}")
    meds = data.get("meds") or []
    if isinstance(meds, list) and meds:
        redacted = [redact_text(str(med)) for med in meds]
        lines.append(f"- دارو/مداخلات اشاره شده: {', '.join(redacted)}")
    if not lines:
        lines.append("- خلاصه مشخصی از مدل دریافت نشد.")
    return title, "\n".join(lines)


def make_note(message: str, answer: str | None) -> Tuple[str, str]:
    if settings.SMART_STORAGE_SUMMARIZE_WITH_LLM:
        try:
            title, summary = _summarize_with_llm(message, answer)
        except Exception:  # pragma: no cover - defensive guard
            title, summary = _rule_based_summary(message, answer)
    else:
        title, summary = _rule_based_summary(message, answer)

    title = redact_text(title).strip()[:200] or "گفتگوی پزشکی"
    summary = redact_text(summary).strip()
    if summary:
        summary = f"{summary}\n\n{DISCLAIMER}"
    else:
        summary = DISCLAIMER
    return title, summary


__all__ = ["make_note", "DISCLAIMER"]
