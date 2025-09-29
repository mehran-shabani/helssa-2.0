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
    نسخهٔ فعلی برنامه را تعیین می‌کند.
    
    اولویت بازگردانی نسخه به‌ترتیب: مقدار متغیر محیطی HELSSA_VERSION؛ مقدار settings.APP_VERSION؛ آخرین تگ گیت در مخزن؛ در صورت نبودن هر یک یا بروز خطا از مقدار پیش‌فرض "v2.0.0" استفاده می‌شود. این تابع در صورت عدم دسترسی به git یا وقوع خطا به‌صورت ایمن مقدار پیش‌فرض را برمی‌گرداند.
    
    Returns:
        str: رشتهٔ نسخهٔ برنامه — مقدار HELSSA_VERSION در صورت وجود، در غیر این صورت رشتهٔ settings.APP_VERSION (در صورت تعریف)، در غیر این صورت آخرین تگ گیت (بدون فاصله)، و در صورت عدم دسترسی یا خطا "v2.0.0".
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
    except (subprocess.CalledProcessError, FileNotFoundError):  # pragma: no cover - git absent
        return "v2.0.0"


class SystemHealthView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = ()

    def get(self, request, *args, **kwargs):  # noqa: D401
        """
        وضعیت پایهٔ سلامت سرویس را ارائه می‌دهد.
        
        Returns:
            JsonResponse: دیکشنری حاوی کلیدهای زیر:
                - "status": رشته با مقدار "ok".
                - "time": زمان سرور به‌صورت ISO 8601.
                - "version": نسخهٔ فعلی سرویس به‌صورت رشته.
            وضعیت HTTP پاسخ: 200
        """
        return JsonResponse(
            {"status": "ok", "time": timezone.now().isoformat(), "version": _version()}
        )


class SystemReadyView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        """
        بررسی فراگیر وضعیت آماده‌به‌کار مؤلفه‌های سیستم و بازگرداندن وضعیت کلی و جزئیات هر مؤلفه.
        
        این متد سه بررسی مستقل انجام می‌دهد و نتایج را در کلید `components` جمع‌آوری می‌کند:
        - db: صحت اتصال به پایگاه‌داده را با `connection.ensure_connection()` آزمون می‌کند. در صورت موفقیت `{"status": "ok"}` و در صورت شکست `{"status": "fail", "error": "<ExceptionClassName>"}` برمی‌گردد.
        - cache: با نوشتن، خواندن و حذف یک کلید موقت در کش، قابلیت نوشتن/خواندن کش را کنترل می‌کند. اگر مقدار خوانده‌شده برابر مقدار نوشته‌شده باشد `status` برابر `"ok"` قرار می‌گیرد و در غیر اینصورت `"fail"` است. در صورت بروز استثناء نام کلاس استثناء در فیلد `error` گزارش می‌شود.
        - celery: دسترسی به بروکر/کارگران صف وظایف سلری را با `celery_app.control.ping(timeout=1.0)` بررسی می‌کند؛ فیلد `workers` لیستی از پاسخ‌های کارگران را شامل می‌شود و `status` برابر `"ok"` وقتی که حداقل یک کارگر پاسخ دهد و در غیر اینصورت `"fail"` خواهد بود. در صورت بروز استثناء نام کلاس استثناء در `error` قرار می‌گیرد.
        
        اگر هر یک از بررسی‌ها شکست بخورد یا استثناء رخ دهد، وضعیت کلی `"degraded"` گزارش شده و کد وضعیت HTTP برابر 503 خواهد شد؛ در غیر اینصورت وضعیت کلی `"ok"` و کد 200 است. در صورت کاهش‌یافتگی، جزئیات مؤلفه‌ها در لاگ به‌عنوان هشدار ثبت می‌شوند.
        
        Returns:
            JsonResponse: یک JSON شامل:
                - `status`: رشته `"ok"` وقتی همهٔ مؤلفه‌ها سالم باشند، یا `"degraded"` در غیر این‌صورت.
                - `components`: دیکشنری با کلیدهای `db`, `cache`, `celery` که برای هر کدام وضعیت و در صورت نیاز اطلاعات تکمیلی مانند `error` یا `workers` را ارائه می‌کند.
            وضعیت HTTP متناظر: 200 برای سالم و 503 برای کاهش‌یافته.
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
