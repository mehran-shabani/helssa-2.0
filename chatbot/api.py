from __future__ import annotations

import base64
import hashlib
import json
from datetime import timedelta
from typing import Any, Callable, Dict, Iterator, Optional
from uuid import uuid4

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse, StreamingHttpResponse
from django.utils.encoding import force_str
from django.utils import timezone
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .models import Attachment, ChatConsent, ChatNote
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
from .services.policy import Decision, decide_storage
from .services.redact import redact_text, scrub_for_cache_key
from .services.router import select_model
from .services.summary import make_note


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
        storage_metadata: Optional[Dict[str, Any]] = None,
        consent_value: Optional[bool] = None,
        on_complete: Optional[Callable[[str], None]] = None,
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
                        if on_complete:
                            on_complete(final_answer)
                        payload = {
                            "done": True,
                            "answer": final_answer,
                            "usage": usage,
                            "model": model,
                            "disclaimer": DISCLAIMER,
                            "request_id": request_id,
                        }
                        if storage_metadata is not None:
                            payload["storage"] = storage_metadata
                        if consent_value is not None:
                            payload["consent"] = consent_value
                        yield _format_sse(payload)
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
        if on_complete:
            on_complete(final_answer)
        payload = {
            "done": True,
            "answer": final_answer,
            "usage": usage,
            "model": model,
            "disclaimer": DISCLAIMER,
            "request_id": request_id,
        }
        if storage_metadata is not None:
            payload["storage"] = storage_metadata
        if consent_value is not None:
            payload["consent"] = consent_value
        yield _format_sse(payload)

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
        store_pref: str | None = validated.get("store")
        consent_update = validated.get("consent")
        purge_requested: bool = bool(validated.get("purge", False))
        source_turn_id: str = validated.get("source_turn_id") or ""
        conversation_uuid = validated.get("conversation_id")

        smart_enabled = getattr(settings, "SMART_STORAGE_ENABLED", False)
        consent_scope = "medical_history"
        user_obj = request.user if getattr(request, "user", None) and request.user.is_authenticated else None
        active_consent = False
        purged_notes = 0

        if smart_enabled:
            consent_kwargs = {"user": user_obj, "scope": consent_scope}
            if consent_update is not None:
                ChatConsent.objects.update_or_create(
                    defaults={"granted": bool(consent_update)},
                    **consent_kwargs,
                )
            consent_record = ChatConsent.objects.filter(**consent_kwargs).first()
            if consent_record:
                active_consent = bool(consent_record.granted)
            elif not getattr(settings, "SMART_STORAGE_REQUIRE_CONSENT", True):
                active_consent = True

            if purge_requested and conversation_uuid:
                notes_qs = ChatNote.objects.filter(conversation_id=conversation_uuid)
                if request.user.is_staff:
                    pass
                elif user_obj:
                    notes_qs = notes_qs.filter(user=user_obj)
                else:
                    notes_qs = notes_qs.filter(user__isnull=True)
                purged_notes, _ = notes_qs.delete()

        user_content: list[dict[str, Any]] = [
            {"type": "input_text", "text": message},
        ]

        has_pdf_text = False
        pdf_text_total = 0
        for index, pdf in enumerate(pdfs, start=1):
            text = extract_text_from_pdf(pdf)
            if text:
                has_pdf_text = True
                pdf_text_total += len(text)
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

        attachments_present = bool(images or pdfs)
        decision: Decision | None = None
        if smart_enabled:
            decision = decide_storage(
                message=message,
                images=len(images),
                pdf_text_len=pdf_text_total,
                consent=active_consent,
                requested=store_pref,
                django_settings=settings,
            )

        cache_key = None
        cached_payload = None
        cache_status = "miss"
        if cache_ttl and not images and not pdfs:
            scrubbed = scrub_for_cache_key(message)
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

        storage_metadata: Optional[Dict[str, Any]] = None
        if smart_enabled and decision is not None:
            storage_metadata = {
                "mode": decision.mode,
                "tags": decision.tags,
                "reason": decision.reason,
            }
            if purge_requested:
                storage_metadata["purged"] = purged_notes

        def persist_storage(answer_text: str) -> None:
            nonlocal conversation_uuid, storage_metadata
            if not smart_enabled or decision is None or decision.mode == "none":
                return
            target_conversation = conversation_uuid or uuid4()
            conversation_uuid = target_conversation
            title, note_summary = make_note(message, answer_text)
            if decision.mode == "full":
                redacted_user = redact_text(message)
                redacted_answer = redact_text(answer_text)
                raw_block = f"```raw\nUser: {redacted_user}\nAssistant: {redacted_answer}\n```"
                note_summary = f"{note_summary}\n\n{raw_block}".strip()
            retention_days = getattr(settings, "SMART_STORAGE_TTL_DAYS", 30)
            retention_at = timezone.now() + timedelta(days=max(retention_days, 1))
            ChatNote.objects.create(
                conversation_id=target_conversation,
                user=user_obj,
                title=title,
                summary=note_summary,
                tags=decision.tags,
                source_turn_id=source_turn_id[:64],
                attachments_present=attachments_present,
                retention_at=retention_at,
            )
            max_turns = getattr(settings, "SMART_STORAGE_MAX_TURNS", 0)
            if max_turns and target_conversation:
                extra_ids = list(
                    ChatNote.objects.filter(
                        conversation_id=target_conversation,
                        user=user_obj,
                    )
                    .order_by("-created_at")
                    .values_list("id", flat=True)[max_turns:]
                )
                if extra_ids:
                    ChatNote.objects.filter(id__in=extra_ids).delete()
            if storage_metadata is not None:
                storage_metadata["mode"] = decision.mode
                storage_metadata["tags"] = decision.tags
                storage_metadata["reason"] = decision.reason
                storage_metadata["conversation_id"] = str(target_conversation)


        if stream:
            streaming_response = StreamingHttpResponse(
                self._collect_stream_events(
                    stream_obj=result,
                    mode=mode,
                    model=model,
                    request_id=request_id,
                    storage_metadata=storage_metadata,
                    consent_value=active_consent if smart_enabled else None,
                    on_complete=persist_storage,
                ),
                content_type="text/event-stream",
            )
            streaming_response["Cache-Control"] = "no-cache"
            streaming_response["X-Cache"] = "miss"
            return streaming_response

        answer_text = _extract_text_from_response(result)
        usage = _extract_usage(result)
        persist_storage(answer_text)
        payload = {
            "answer": answer_text,
            "model": getattr(result, "model", model),
            "usage": usage,
            "disclaimer": DISCLAIMER,
            "request_id": request_id,
        }

        if smart_enabled and storage_metadata is not None:
            payload["storage"] = storage_metadata
            payload["consent"] = active_consent

        if cache_key and cache_ttl:
            cache_status = "miss"
            cache_payload = payload.copy()
            cache_payload.pop("request_id", None)
            cache.set(cache_key, cache_payload, cache_ttl)

        response = JsonResponse(payload)
        response["X-Cache"] = cache_status
        return response


chatbot_ask_view = ChatbotAskView.as_view

