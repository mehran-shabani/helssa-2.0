import hmac
import time

from django.conf import settings


def verify_signature(headers, body):
    secret = settings.BITPAY_WEBHOOK_SECRET
    if not secret:
        return False, "missing_secret"
    sig_name, ts_name = settings.BITPAY_SIGNATURE_HEADER, settings.BITPAY_TIMESTAMP_HEADER
    headers_lower = {str(k).lower(): v for k, v in headers.items()}
    signature = headers_lower.get(sig_name.lower())
    timestamp = headers_lower.get(ts_name.lower())
    if not signature:
        return False, "missing_signature"
    if not timestamp:
        return False, "missing_timestamp"
    try:
        ts_int = int(timestamp)
    except ValueError:
        return False, "bad_timestamp"
    time_diff = int(time.time()) - ts_int
    if time_diff < -30 or time_diff > settings.PAY_SIG_MAX_SKEW_SECONDS:
        return False, "skew"
    body_bytes = body if isinstance(body, (bytes, bytearray)) else str(body).encode()
    expected = hmac.new(
        secret.encode(),
        bytes(body_bytes) + b"|" + str(timestamp).encode(),
        digestmod="sha256",
    ).hexdigest()
    return (True, "") if hmac.compare_digest(expected, signature) else (False, "mismatch")
