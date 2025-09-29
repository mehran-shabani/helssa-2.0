from __future__ import annotations

from datetime import date

import pytest
from rest_framework.test import APIClient

from analytics.models import Event, StatsDaily

pytestmark = pytest.mark.django_db


def test_daily_stats_requires_staff_and_filters(django_user_model):
    """
    دسترسی و فیلترینگ نقطه‌پایان آمار روزانه را آزمایش می‌کند.
    
    این تست اطمینان می‌دهد که درخواست به /api/v1/analytics/daily/ برای کاربر ناشناس مجاز نیست، سپس با یک سوپریوزر احراز هویت انجام می‌دهد، دو رکورد StatsDaily برای روزهای مختلف ایجاد می‌کند و با پارامترهای from/to روی یک روز مشخص درخواست می‌فرستد؛ انتظار برگرداندن دقیقاً یک رکورد فیلترشده است که مقدار `pay_success` آن برابر 3 باشد.
    
    Parameters:
        django_user_model: فیکسچر pytest که مدل کاربر را فراهم می‌کند و برای ایجاد سوپریوزر استفاده می‌شود.
    """
    client = APIClient()
    assert client.get("/api/v1/analytics/daily/").status_code in {401, 403}

    user = django_user_model.objects.create_superuser(
        username="staff", email="staff@example.com", password="pass"
    )
    client.force_authenticate(user=user)

    StatsDaily.objects.create(day=date(2025, 9, 25), pay_success=1)
    StatsDaily.objects.create(day=date(2025, 9, 26), pay_success=3)

    response = client.get("/api/v1/analytics/daily/?from=2025-09-26&to=2025-09-26")
    payload = response.json()
    assert response.status_code == 200
    assert payload["count"] == 1
    assert payload["results"][0]["pay_success"] == 3


def test_events_filter_and_limit(django_user_model):
    """
    این تست صحت فیلتر کردن نتایج بر اساس نام و محدودسازی تعداد بازگشتی در endpoint رویدادها را بررسی می‌کند.
    
    توضیحات:
    تست یک کاربر سوپر‌یوزر ایجاد و با آن کلاینت را احراز هویت می‌کند، چند رویداد با همین نام تولید می‌کند، سپس با پارامترهای query شامل `name=pay_success` و `limit=3` به مسیر `/api/v1/analytics/events/` درخواست می‌زند و انتظار دارد که پاسخ موفق باشد، دقیقاً سه مورد در فیلد `results` بازگردد و همهٔ آیتم‌های بازگشتی نام `pay_success` داشته باشند.
    
    Parameters:
        django_user_model: فیکسچر مدل کاربر برای ایجاد یک سوپر‌یوزر جهت احراز هویت درخواست‌ها.
    """
    user = django_user_model.objects.create_superuser(
        username="staff2", email="staff2@example.com", password="pass"
    )
    client = APIClient()
    client.force_authenticate(user=user)

    for idx in range(5):
        Event.objects.create(name="pay_success", props={"idx": idx})

    response = client.get("/api/v1/analytics/events/?name=pay_success&limit=3")
    payload = response.json()
    assert response.status_code == 200
    assert len(payload["results"]) == 3
    assert all(item["name"] == "pay_success" for item in payload["results"])
