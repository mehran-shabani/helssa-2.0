import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def test_subscription_me_returns_zeros_for_new_user(django_user_model):
    user = django_user_model.objects.create_user(
        username="subscriber", email="subscriber@example.com", password="pass"
    )

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get("/api/v1/subscriptions/me")
    assert response.status_code == 200 and response.json() == {"tokens": 0, "balance": 0}
