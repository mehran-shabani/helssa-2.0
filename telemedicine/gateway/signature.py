import hmac
import time

from django.conf import settings


def verify_signature(headers, body):
    secret = settings.BITPAY_WEBHOOK_SECRET
    if not secret:
        return False, "missing_secret"
    sig_name, ts_name = settings.BITPAY_SIGNATURE_HEADER, settings.BITPAY_TIMESTAMP_HEADER
    signature = headers.get(sig_name) or headers.get(sig_name.lower())
    timestamp = headers.get(ts_name) or headers.get(ts_name.lower())
    if not signature:
        return False, "missing_signature"
    if not timestamp:
        return False, "missing_timestamp"
    try:
        ts_int = int(timestamp)
    except ValueError:
        return False, "bad_timestamp"
    if abs(int(time.time()) - ts_int) > settings.PAY_SIG_MAX_SKEW_SECONDS:
        return False, "skew"
    body_bytes = body if isinstance(body, bytes) else body.encode("utf-8")
    expected = hmac.new(
        secret.encode(), body_bytes + b"|" + timestamp.encode(), digestmod="sha256"
    ).hexdigest()
    return (True, "") if hmac.compare_digest(expected, signature) else (False, "mismatch")
