from __future__ import annotations

import logging

from celery import shared_task
from django.core.management import call_command

logger = logging.getLogger(__name__)


@shared_task
def collect_slowlog() -> None:
    logger.info("Scheduled perf_slowlog run starting")
    call_command("perf_slowlog")
    logger.info("Scheduled perf_slowlog run completed")
