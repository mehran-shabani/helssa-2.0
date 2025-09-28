import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_health_endpoint(client):
    url = reverse("health")
    response = client.get(url)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "X-Request-ID" in response
    assert "X-Response-Time-ms" in response
