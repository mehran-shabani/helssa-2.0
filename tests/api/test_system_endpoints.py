from __future__ import annotations

import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def _fake_celery(response):
    """
    ایجاد یک شیء شبیه‌سازی‌شده از Celery برای آزمایش که متد `control.ping` آن همیشه مقدار
    داده‌شده را برمی‌گرداند.
    
    Parameters:
        response: پاسخ ثابتی که متد `control.ping` باید بازگرداند (مثلاً `[{"ok": True}]` یا `[]`).
    
    Returns:
        mock_celery: شیء شبیه‌سازی‌شده‌ای با ویژگی `control` که متد `ping(timeout: float = 1.0)` را
        دارد و مقدار `response` را برمی‌گرداند.
    """
    class _Control:
        def ping(self, timeout: float = 1.0):
            return response

    return type("Celery", (), {"control": _Control()})()


def _auth_client(user):
    """
    یک نمونهٔ APIClient را ساخته و آن را به‌عنوان کاربر مشخص شده احراز هویت می‌کند.
    
    Parameters:
        user (django.contrib.auth.models.User): نمونهٔ کاربر دجانگو که درخواست‌ها باید
        به‌صورت آن کاربر اجرا شوند.
    
    Returns:
        APIClient: نمونهٔ DRF `APIClient` که با کاربر داده‌شده احراز هویت شده است.
    """
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
    """
    بررسی می‌کند که endpoint سلامت/آمادگی سیستم (/api/v1/system/ready) فقط برای کاربران دارای
    دسترسی سطح مدیر (staff/superuser) قابل دسترسی باشد.
    
    جزئیات:
    - درخواست بدون احراز هویت باید با کد وضعیت 401 یا 403 رد شود.
    - درخواست از طرف یک کاربر عادی (non-staff) پس از احراز هویت باید با کد وضعیت 403 رد شود.
    
    Parameters:
        django_user_model: فیکچر یا مدل کاربر Django که برای ایجاد کاربرهای آزمایشی (مثلاً کاربر
        عادی) استفاده می‌شود.
    """
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
