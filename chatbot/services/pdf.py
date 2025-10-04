from __future__ import annotations

from typing import IO

from django.conf import settings
from pypdf import PdfReader


def extract_text_from_pdf(
    file_obj: IO[bytes],
    *,
    max_pages: int | None = None,
    max_chars: int | None = None,
) -> str:
    max_pages = max_pages or settings.CHATBOT_PDF_MAX_PAGES
    max_chars = max_chars or settings.CHATBOT_PDF_MAX_CHARS

    file_obj.seek(0)
    reader = PdfReader(file_obj)
    pieces: list[str] = []
    for idx, page in enumerate(reader.pages):
        if idx >= max_pages:
            break
        text = page.extract_text() or ""
        if text:
            pieces.append(text.strip())
    file_obj.seek(0)
    combined = "\n\n".join(filter(None, pieces))
    if len(combined) > max_chars:
        return combined[:max_chars]
    return combined


__all__ = ["extract_text_from_pdf"]
