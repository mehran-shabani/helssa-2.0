import hmac
import json
import time
from datetime import timedelta

import pytest
from django.conf import settings
from django.utils import timezone

from analytics.models import Event
from telemedicine.models import IdempotencyKey

pytestmark = pytest.mark.django_db


def test_idempotency_for_webhook_and_verify(client, monkeypatch):
    secret = "sig"
    monkeypatch.setenv("BITPAY_WEBHOOK_SECRET", secret)
    settings.BITPAY_WEBHOOK_SECRET = secret
    payload = json.dumps({
        "id": "evt-1",
        "status": "confirmed",
        "created_at": (timezone.now() - timedelta(minutes=5)).isoformat(),
        "success_at": timezone.now().isoformat(),
    })
    ts = str(int(time.time()))
    sig = hmac.new(
        secret.encode(), payload.encode() + b"|" + ts.encode(), digestmod="sha256"
    ).hexdigest()
    for _ in range(2):
        assert (
            client.post(
                "/telemedicine/pay/webhook",
                data=payload,
                content_type="application/json",
                HTTP_X_SIGNATURE=sig,
                HTTP_X_TIMESTAMP=ts,
            ).status_code
            == 200
        )
    assert Event.objects.filter(name="pay_webhook_duplicate", props__scope="webhook").exists()
    assert IdempotencyKey.objects.filter(key__startswith="webhook:bitpay:").count() == 1

    monkeypatch.setattr(
        "telemedicine.views.verify_payment",
        lambda *a, **k: {"status": "confirmed", "created_at": timezone.now().isoformat()},
    )
    body = json.dumps({"transaction_id": "txn-1"})
    first = client.post("/telemedicine/pay/verify", data=body, content_type="application/json")
    second = client.post("/telemedicine/pay/verify", data=body, content_type="application/json")
    assert first.status_code == second.status_code == 200 and second.json() == first.json()
    assert Event.objects.filter(name="pay_webhook_duplicate", props__scope="verify").exists()
    assert IdempotencyKey.objects.filter(key__startswith="verify:bitpay:").count() == 1
