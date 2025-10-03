from __future__ import annotations

import logging
import os

from django.conf import settings
from django.db import Error
from django.utils.timezone import now

logger = logging.getLogger(__name__)

READY_LAST_OK_TIMESTAMP = 0


def note_ready_success() -> None:
    global READY_LAST_OK_TIMESTAMP
    READY_LAST_OK_TIMESTAMP = int(now().timestamp())


def _safe_count(model) -> int:
    try:
        return model.objects.count()
    except Error:  # pragma: no cover - db outages hard to simulate
        logger.exception("metrics count failed", extra={"model": model._meta.label_lower})
        return 0


def build_metrics() -> str:
    from analytics.models import Event, StatsDaily

    parts = [
        f'helssa_app_info{{version="{settings.APP_VERSION}"}} 1',
        f"helssa_events_total {_safe_count(Event)}",
        f"helssa_statsdays_total {_safe_count(StatsDaily)}",
        f"helssa_ready_last_ok_timestamp {READY_LAST_OK_TIMESTAMP}",
    ]
    return "\n".join(parts) + "\n"


def metrics_enabled() -> bool:
    return os.getenv("ENABLE_METRICS", "false").lower() == "true"
