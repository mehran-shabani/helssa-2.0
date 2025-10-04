from __future__ import annotations

import base64
import hashlib
import json
import re
from typing import Any, Dict, Iterator

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse, StreamingHttpResponse
from django.utils.encoding import force_str
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .models import Attachment
from .prompt_templates import DISCLAIMER, system_prompt
from .serializers import AskSerializer
from .services.client import (
    APIConnectionError,
    APIError,
    APIStatusError,
    APITimeoutError,
    invoke_response,
)
from .services.pdf import extract_text_from_pdf
from .services.router import select_model


def _scrub_for_cache_key(message: str) -> str:
    patterns = [
        re.compile(r"\b\d{10,16}\b"),  # possible phone/national numbers
        re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    ]
    scrubbed = message
    for pattern in patterns:
        scrubbed = pattern.sub("<redacted>", scrubbed)
    return scrubbed


def _format_sse(data: Dict[str, Any]) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _extract_text_from_response(response: Any) -> str:
    if response is None:
        return ""
    if hasattr(response, "output_text"):
        return force_str(getattr(response, "output_text"))
    output = getattr(response, "output", None)
    if output:
        parts: list[str] = []
        try:
            for item in output[0].content:  # type: ignore[index]
                text = getattr(item, "text", None)
                if text:
                    parts.append(force_str(text))
                elif isinstance(item, dict) and item.get("text"):
                    parts.append(force_str(item["text"]))
        except Exception:  # pragma: no cover - defensive
            pass
        if parts:
            return "".join(parts)
    choices = getattr(response, "choices", None)
    if choices:
        message = getattr(choices[0], "message", None)
        if message is None and isinstance(choices[0], dict):
            message = choices[0].get("message")
        if message is None:
            return ""
        content = getattr(message, "content", None)
        if isinstance(content, list):
            return "".join(part.get("text", "") for part in content if isinstance(part, dict))
        if isinstance(content, str):
            return content
        if isinstance(message, dict):
            return force_str(message.get("content", ""))
    return ""


def _extract_usage(response: Any) -> Dict[str, Any]:
    usage = getattr(response, "usage", None)
    if usage is None and isinstance(response, dict):
        usage = response.get("usage")
    if usage is None:
        return {}
    if isinstance(usage, dict):
        return {
            "input_tokens": usage.get("prompt_tokens")
            or usage.get("input_tokens")
            or usage.get("prompt"),
            "output_tokens": usage.get("completion_tokens")
            or usage.get("output_tokens")
            or usage.get("completion"),
            "total_tokens": usage.get("total_tokens"),
        }
    result: Dict[str, Any] = {}
    for key in ("input_tokens", "output_tokens", "total_tokens", "prompt_tokens", "completion_tokens"):
        if hasattr(usage, key):
            result[key] = getattr(usage, key)
    if "prompt_tokens" in result and "input_tokens" not in result:
        result["input_tokens"] = result.pop("prompt_tokens")
    if "completion_tokens" in result and "output_tokens" not in result:
        result["output_tokens"] = result.pop("completion_tokens")
    return result


