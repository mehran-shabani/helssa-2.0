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
    assert response.status_code == 200 and response.json()["results"]


def test_visits_reject_non_staff(django_user_model):
    user = django_user_model.objects.create_user(
        username="regular", email="regular@example.com", password="pass"
    )
    anonymous_response = APIClient().get("/api/v1/doctor/visits/")
    assert anonymous_response.status_code in {401, 403}

    client = APIClient()
    client.force_authenticate(user=user)
    assert client.get("/api/v1/doctor/visits/").status_code == 403
