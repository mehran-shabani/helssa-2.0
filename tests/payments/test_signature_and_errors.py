import hmac
import json
from datetime import timedelta

import pytest
import requests
from django.conf import settings
from django.utils import timezone

from analytics.models import Event

pytestmark = pytest.mark.django_db


def _timeout():
    return requests.Timeout("timed out")


def _http_error(status):
    resp = requests.Response()
    resp.status_code = status
    err = requests.HTTPError(str(status))
    err.response = resp
    return err


def _webhook(client, payload, secret, *, sign=None, timestamp=None):
    body = json.dumps(payload)
    ts = str(timestamp or int(timezone.now().timestamp()))
    key = (sign or secret).encode()
    sig = hmac.new(key, body.encode() + ts.encode(), digestmod="sha256").hexdigest()
    return client.post(
        "/telemedicine/pay/webhook",
        data=body,
        content_type="application/json",
        HTTP_X_SIGNATURE=sig,
        HTTP_X_TIMESTAMP=ts,
    )


def test_signature_and_tat(client, monkeypatch):
    secret = "sig"
    monkeypatch.setenv("BITPAY_WEBHOOK_SECRET", secret)
    settings.BITPAY_WEBHOOK_SECRET = secret
    assert _webhook(client, {"id": "bad"}, secret, sign="other").status_code == 400
    assert Event.objects.filter(name="pay_webhook_bad_sig", props__reason="mismatch").exists()
    skew = settings.PAY_SIG_MAX_SKEW_SECONDS + 60
    old = int((timezone.now() - timedelta(seconds=skew)).timestamp())
    assert _webhook(client, {"id": "old"}, secret, timestamp=old).status_code == 400
    ok = _webhook(
        client,
        {
            "id": "evt",
            "status": "confirmed",
            "created_at": (timezone.now() - timedelta(minutes=5)).isoformat(),
            "success_at": timezone.now().isoformat(),
            "amount": {"value": "50.00", "currency": "USD"},
        },
        secret,
    )
    assert ok.status_code == 200
    tat = Event.objects.filter(name="pay_success", props__gateway="bitpay").last()
    assert tat and tat.props["tat_ms"] > 0

@pytest.mark.parametrize("factory, expected", [(_timeout, "timeout"), (lambda: _http_error(500), 500)])
def test_verify_errors_emit_ext_error(client, monkeypatch, factory, expected):
    exc = factory()
    def raiser(*_, **__):
        raise exc
    monkeypatch.setattr("telemedicine.views.verify_payment", raiser)
    resp = client.post(
        "/telemedicine/pay/verify",
        data=json.dumps({"transaction_id": "txn"}),
        content_type="application/json",
    )
    assert resp.status_code == 502
    event = Event.objects.filter(name="ext_error", props__op="verify").last()
    assert event and event.props["code"] == expected
