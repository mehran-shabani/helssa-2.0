import pytest
from django.http import HttpResponse
from django.test import RequestFactory

from core.middleware.request_id import RequestIDMiddleware

pytestmark = pytest.mark.django_db


def get_response(request):
    return HttpResponse("ok")


def test_request_id_preserved():
    middleware = RequestIDMiddleware(get_response)
    factory = RequestFactory()
    request = factory.get("/ping", HTTP_X_REQUEST_ID="abc123")
    response = middleware(request)
    assert response["X-Request-ID"] == "abc123"


def test_request_id_generated():
    middleware = RequestIDMiddleware(get_response)
    factory = RequestFactory()
    request = factory.get("/ping")
    response = middleware(request)
    assert response["X-Request-ID"]
    assert int(response["X-Response-Time-ms"]) >= 0
