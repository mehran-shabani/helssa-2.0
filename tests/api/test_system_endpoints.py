from __future__ import annotations

import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def _fake_celery(response):
    class _Control:
        def ping(self, timeout: float = 1.0):
            return response

    return type("Celery", (), {"control": _Control()})()


def _auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def test_system_health_public_headers():
    response = APIClient().get("/api/v1/system/health")
    body = response.json()
    assert response.status_code == 200 and body["status"] == "ok"
    assert "version" in body and "X-Request-ID" in response
    assert "X-Response-Time-ms" in response


def test_system_ready_requires_staff(django_user_model):
    client = APIClient()
    assert client.get("/api/v1/system/ready").status_code in {401, 403}

    user = django_user_model.objects.create_user(
        username="regular", email="regular@example.com", password="pass"
    )
    client.force_authenticate(user=user)
    assert client.get("/api/v1/system/ready").status_code == 403


@pytest.mark.parametrize(
    "celery_response, expected_status",
    [([{"ok": True}], 200), ([], 503)],
)
def test_system_ready_status(monkeypatch, django_user_model, celery_response, expected_status):
    monkeypatch.setattr("apps.system.views.celery_app", _fake_celery(celery_response))
    user = django_user_model.objects.create_superuser(
        username="admin", email="admin@example.com", password="pass"
    )
    response = _auth_client(user).get("/api/v1/system/ready")

    assert response.status_code == expected_status
    payload = response.json()
    assert payload["status"] == ("ok" if expected_status == 200 else "degraded")
    assert "components" in payload
