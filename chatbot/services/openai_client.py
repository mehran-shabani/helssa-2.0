"""
OpenAI client service using the Responses API (v1+).

This module provides functions to interact with OpenAI's
Responses API with streaming support.
"""
from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator

from django.conf import settings
from openai import OpenAI

_client: OpenAI | None = None


def get_client() -> OpenAI:
    """Get or create a singleton OpenAI client instance."""
    global _client
    if _client:
        return _client

    kwargs: dict[str, Any] = {}
    if settings.OPENAI_API_KEY:
        kwargs["api_key"] = settings.OPENAI_API_KEY
    if settings.OPENAI_BASE_URL:
        kwargs["base_url"] = settings.OPENAI_BASE_URL

    _client = OpenAI(**kwargs)
    return _client


async def stream_response(
    model: str, input_payload: list[dict], **kwargs
) -> AsyncIterator[str]:
    """
    Stream response from OpenAI using the Responses API.

    Args:
        model: The OpenAI model to use (e.g., gpt-4o-mini, o1).
        input_payload: List of message dictionaries in Responses API format.
        **kwargs: Additional parameters (e.g., temperature, timeout).

    Yields:
        Text deltas from the streaming response.
    """
    client = get_client()

    # Run streaming in a thread pool to avoid blocking
    def _stream():
        chunks = []
        with client.responses.stream(model=model, input=input_payload, **kwargs) as stream:
            for event in stream:
                if event.type == "response.output_text.delta":
                    chunks.append(event.delta)
            stream.close()
        return chunks

    chunks = await asyncio.to_thread(_stream)
    for chunk in chunks:
        yield chunk


async def summarize_conversation(messages: list[dict[str, str]]) -> str:
    """
    Summarize a conversation to reduce token usage.

    Args:
        messages: List of message dicts with 'role' and 'content' keys.

    Returns:
        Summary text.
    """
    client = get_client()

    # Build a simple summarization prompt
    conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
    summary_prompt = [
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": f"Summarize this medical conversation concisely:\n\n{conversation_text}",
                }
            ],
        }
    ]

    def _get_summary():
        response = client.responses.create(
            model=settings.OPENAI_DEFAULT_MODEL,
            input=summary_prompt,
            temperature=0.3,
        )
        # Extract the text content from response
        if hasattr(response, "output") and response.output:
            for item in response.output:
                if item.type == "text":
                    return item.text
        return "Summary not available."

    return await asyncio.to_thread(_get_summary)
