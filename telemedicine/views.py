from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Dict

from django.conf import settings
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from analytics.models import Event

from .gateway.bitpay import verify_payment
from .gateway.signature import verify_signature
from .models import IdempotencyKey

logger = logging.getLogger(__name__)
SUCCESS = {"status": "ok"}
ERROR = {"status": "error", "code": "gateway_unavailable"}
SUCCESS_STATUSES = {"confirmed", "completed", "success", "paid", "settled"}


def _emit(name: str, **props: Any) -> None:
    try:
        Event.objects.create(name=name, props=props)
    except Exception:  # pragma: no cover
        logger.exception("analytics_event_failed", extra={"name": name})


def _idem_key(prefix: str, token: str | None, raw: bytes) -> str:
    return f"{prefix}:{settings.PAYMENT_GATEWAY}:{token or hashlib.sha256(raw).hexdigest()}"


def _register_key(key: str) -> bool:
    try:
        with transaction.atomic():
            _, created = IdempotencyKey.objects.get_or_create(key=key)
            return created
    except IntegrityError:
        return False


def _acquire(prefix: str, token: str | None, request: HttpRequest, scope: str):
    key = _idem_key(prefix, token, request.body)
    cache_key = f"idem:{key}"
    if not _register_key(key):
        _emit("pay_webhook_duplicate", key=key, scope=scope)
        return False, key, cache.get(cache_key), cache_key
    return True, key, None, cache_key


def _parse_dt(raw: Any) -> datetime | None:
    if not raw and raw != 0:
        return None
    if isinstance(raw, datetime):
        return raw if timezone.is_aware(raw) else timezone.make_aware(raw, timezone.utc)
    if isinstance(raw, (int, float)):
        return datetime.fromtimestamp(float(raw), tz=timezone.utc)
    dt = parse_datetime(str(raw))
    if dt:
        return dt if timezone.is_aware(dt) else timezone.make_aware(dt, timezone.utc)
    return None


def _emit_success(payload: Dict[str, Any], source: str) -> None:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    status = str(data.get("status") or payload.get("status") or "").lower()
    if status not in SUCCESS_STATUSES:
        return
    created = _parse_dt(data.get("created_at") or payload.get("created_at") or data.get("invoice_created_at"))
    finished = _parse_dt(
        data.get("success_at") or data.get("confirmed_at") or data.get("paid_at") or payload.get("confirmed_at")
    ) or timezone.now()
    created = created or finished
    if not created:
        return
    amount = data.get("amount") or data.get("price") or data.get("total")
    currency = data.get("currency") or data.get("price_currency") or data.get("currency_code")
    if isinstance(amount, dict):
        currency = amount.get("currency") or currency
        amount = amount.get("value") or amount.get("amount")
    tat_ms = max(int((finished - created).total_seconds() * 1000), 0)
    _emit("pay_success", tat_ms=tat_ms, amount=amount, currency=currency, gateway=settings.PAYMENT_GATEWAY, source=source)


def _json_body(request: HttpRequest) -> Dict[str, Any] | None:
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return None


@csrf_exempt
@require_POST
def bitpay_webhook(request: HttpRequest) -> JsonResponse:
    ok, reason = verify_signature(request.headers, request.body)
    if not ok:
        _emit("pay_webhook_bad_sig", reason=reason)
        return JsonResponse({"status": "error", "code": "bad_signature"}, status=400)
    payload = _json_body(request)
    if payload is None:
        _emit("pay_webhook_bad_sig", reason="bad_payload")
        return JsonResponse({"status": "error", "code": "bad_payload"}, status=400)
    event_id = payload.get("id") or payload.get("event_id")
    if isinstance(payload.get("data"), dict) and not event_id:
        data = payload["data"]
        event_id = data.get("id") or data.get("event_id")
    ok, key, cached, cache_key = _acquire("webhook", event_id, request, "webhook")
    if not ok:
        return JsonResponse(cached or SUCCESS)
    cache.set(cache_key, SUCCESS, 3600)
    _emit_success(payload, "webhook")
    return JsonResponse(SUCCESS)


@csrf_exempt
@require_POST
def bitpay_verify(request: HttpRequest) -> JsonResponse:
    data = _json_body(request)
    if data is None:
        return JsonResponse({"status": "error", "code": "bad_payload"}, status=400)
    txn_id = data.get("transaction_id") or data.get("id") or data.get("invoice_id")
    ok, key, cached, cache_key = _acquire("verify", txn_id, request, "verify")
    if not ok:
        return JsonResponse(cached or SUCCESS)
    try:
        response = verify_payment(settings.BITPAY_VERIFY_URL, data)
    except Exception as exc:
        logger.warning("bitpay.verify_error", extra={"error": str(exc)})
        _emit(
            "ext_error",
            service="bitpay",
            op="verify",
            code=getattr(getattr(exc, "response", None), "status_code", "timeout"),
            msg=str(exc),
        )
        IdempotencyKey.objects.filter(key=key).delete()
        return JsonResponse(cached or ERROR, status=502)
    success_body: Dict[str, Any] = {"status": "ok", "data": response}
    cache.set(cache_key, success_body, 3600)
    _emit_success(response if isinstance(response, dict) else data, "verify")
    return JsonResponse(success_body)
