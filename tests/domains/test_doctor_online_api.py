from __future__ import annotations

import pytest
from rest_framework.test import APIClient
from doctor_online.models import Visit

pytestmark = pytest.mark.django_db


def test_staff_can_list_visits(django_user_model):
    staff = django_user_model.objects.create_superuser(
        username="docadmin", email="docadmin@example.com", password="pass"
    )
    Visit.objects.create(user=staff, note="Follow-up")

    client = APIClient()
    client.force_authenticate(user=staff)
    response = client.get("/api/v1/doctor/visits/")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["results"][0]["note"] == "Follow-up"


def test_visits_reject_non_staff(django_user_model):
    """
    بررسی می‌کند که دسترسی به نقطهٔ انتهایی "/api/v1/doctor/visits/" برای کاربران غیرپرسنل مسدود باشد.
    
    آزمایش یک کاربر عادی ایجاد می‌کند، سپس:
    - درخواست ناشناس به "/api/v1/doctor/visits/" باید وضعیت 401 یا 403 برگرداند.
    - درخواست احرازشده با کاربر غیرپرسنل باید وضعیت 403 برگرداند.
    """
    user = django_user_model.objects.create_user(
        username="regular", email="regular@example.com", password="pass"
    )
    anonymous_response = APIClient().get("/api/v1/doctor/visits/")
    assert anonymous_response.status_code == 401

    client = APIClient()
    client.force_authenticate(user=user)
    assert client.get("/api/v1/doctor/visits/").status_code == 403