from __future__ import annotations

from types import SimpleNamespace

import pytest
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient

from chatbot.prompt_templates import DISCLAIMER


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


def build_response(answer: str, model: str = "test-model"):
    return SimpleNamespace(output_text=answer, model=model, usage={"input_tokens": 5, "output_tokens": 10})


@pytest.mark.django_db
def test_chatbot_json_request_returns_answer(api_client, monkeypatch, settings):
    settings.CHATBOT_DEFAULT_MODEL = "json-model"
    settings.CHATBOT_ALLOWED_MODELS = {"json-model"}

    calls = {}

    def fake_invoke(**kwargs):
        calls["model"] = kwargs["model"]
        return "responses", build_response("این یک پاسخ آزمایشی است.", model=kwargs["model"])

    monkeypatch.setattr("chatbot.api.invoke_response", fake_invoke)

    url = reverse("chatbot-ask")
    response = api_client.post(url, {"message": "سلام"}, format="json")

    assert response.status_code == 200
    data = response.json()
    assert data["answer"].startswith("این یک پاسخ")
    assert data["model"] == "json-model"
    assert data["disclaimer"] == DISCLAIMER
    assert calls["model"] == "json-model"


@pytest.mark.django_db
def test_chatbot_multipart_with_files(api_client, monkeypatch, settings):
    settings.CHATBOT_DEFAULT_MODEL = "default"
    settings.CHATBOT_REASONING_MODEL = "reason"
    settings.CHATBOT_VISION_MODEL = "vision"
    settings.CHATBOT_ALLOWED_MODELS = {"default", "reason", "vision"}

    pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    pdf_file = SimpleUploadedFile("report.pdf", pdf_bytes, content_type="application/pdf")
    image_file = SimpleUploadedFile("scan.png", b"\x89PNG\r\n", content_type="image/png")

    monkeypatch.setattr("chatbot.api.extract_text_from_pdf", lambda *_: "خلاصه PDF آزمایشی")

    captured = {}

    def fake_invoke(**kwargs):
        captured["model"] = kwargs["model"]
        captured["content"] = kwargs["user_content"]
        return "responses", build_response("پاسخ برای فایل ها", model=kwargs["model"])

    monkeypatch.setattr("chatbot.api.invoke_response", fake_invoke)

    url = reverse("chatbot-ask")
    response = api_client.post(
        url,
        {
            "message": "لطفاً تحلیل کن",
            "pdfs": [pdf_file],
            "images": [image_file],
        },
        format="multipart",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "vision"  # vision takes precedence when images provided
    assert captured["model"] == "vision"
    user_content = captured["content"]
    assert any(block.get("type") == "input_image" for block in user_content)
    assert any("خلاصه PDF" in block.get("text", "") for block in user_content if block.get("type") == "input_text")


@pytest.mark.django_db
def test_chatbot_cache_hit(api_client, monkeypatch, settings):
    settings.CHATBOT_DEFAULT_MODEL = "cache-model"
    settings.CHATBOT_ALLOWED_MODELS = {"cache-model"}

    call_counter = {"count": 0}

    def fake_invoke(**kwargs):
        call_counter["count"] += 1
        return "responses", build_response("پاسخ کش شده", model=kwargs["model"])

    monkeypatch.setattr("chatbot.api.invoke_response", fake_invoke)

    url = reverse("chatbot-ask")
    resp1 = api_client.post(url, {"message": "سلام", "cache_ttl": 30}, format="json")
    assert resp1.status_code == 200
    assert resp1["X-Cache"] == "miss"
    assert call_counter["count"] == 1

    resp2 = api_client.post(url, {"message": "سلام", "cache_ttl": 30}, format="json")
    assert resp2.status_code == 200
    assert resp2["X-Cache"] == "hit"
    assert call_counter["count"] == 1


@pytest.mark.django_db
def test_chatbot_model_override_not_allowed(api_client, monkeypatch, settings):
    settings.CHATBOT_DEFAULT_MODEL = "safe-default"
    settings.CHATBOT_ALLOWED_MODELS = {"safe-default"}

    observed = {}

    def fake_invoke(**kwargs):
        observed["model"] = kwargs["model"]
        return "responses", build_response("", model=kwargs["model"])

    monkeypatch.setattr("chatbot.api.invoke_response", fake_invoke)

    url = reverse("chatbot-ask")
    response = api_client.post(url, {"message": "hello", "model": "unauthorized"}, format="json")
    assert response.status_code == 200
    assert observed["model"] == "safe-default"


class DummyStream:
    def __init__(self, events):
        self._events = events

    def __enter__(self):
        return iter(self._events)

    def __exit__(self, exc_type, exc, tb):
        return False


@pytest.mark.django_db
def test_chatbot_streaming_sse(api_client, monkeypatch, settings):
    settings.CHATBOT_DEFAULT_MODEL = "stream-model"
    settings.CHATBOT_ALLOWED_MODELS = {"stream-model"}

    events = [
        SimpleNamespace(type="response.output_text.delta", delta={"text": "در"}),
        SimpleNamespace(type="response.output_text.delta", delta={"text": "مان"}),
        SimpleNamespace(
            type="response.completed",
            response=SimpleNamespace(output_text="درمان", usage={"input_tokens": 2, "output_tokens": 3}),
        ),
    ]

    def fake_invoke(**kwargs):
        return "responses", DummyStream(events)

    monkeypatch.setattr("chatbot.api.invoke_response", fake_invoke)

    url = reverse("chatbot-ask") + "?stream=true"
    response = api_client.post(url, {"message": "درمان"}, format="json")

    assert response.status_code == 200
    assert response["Content-Type"] == "text/event-stream"
    chunks = b"".join(part if isinstance(part, bytes) else part.encode("utf-8") for part in response.streaming_content)
    payloads = [line for line in chunks.decode("utf-8").split("\n\n") if line]
    assert payloads[0].startswith("data: {\"delta\": \"در\"}")
    assert "\"done\": true" in payloads[-1]
    assert "درمان" in payloads[-1]

