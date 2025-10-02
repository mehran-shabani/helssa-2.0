import json
import logging
from functools import lru_cache

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "helssa-bitpay-client"})
    return session


def verify_payment(url, payload, headers=None):
    session = _get_session()
    try:
        resp = session.post(
            url,
            json=payload,
            headers=headers or {},
            timeout=settings.BITPAY_REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("bitpay.verify_failed", extra={"error": str(exc)})
        raise
    try:
        return resp.json()
    except json.JSONDecodeError:
        logger.warning(
            "bitpay.non_json_response",
            extra={"url": url, "status": resp.status_code},
        )
        return {"raw": resp.text}
