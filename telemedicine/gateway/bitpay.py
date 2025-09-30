import json
import logging

import requests

logger = logging.getLogger(__name__)


def verify_payment(url, payload, headers=None):
    try:
        resp = requests.post(url, json=payload, headers=headers or {}, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("bitpay.verify_failed", extra={"error": str(exc)})
        raise
    try:
        return resp.json()
    except json.JSONDecodeError:
        return {"raw": resp.text}
