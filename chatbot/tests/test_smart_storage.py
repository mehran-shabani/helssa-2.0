from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from django.core.cache import cache
from django.urls import reverse
from rest_framework.test import APIClient

from chatbot.models import ChatNote
from chatbot.services.summary import DISCLAIMER


@pytest.fixture(autouse=True)
def clear_cache_and_notes():
    cache.clear()
    ChatNote.objects.all().delete()
    yield
    cache.clear()
    ChatNote.objects.all().delete()


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture(autouse=True)
def stub_invoke(monkeypatch):
    def fake_invoke(**kwargs):
        return "responses", SimpleNamespace(
            output_text="پاسخ پزشکی نمونه",
            model=kwargs.get("model", "stub-model"),
            usage={"input_tokens": 5, "output_tokens": 12},
        )

    monkeypatch.setattr("chatbot.api.invoke_response", fake_invoke)


def enable_smart_storage(settings):
    settings.SMART_STORAGE_ENABLED = True
    settings.SMART_STORAGE_REQUIRE_CONSENT = True
    settings.SMART_STORAGE_DEFAULT_MODE = "summary"
    settings.SMART_STORAGE_CLASSIFY_WITH_LLM = False
    settings.SMART_STORAGE_SUMMARIZE_WITH_LLM = False
    settings.CHATBOT_DEFAULT_MODEL = "test-model"
    settings.CHATBOT_ALLOWED_MODELS = {"test-model"}


@pytest.mark.django_db
def test_no_consent_requires_skip_storage(api_client, settings):
    enable_smart_storage(settings)
    conversation_id = uuid4()

    url = reverse("chatbot-ask")
    response = api_client.post(
        url,
        {
            "message": "سرفه و تب دارم",
            "conversation_id": str(conversation_id),
        },
        format="json",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["storage"]["mode"] == "none"
    assert data["storage"]["reason"] == "consent_required"
    assert data["consent"] is False
    assert ChatNote.objects.count() == 0


@pytest.mark.django_db
def test_consent_medical_summary_persisted(api_client, settings):
    enable_smart_storage(settings)
    conversation_id = uuid4()

    url = reverse("chatbot-ask")
    response = api_client.post(
        url,
        {
            "message": "سرفه خشک دو هفته است",
            "conversation_id": str(conversation_id),
            "consent": True,
        },
        format="json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["storage"]["mode"] == "summary"
    assert payload["consent"] is True
    note = ChatNote.objects.get()
    assert str(note.conversation_id) == payload["storage"]["conversation_id"]
    assert note.tags.get("medical_relevant") is True
    assert DISCLAIMER in note.summary
    assert not note.attachments_present


@pytest.mark.django_db
def test_critical_keyword_full_storage_with_redaction(api_client, settings):
    enable_smart_storage(settings)
    conversation_id = uuid4()

    url = reverse("chatbot-ask")
    response = api_client.post(
        url,
        {
            "message": "درد قفسه سینه دارم و شماره 09123456789",
            "conversation_id": str(conversation_id),
            "consent": True,
        },
        format="json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["storage"]["mode"] == "full"
    note = ChatNote.objects.get()
    assert "```raw" in note.summary
    assert "<phone>" in note.summary
    assert "09123456789" not in note.summary


@pytest.mark.django_db
def test_admin_smalltalk_not_persisted(api_client, settings):
    enable_smart_storage(settings)
    conversation_id = uuid4()

    response = api_client.post(
        reverse("chatbot-ask"),
        {
            "message": "سلام پیگیری پرداخت فاکتور است",
            "conversation_id": str(conversation_id),
            "consent": True,
        },
        format="json",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["storage"]["mode"] == "none"
    assert ChatNote.objects.count() == 0


@pytest.mark.django_db
def test_purge_existing_notes(api_client, settings):
    enable_smart_storage(settings)
    conversation_id = uuid4()

    first = api_client.post(
        reverse("chatbot-ask"),
        {
            "message": "تب سه روزه",
            "conversation_id": str(conversation_id),
            "consent": True,
        },
        format="json",
    )
    assert first.status_code == 200
    assert ChatNote.objects.filter(conversation_id=conversation_id).count() == 1

    second = api_client.post(
        reverse("chatbot-ask"),
        {
            "message": "سلام",
            "conversation_id": str(conversation_id),
            "purge": True,
            "store": "none",
            "consent": True,
        },
        format="json",
    )
    assert second.status_code == 200
    data = second.json()
    assert data["storage"]["mode"] == "none"
    assert data["storage"].get("purged") == 1
    assert ChatNote.objects.filter(conversation_id=conversation_id).count() == 0


@pytest.mark.django_db
def test_llm_classification_and_summary_called(api_client, monkeypatch, settings):
    enable_smart_storage(settings)
    settings.SMART_STORAGE_CLASSIFY_WITH_LLM = True
    settings.SMART_STORAGE_SUMMARIZE_WITH_LLM = True

    classify_called = {"count": 0}
    summary_called = {"count": 0}

    def fake_classify(message):
        classify_called["count"] += 1
        return {"medical_relevant": True, "critical": False, "admin": False, "smalltalk": False}

    def fake_summary(message, answer):
        summary_called["count"] += 1
        return "عنوان", "- شکایت اصلی: تست"

    monkeypatch.setattr("chatbot.services.triage.classify_with_llm", fake_classify)
    monkeypatch.setattr("chatbot.services.summary._summarize_with_llm", fake_summary)

    response = api_client.post(
        reverse("chatbot-ask"),
        {
            "message": "گلودرد",
            "conversation_id": str(uuid4()),
            "consent": True,
        },
        format="json",
    )

    assert response.status_code == 200
    assert classify_called["count"] == 1
    assert summary_called["count"] == 1
    assert ChatNote.objects.count() == 1
