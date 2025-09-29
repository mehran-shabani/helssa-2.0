from __future__ import annotations

import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def _fake_celery(response):
    """
    یک شیء شبیه‌سازی‌شده از کلاینت Celery بازمی‌سازد که برای تست‌ها قابل استفاده است.
    
    Parameters:
        response: مقداری که متد کنترل `ping` باید بازگرداند (مثلاً یک لیست پاسخ یا مقدار خطا).
    
    Returns:
        fake_celery: نمونه‌ای شبیه به شیء Celery که دارای صفت `control` است؛ فراخوانی `fake_celery.control.ping(timeout=...)` مقدار `response` را برمی‌گرداند.
    """
    class _Control:
        def ping(self, timeout: float = 1.0):
            return response

    return type("Celery", (), {"control": _Control()})()


def _auth_client(user):
    """
    یک DRF APIClient تأیید هویت‌شده برای کاربر داده‌شده ایجاد می‌کند.
    
    Parameters:
        user: نمونه‌ی مدل کاربر دجانگو که کلاینت با آن احراز هویت خواهد شد.
    
    Returns:
        APIClient: نمونه‌ی APIClient که به‌طور اجباری برای کاربر داده‌شده احراز هویت شده است.
    """
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def test_system_health_public_headers():
    """
    آزمون وضعیت سلامت عمومی سرور و هدرهای مرتبط را بررسی می‌کند.
    
    این تست با یک کلاینت ناشناس درخواست GET به مسیر /api/v1/system/health می‌فرستد و موارد زیر را تأیید می‌کند: کد وضعیت HTTP برابر 200، مقدار فیلد `status` در بدنه پاسخ برابر "ok"، وجود فیلد `version` در بدنه، و وجود هدرهای `X-Request-ID` و `X-Response-Time-ms` در پاسخ.
    """
    response = APIClient().get("/api/v1/system/health")
    body = response.json()
    assert response.status_code == 200 and body["status"] == "ok"
    assert "version" in body and "X-Request-ID" in response
    assert "X-Response-Time-ms" in response


def test_system_ready_requires_staff(django_user_model):
    """
    این تست بررسی می‌کند که نقطهٔ آماده‌به‌کاری سیستم (/api/v1/system/ready) فقط برای کاربران دارای مجوز مدیریتی قابل دسترسی است.
    
    توضیحات:
    - درخواست بدون احراز هویت باید با کد وضعیت HTTP برابر 401 یا 403 پاسخ دهد.
    - درخواست با کاربر عادی (بدون دسترسی staff/superuser) باید با کد وضعیت HTTP 403 پاسخ دهد.
    
    Parameters:
        django_user_model: فیکسچر مدل کاربر Django که برای ساخت یک کاربر عادی استفاده می‌شود.
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
    آزمونی پارامترایز شده که وضعیت endpoint آماده‌باش سیستم را هنگام پاسخ‌های مختلف Celery بررسی می‌کند.
    
    شرح:
    این تست یک شیء Celery جعلی با پاسخ مشخص تنظیم می‌کند، یک کاربر ابرکاربر (superuser) ایجاد و با آن درخواست GET به /api/v1/system/ready ارسال می‌کند و سپس صحت کد وضعیت HTTP و ساختار بار پاسخ را بررسی می‌کند.
    
    Parameters:
        monkeypatch: ابزار pytest برای جایگزینی ویژگی‌ها در زمان اجرا.
        django_user_model: مدل کاربر Django برای ایجاد ابرکاربر تستی.
        celery_response (list|dict): مقدار بازگشتی شبیه‌سازی‌شده از `celery.control.ping()` که نشان‌دهنده وضعیت سرویس‌های صف‌کاری است.
        expected_status (int): کد وضعیت HTTP مورد انتظار از endpoint؛ معمولاً `200` برای وضعیت کامل و مقدار دیگر (مثلاً `503`) برای حالت کاهش‌یافته.
    
    Assertions:
        - کد وضعیت پاسخ با `expected_status` مطابقت دارد.
        - فیلد `status` در بار پاسخ `ok` اگر `expected_status == 200` و در غیر این صورت `degraded` است.
        - فیلد `components` در بار پاسخ وجود دارد.
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