class ChatbotAskView(APIView):
    parser_classes = (JSONParser, FormParser, MultiPartParser)
    permission_classes = (AllowAny,)

    def _get_request_id(self, request) -> str:
        return getattr(request, "request_id", "-")

    def _error(self, *, request, status: int, error: str, hint: str | None = None) -> JsonResponse:
        payload = {
            "error": error,
            "hint": hint or "",
            "request_id": self._get_request_id(request),
        }
        response = JsonResponse(payload, status=status)
        response["X-Cache"] = "miss"
        return response

    def _collect_stream_events(
        self,
        *,
        stream_obj: Any,
        mode: str,
        model: str,
        request_id: str,
    ) -> Iterator[str]:
        answer_parts: list[str] = []
        usage: Dict[str, Any] = {}

        def emit_delta(delta_text: str) -> Iterator[str]:
            if not delta_text:
                return
            answer_parts.append(delta_text)
            yield _format_sse({"delta": delta_text})

        if mode == "responses":
            with stream_obj as stream:
                for event in stream:
                    event_type = getattr(event, "type", None) or (
                        event.get("type") if isinstance(event, dict) else None
                    )
                    if event_type == "response.output_text.delta":
                        delta = getattr(event, "delta", None)
                        if delta is None and isinstance(event, dict):
                            delta = event.get("delta")
                        text = ""
                        if isinstance(delta, dict):
                            text = delta.get("text", "")
                        elif isinstance(delta, str):
                            text = delta
                        for chunk in emit_delta(text):
                            yield chunk
                    elif event_type == "response.completed":
                        response_obj = getattr(event, "response", None) or (
                            event.get("response") if isinstance(event, dict) else None
                        )
                        final_answer = _extract_text_from_response(response_obj)
                        usage = _extract_usage(response_obj)
                        if not final_answer:
                            final_answer = "".join(answer_parts)
                        yield _format_sse(
                            {
                                "done": True,
                                "answer": final_answer,
                                "usage": usage,
                                "model": model,
                                "disclaimer": DISCLAIMER,
                                "request_id": request_id,
                            }
                        )
                        return
                    elif event_type == "response.error":
                        error = getattr(event, "error", None) or (
                            event.get("error") if isinstance(event, dict) else {}
                        )
                        message = getattr(error, "message", None)
                        if isinstance(error, dict):
                            message = error.get("message")
                        yield _format_sse(
                            {
                                "done": True,
                                "error": "upstream_error",
                                "hint": message or "",
                                "request_id": request_id,
                            }
                        )
                        return
        else:  # chat completions fallback
            for chunk in stream_obj:
                choices = getattr(chunk, "choices", None)
                if choices is None and isinstance(chunk, dict):
                    choices = chunk.get("choices")
                if not choices:
                    continue
                choice = choices[0]
                finish_reason = getattr(choice, "finish_reason", None)
                if finish_reason is None and isinstance(choice, dict):
                    finish_reason = choice.get("finish_reason")
                delta = getattr(choice, "delta", None)
                if delta is None and isinstance(choice, dict):
                    delta = choice.get("delta")
                text = ""
                if isinstance(delta, dict):
                    content = delta.get("content")
                    if isinstance(content, list):
                        text = "".join(part.get("text", "") for part in content)
                    elif isinstance(content, str):
                        text = content
                    text = text or delta.get("content", "") or delta.get("text", "")
                elif hasattr(delta, "content"):
                    content = getattr(delta, "content")
                    if isinstance(content, list):
                        text = "".join(part.get("text", "") for part in content if isinstance(part, dict))
                    elif isinstance(content, str):
                        text = content
                for chunk_text in emit_delta(text):
                    yield chunk_text
                if finish_reason:
                    break

        final_answer = "".join(answer_parts)
        yield _format_sse(
            {
                "done": True,
                "answer": final_answer,
                "usage": usage,
                "model": model,
                "disclaimer": DISCLAIMER,
                "request_id": request_id,
            }
        )

    def post(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, "copy") else dict(request.data)
        if "stream" not in data and "stream" in request.query_params:
            data["stream"] = request.query_params.get("stream")
        serializer = AskSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        message: str = validated["message"]
        stream: bool = validated.get("stream") or (
            str(request.query_params.get("stream", "")).lower() in {"true", "1", "yes"}
        )
        requested_model: str | None = validated.get("model")
        images = validated.get("images", [])
        pdfs = validated.get("pdfs", [])
        cache_ttl = validated.get("cache_ttl")

        user_content: list[dict[str, Any]] = [
            {"type": "input_text", "text": message},
        ]

        has_pdf_text = False
        for index, pdf in enumerate(pdfs, start=1):
            text = extract_text_from_pdf(pdf)
            if text:
                has_pdf_text = True
                user_content.append(
                    {
                        "type": "input_text",
                        "text": f"[خلاصه فایل PDF {index}]\n{text}",
                    }
                )
            Attachment.maybe_persist(file_obj=pdf, kind=Attachment.KIND_PDF)

        for image in images:
            media_type = getattr(image, "content_type", "image/png")
            raw = image.read()
            encoded = base64.b64encode(raw).decode("utf-8")
            image.seek(0)
            user_content.append(
                {
                    "type": "input_image",
                    "image": {"data": encoded, "media_type": media_type},
                }
            )
            Attachment.maybe_persist(file_obj=image, kind=Attachment.KIND_IMAGE)

        model = select_model(
            requested_model=requested_model,
            has_images=bool(images),
            has_pdf_text=has_pdf_text,
        )

        cache_key = None
        cached_payload = None
        cache_status = "miss"
        if cache_ttl and not images and not pdfs:
            scrubbed = _scrub_for_cache_key(message)
            key_material = f"{model}|{scrubbed}"
            digest = hashlib.sha256(key_material.encode("utf-8")).hexdigest()
            cache_key = f"chatbot:{digest}"
        cached_payload = cache.get(cache_key)
        if cached_payload:
            payload = {
                **cached_payload,
                "request_id": self._get_request_id(request),
            }
            response = JsonResponse(payload)
            response["X-Cache"] = "hit"
            return response

        try:
            mode, result = invoke_response(
                system_prompt=system_prompt(),
                user_content=user_content,
                model=model,
                stream=stream,
                max_output_tokens=settings.CHATBOT_MAX_TOKENS,
                metadata={"source": "helssa-chatbot"},
            )
        except APITimeoutError as exc:
            return self._error(
                request=request,
                status=504,
                error="upstream_timeout",
                hint=str(exc),
            )
        except APIStatusError as exc:
            status_code = getattr(exc, "status_code", None)
            if status_code in {401, 403}:
                return self._error(
                    request=request,
                    status=502,
                    error="upstream_auth_error",
                    hint=str(exc),
                )
            if status_code and 400 <= status_code < 500:
                return self._error(
                    request=request,
                    status=400,
                    error="bad_request",
                    hint=str(exc),
                )
            return self._error(
                request=request,
                status=502,
                error="upstream_error",
                hint=str(exc),
            )
        except (APIConnectionError, APIError) as exc:
            return self._error(
                request=request,
                status=502,
                error="upstream_error",
                hint=str(exc),
            )

        request_id = self._get_request_id(request)

        if stream:
            streaming_response = StreamingHttpResponse(
                self._collect_stream_events(
                    stream_obj=result,
                    mode=mode,
                    model=model,
                    request_id=request_id,
                ),
                content_type="text/event-stream",
            )
            streaming_response["Cache-Control"] = "no-cache"
            streaming_response["X-Cache"] = "miss"
            return streaming_response

        answer_text = _extract_text_from_response(result)
        usage = _extract_usage(result)
        payload = {
            "answer": answer_text,
            "model": getattr(result, "model", model),
            "usage": usage,
            "disclaimer": DISCLAIMER,
            "request_id": request_id,
        }

        if cache_key and cache_ttl:
            cache_status = "miss"
            cache_payload = payload.copy()
            cache_payload.pop("request_id", None)
            cache.set(cache_key, cache_payload, cache_ttl)

        response = JsonResponse(payload)
        response["X-Cache"] = cache_status
        return response


chatbot_ask_view = ChatbotAskView.as_view

