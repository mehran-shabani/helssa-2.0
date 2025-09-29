from __future__ import annotations

import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def _fake_celery(response):
    """
    یک شیء شبیه‌سازی‌شده از Celery با یک کنترل `ping` قابل پیکربندی ایجاد می‌کند.
    
    این شیء برای تست‌های واحد قابل استفاده است تا رفتار پاسخ‌دهی Celery (مثلاً `celery_app.control.ping`) را با مقدار مشخص شبیه‌سازی کند.
    
    Parameters:
        response: مقدار ثابتی که متد `control.ping` باید بازگرداند (مثلاً `[{"ok": True}]` یا `[]`).
    
    Returns:
        mock_celery: شیئی با صفت `control` که متد `ping(timeout: float = 1.0)` را دارد و همیشه مقدار `response` را بازمی‌گرداند.
    """
    class _Control:
        def ping(self, timeout: float = 1.0):
            """
            پاسخی ثابت شبیه به خروجی متد `control.ping` در Celery را بازمی‌گرداند.
            
            پارامترها:
                timeout (float): حداکثر زمان انتظار (ثابت گذاشته می‌شود اما در این شبیه‌ساز نادیده گرفته می‌شود).
            
            بازگشت:
                همان مقدار `response` که هنگام ساخت شبیه‌ساز تعیین شده است.
            """
            return response

    return type("Celery", (), {"control": _Control()})()


def _auth_client(user):
    """
    یک نمونهٔ APIClient احراز هویت‌شده با کاربر مشخص می‌سازد.
    
    این کمک‌تابع یک APIClient از DRF ایجاد می‌کند و آن را طوری پیکربندی می‌کند که تمام درخواست‌ها به‌عنوان کاربر داده‌شده اجرا شوند (مناسب برای تست‌های endpoint‌هایی که نیاز به کاربر خاص دارند).
    
    Parameters:
        user (django.contrib.auth.models.User): نمونهٔ کاربر دجانگو که درخواست‌ها باید به‌صورت آن کاربر اجرا شوند.
    
    Returns:
        APIClient: نمونهٔ DRF APIClient که احراز هویت آن برای کاربر داده‌شده برقرار شده است.
    """
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def test_system_health_public_headers():
    """
    بررسی می‌کند که نقطهٔ پایانی عمومی سلامت سیستم (/api/v1/system/health) پاسخ موفق و هدرهای عمومی را ارائه می‌دهد.
    
    انتظار می‌رود درخواست GET به این مسیر وضعیت HTTP 200 بازگرداند و بدنهٔ JSON شامل فیلد `status` با مقدار `"ok"` و فیلد `version` باشد. همچنین پاسخ باید هدرهای `X-Request-ID` و `X-Response-Time-ms` را داشته باشد.
    """
    response = APIClient().get("/api/v1/system/health")
    body = response.json()
    assert response.status_code == 200 and body["status"] == "ok"
    assert "version" in body and "X-Request-ID" in response
    assert "X-Response-Time-ms" in response


def test_system_ready_requires_staff(django_user_model):
    """
    بررسی می‌کند که دسترسی به endpoint /api/v1/system/ready محدود به کاربران با دسترسی staff یا superuser باشد.
    
    این تست رفتارهای زیر را اعتبارسنجی می‌کند:
    - درخواست بدون احراز هویت باید با کد وضعیت 401 یا 403 رد شود.
    - درخواست از طرف کاربری عادی (non-staff) پس از احراز هویت باید با کد وضعیت 403 رد شود.
    
    Parameters:
        django_user_model: فیکچر یا کلاس مدل کاربر Django برای ساخت کاربرهای تستی (مثلاً کاربر عادی).
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
    """
    وضعیت آماده‌به‌کار سیستم را براساس پاسخ شبیه‌سازی‌شده Celery اعتبارسنجی می‌کند.
    
    این تست با شبیه‌سازی پاسخ `celery_app`، یک کاربر سوپروزرایزر ایجاد می‌کند، درخواست GET به `/api/v1/system/ready` ارسال می‌کند و بررسی می‌کند که کد وضعیت HTTP و محتوای پاسخ (فیلد `status` و وجود فیلد `components`) مطابق مقدار مورد انتظار باشد.
    
    Parameters:
        celery_response (list): لیستی که خروجی مورد انتظار `control.ping` از سرویس Celery را شبیه‌سازی می‌کند (مثلاً `[{"ok": True}]` برای سالم بودن یا `[]` برای خطا).
        expected_status (int): کد وضعیت HTTP مورد انتظار از اندپوینت readiness (مثلاً `200` برای سالم یا `503` برای degradated).
    """
    monkeypatch.setattr("apps.system.views.celery_app", _fake_celery(celery_response))
    user = django_user_model.objects.create_superuser(
        username="admin", email="admin@example.com", password="pass"
    )
    response = _auth_client(user).get("/api/v1/system/ready")

    assert response.status_code == expected_status
    payload = response.json()
    assert payload["status"] == ("ok" if expected_status == 200 else "degraded")
    assert "components" in payload
