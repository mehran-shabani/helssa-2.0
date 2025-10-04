"""
Message builder utilities for constructing OpenAI Responses API payloads.

Provides functions to build text and vision inputs with medical safety prompts.
"""
from __future__ import annotations

from typing import Any

MEDICAL_SYSTEM_PROMPT = (
    "You are a careful medical information assistant. "
    "Never provide diagnosis, prescriptions, or treatments. "
    "Provide general educational info only and always advise consulting a doctor. "
    "If the user mentions an emergency, tell them to seek emergency help immediately."
)


def build_text_input(user_text: str, history: list[dict[str, str]]) -> list[dict[str, Any]]:
    """
    Build a text-only input payload for the Responses API.

    Args:
        user_text: The user's current message.
        history: List of previous messages with 'role' and 'content' keys.

    Returns:
        List of message dicts in Responses API format.
    """
    messages = [
        {
            "role": "system",
            "content": [{"type": "input_text", "text": MEDICAL_SYSTEM_PROMPT}],
        }
    ]

    # Add conversation history
    for msg in history:
        messages.append(
            {
                "role": msg["role"],
                "content": [{"type": "input_text", "text": msg["content"]}],
            }
        )

    # Add current user message
    messages.append(
        {
            "role": "user",
            "content": [{"type": "input_text", "text": user_text}],
        }
    )

    return messages


def build_vision_input(
    user_text: str, image_url_or_b64: str, history: list[dict[str, str]]
) -> list[dict[str, Any]]:
    """
    Build a vision input payload (text + image) for the Responses API.

    Args:
        user_text: The user's current message.
        image_url_or_b64: Image URL or base64 data URL.
        history: List of previous messages with 'role' and 'content' keys.

    Returns:
        List of message dicts in Responses API format.
    """
    messages = [
        {
            "role": "system",
            "content": [{"type": "input_text", "text": MEDICAL_SYSTEM_PROMPT}],
        }
    ]

    # Add conversation history
    for msg in history:
        messages.append(
            {
                "role": msg["role"],
                "content": [{"type": "input_text", "text": msg["content"]}],
            }
        )

    # Add current user message with image
    content_items = [
        {
            "type": "input_text",
            "text": user_text or "Describe this image for educational medical context only.",
        },
        {"type": "input_image", "image_url": image_url_or_b64},
    ]

    messages.append(
        {
            "role": "user",
            "content": content_items,
        }
    )

    return messages
