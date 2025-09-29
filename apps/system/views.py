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
    نسخهٔ جاری برنامه را تعیین می‌کند با اولویت‌بندی: متغیر محیطی HELSSA_VERSION، تنظیمات APP_VERSION، و در صورت نبودن آن‌ها تلاش برای استخراج آخرین تگ گیت؛ در نهایت در صورت هرگونه مشکل مقدار پیش‌فرض "v2.0.0" را برمی‌گرداند.
    
    Returns:
        str: رشتهٔ نسخهٔ برنامه؛ مقدار ممکن شامل مقدار HELSSA_VERSION، مقدار settings.APP_VERSION، آخرین تگ گیت (بدون فاصله)، یا در صورت عدم دسترسی یا خطا "v2.0.0".
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
        پاسخ سلامت پایهٔ سرویس را برمی‌گرداند که شامل وضعیت، زمان سرور و نسخهٔ جاری سرویس است.
        
        Response:
            JsonResponse حاوی دیکشنری با کلیدهای زیر:
                - "status": رشته‌ای با مقدار "ok".
                - "time": زمان جاری سرور به فرمت ISO 8601.
                - "version": نسخهٔ جاری سرویس به صورت رشته.
            وضعیت HTTP پاسخ: 200
        """
        return JsonResponse(
            {"status": "ok", "time": timezone.now().isoformat(), "version": _version()}
        )


class SystemReadyView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        """
        وضعیت آماده‌به‌کار هر مؤلفهٔ سیستم را بررسی و وضعیت کلی را بازمی‌گرداند.
        
        این متد سه بررسی جداگانه انجام می‌دهد و نتایج هر یک را در فیلد `components` جمع‌آوری می‌کند:
        - `db`: اتصال به پایگاه‌داده را با `connection.ensure_connection()` بررسی می‌کند؛ مقدار `status` برابر `"ok"` در صورت موفقیت و `"fail"` در صورت شکست است و در شکست نام کلاس استثناء در فیلد `error` قرار می‌گیرد.
        - `cache`: با نوشتن و خواندن یک کلید موقت وضعیت کش را آزمایش می‌کند؛ `status` برابر `"ok"` وقتی مقدار خوانده‌شده مطابق انتظار باشد، و در غیر این‌صورت `"fail"` است. در صورت استثناء، نام کلاس استثناء در `error` گزارش می‌شود.
        - `celery`: با فراخوانی `celery_app.control.ping(timeout=1.0)` وضعیت کارگران/بروکر سلری را بررسی می‌کند؛ فیلد `workers` نتیجهٔ `ping` و `status` برابر `"ok"` یا `"fail"` خواهد بود. در صورت استثناء، نام کلاس استثناء در `error` قرار می‌گیرد.
        
        اگر هر یک از مؤلفه‌ها دچار شکست یا استثناء شود، وضعیت کلی به‌عنوان کاهش‌یافته (`degraded`) گزارش و کد وضعیت HTTP به 503 تغییر می‌کند. در حین بررسی‌ها، خطاها و وضعیت کاهش‌یافته با logger ثبت می‌شوند.
        
        Returns:
            JsonResponse: پاسخ JSON با دو کلید:
                - `status`: رشته `"ok"` وقتی همهٔ مؤلفه‌ها سالم باشند، یا `"degraded"` در غیر این‌صورت.
                - `components`: دیکشنری حاوی وضعیت هر مؤلفه (`db`, `cache`, `celery`) و اطلاعات مرتبط (مثلاً `error` یا `workers`).
            وضعیت HTTP مربوطه 200 برای سالم و 503 برای کاهش‌یافته.
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
