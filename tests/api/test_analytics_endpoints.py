from __future__ import annotations

from datetime import date

import pytest
from rest_framework.test import APIClient

from analytics.models import Event, StatsDaily

pytestmark = pytest.mark.django_db


def test_daily_stats_requires_staff_and_filters(django_user_model):
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
    قابلیت فیلتر بر اساس نام و محدودسازی تعداد نتایج در endpoint رویدادها را تست می‌کند.
    
    این تست یک کاربر سوپر‌یوزر ایجاد و با آن احراز هویت می‌کند، پنج رویداد با نام "pay_success" و پراپرتی‌های متفاوت می‌سازد، سپس درخواست به /api/v1/analytics/events/ با پارامترهای نام و limit ارسال می‌کند و بررسی می‌کند که پاسخ با کد 200 بازگردد، تعداد نتایج حداکثر برابر با مقدار limit باشد و همهٔ آیتم‌های بازگشتی نام "pay_success" داشته باشند.
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
    assert len(payload["results"]) <= 3
    assert all(item["name"] == "pay_success" for item in payload["results"])
