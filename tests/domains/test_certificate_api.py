import pytest
from rest_framework.test import APIClient
from certificate.models import Certificate

pytestmark = pytest.mark.django_db


def test_owner_sees_only_their_certificates(django_user_model):
    owner = django_user_model.objects.create_user(
        username="owner", email="owner@example.com", password="pass"
    )
    other = django_user_model.objects.create_user(
        username="other", email="other@example.com", password="pass"
    )
    owner_cert = Certificate.objects.create(owner=owner, title="Owner Cert")
    Certificate.objects.create(owner=other, title="Other Cert")

    client = APIClient()
    client.force_authenticate(user=owner)
    data = client.get("/api/v1/certificates/").json()["results"]
    assert {item["id"] for item in data} == {owner_cert.id}


def test_staff_sees_all_certificates(django_user_model):
    owner = django_user_model.objects.create_user(
        username="owner2", email="owner2@example.com", password="pass"
    )
    other = django_user_model.objects.create_user(
        username="other2", email="other2@example.com", password="pass"
    )
    cert_owner = Certificate.objects.create(owner=owner, title="Owner2 Cert")
    cert_other = Certificate.objects.create(owner=other, title="Other2 Cert")

    staff = django_user_model.objects.create_superuser(
        username="certadmin", email="certadmin@example.com", password="pass"
    )
    client = APIClient()
    client.force_authenticate(user=staff)
    data = client.get("/api/v1/certificates/").json()["results"]
    assert {item["id"] for item in data} == {cert_owner.id, cert_other.id}
