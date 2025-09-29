from __future__ import annotations

import logging
import os
import subprocess
from uuid import uuid4

from celery import current_app as celery_app
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


def _version() -> str:
    """
    نسخهٔ جاری برنامه را از منابع پیکربندی یا مخزن بازمی‌گرداند.
    
    ابتدا مقدار متغیر محیطی `HELSSA_VERSION` را می‌خواند؛ اگر موجود باشد همان را برمی‌گرداند. در غیر این صورت مقدار `APP_VERSION` از تنظیمات جنگو را بررسی می‌کند و در صورت وجود آن را برمی‌گرداند. اگر هیچ‌کدام فراهم نباشند، سعی می‌کند از خروجی `git describe --tags --abbrev=0` برای تعیین آخرین تگ استفاده کند و در صورت ناموفق بودن عملیات یا نبودن گیت مقدار پیش‌فرض `"v2.0.0"` را بازمی‌گرداند.
    
    Returns:
        str: رشتهٔ نسخه (مثلاً `"v1.2.3"` یا مقدار پیش‌فرض `"v2.0.0"`).
    """
    env_version = os.getenv("HELSSA_VERSION")
    if env_version:
        return env_version
    setting_version = getattr(settings, "APP_VERSION", None)
    if setting_version:
        return str(setting_version)
    try:
        return (
            subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"], text=True)
            .strip()
            or "v2.0.0"
        )
    except Exception:  # pragma: no cover - git may be absent
        return "v2.0.0"


class SystemHealthView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = ()

    def get(self, request, *args, **kwargs):  # noqa: D401
        """
        پاسخ وضعیت سلامت سرویس را با وضعیت کلی، زمان فعلی سرور و نسخه برنامه بازمی‌گرداند.
        
        Returns:
            JsonResponse: JSON شامل کلیدهای `"status"` با مقدار `"ok"`, `"time"` با مقدار زمان فعلی سرور در فرمت ISO، و `"version"` با رشته نسخهٔ برنامه.
        """
        return JsonResponse(
            {"status": "ok", "time": timezone.now().isoformat(), "version": _version()}
        )


class SystemReadyView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        """
        وضعیت آمادگی سیستم را برای چند مولفهٔ حیاتی بررسی کرده و پاسخ JSON با وضعیت کلی و جزئیات هر مولفه باز می‌گرداند.
        
        این متد به ترتیب اتصال به پایگاه‌داده، عملکرد کش (نوشتن/خواندن یک کلید آزمایشی کوتاه‌مدت) و در دسترس‌بودن کارگران Celery (با استفاده از ping) را امتحان می‌کند. برای هر مولفه یک ورودی در کلید `components` ایجاد می‌شود که وضعیت آن را به‌صورت `"ok"` یا `"fail"` نشان می‌دهد و در صورت خطا نام کلاس استثنا ثبت می‌گردد. اگر هر یک از بررسی‌ها ناموفق باشد، وضعیت کلی به `"degraded"` تغییر کرده و پاسخ با کد وضعیت HTTP 503 بازگردانده می‌شود. خطاهای هر بخش لاگ شده و در صورت کاهش قابلیت آماده‌باش، یک هشدار با جزئیات مؤلفه‌ها صادر می‌شود.
        
        Returns:
            JsonResponse: پاسخ JSON با دو کلید:
                - `status`: `"ok"` اگر همهٔ مؤلفه‌ها آماده باشند و `"degraded"` در غیر این صورت.
                - `components`: دیکشنری شامل وضعیت هر مؤلفه (`"db"`, `"cache"`, `"celery"`) و اطلاعات تکمیلی (مانند لیست کارگران یا نام خطا).
            وضعیت HTTP پاسخ برابر 200 در حالت سالم و 503 در حالت کاهش‌یافته است.
        """
        components = {}
        status_code = 200

        try:
            connection.ensure_connection()
            components["db"] = {"status": "ok"}
        except Exception as exc:  # pragma: no cover - difficult to simulate
            components["db"] = {"status": "fail", "error": exc.__class__.__name__}
            logger.exception("database readiness check failed")
            status_code = 503

        try:
            probe_key = f"ready-probe-{uuid4()}"
            cache.set(probe_key, "1", timeout=1)
            cache_ok = cache.get(probe_key) == "1"
            cache.delete(probe_key)
            components["cache"] = {"status": "ok" if cache_ok else "fail"}
            if not cache_ok:
                status_code = 503
        except Exception as exc:  # pragma: no cover - cache misconfig rare
            components["cache"] = {"status": "fail", "error": exc.__class__.__name__}
            logger.exception("cache readiness check failed")
            status_code = 503

        try:
            workers = celery_app.control.ping(timeout=1.0)
            celery_ok = bool(workers)
            components["celery"] = {"status": "ok" if celery_ok else "fail", "workers": workers}
            if not celery_ok:
                status_code = 503
        except Exception as exc:  # pragma: no cover - broker unavailable
            components["celery"] = {"status": "fail", "error": exc.__class__.__name__}
            logger.exception("celery readiness check failed")
            status_code = 503

        if status_code == 503:
            logger.warning("system readiness degraded", extra={"components": components})

        return JsonResponse(
            {"status": "ok" if status_code == 200 else "degraded", "components": components},
            status=status_code,
        )
