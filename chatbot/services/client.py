from __future__ import annotations

import threading
from typing import Any, Dict, List, Tuple

from django.conf import settings
from openai import (  # type: ignore
    APIConnectionError,
    APIError,
    APIStatusError,
    APITimeoutError,
    OpenAI,
)

_client: OpenAI | None = None
_lock = threading.Lock()


def get_client() -> OpenAI:
    global _client
    if _client is None:
        with _lock:
            if _client is None:
                kwargs: Dict[str, Any] = {
                    "api_key": settings.OPENAI_API_KEY or None,
                    "timeout": settings.CHATBOT_REQUEST_TIMEOUT,
                }
                if settings.OPENAI_BASE_URL:
                    kwargs["base_url"] = settings.OPENAI_BASE_URL
                if settings.OPENAI_ORG:
                    kwargs["organization"] = settings.OPENAI_ORG
                _client = OpenAI(**kwargs)
    return _client


def build_input_messages(*, system_prompt: str, user_content: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
        {"role": "user", "content": user_content},
    ]


def _convert_for_chat(user_content: List[dict[str, Any]]) -> List[dict[str, Any]]:
    converted: List[dict[str, Any]] = []
    for block in user_content:
        kind = block.get("type")
        if kind == "input_text":
            converted.append({"type": "text", "text": block.get("text", "")})
        elif kind == "input_image":
            image = block.get("image", {})
            data = image.get("data")
            media_type = image.get("media_type", "image/png")
            if data:
                converted.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{data}",
                        },
                    }
                )
    return converted


def invoke_response(
    *,
    system_prompt: str,
    user_content: list[dict[str, Any]],
    model: str,
    stream: bool,
    max_output_tokens: int,
    metadata: Dict[str, Any] | None = None,
) -> Tuple[str, Any]:
    client = get_client()
    payload = {
        "model": model,
        "input": build_input_messages(system_prompt=system_prompt, user_content=user_content),
        "max_output_tokens": max_output_tokens,
        "temperature": 0.2,
        "metadata": metadata or {},
    }
    try:
        if stream:
            return "responses", client.responses.stream(**payload)
        return "responses", client.responses.create(**payload)
    except AttributeError:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": _convert_for_chat(user_content)},
        ]
        chat_payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": max_output_tokens,
            "metadata": metadata or {},
        }
        if stream:
            return "chat", client.chat.completions.create(stream=True, **chat_payload)
        return "chat", client.chat.completions.create(**chat_payload)


__all__ = [
    "APIConnectionError",
    "APIError",
    "APIStatusError",
    "APITimeoutError",
    "get_client",
    "invoke_response",
]
