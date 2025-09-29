from __future__ import annotations

from django.utils.dateparse import parse_date
from rest_framework import permissions, serializers, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination

from .models import Event, StatsDaily


class DefaultLimitPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "limit"
    max_page_size = 200


class StatsDailySerializer(serializers.ModelSerializer):
    class Meta:
        model = StatsDaily
        fields = [
            "id",
            "day",
            "rx_started",
            "rx_delivered",
            "pay_success",
            "pay_tat_p50_ms",
            "pay_tat_p95_ms",
            "apk_downloads",
        ]


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ["id", "name", "at", "props"]


class DailyStatsViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = StatsDailySerializer
    pagination_class = DefaultLimitPagination
    queryset = StatsDaily.objects.all().order_by("-day")

    def get_queryset(self):  # noqa: D401
        """
        Queryset مدل آمار روزانه را بر اساس پارامترهای تاریخ پرس‌وجو فیلتر می‌کند.
        
        این متد پارامترهای اختیاری `from` و `to` را از self.request.query_params می‌خواند. هر پارامتر در صورت وجود با `parse_date` تجزیه می‌شود؛ اگر تجزیه ناموفق باشد برای همان پارامتر ValidationError با پیام فرمت تاریخ مورد انتظار (`YYYY-MM-DD`) برگردانده می‌شود. اگر تجزیه موفق باشد، به‌ترتیب فیلترهای `day__gte` (برای `from`) و `day__lte` (برای `to`) روی queryset اعمال می‌گردد و queryset نهایی بازگردانده می‌شود.
        
        Returns:
            QuerySet: QuerySet فیلترشده‌ی `StatsDaily` مطابق پارامترهای تاریخ ارائه‌شده.
        
        Raises:
            ValidationError: اگر مقدار `from` یا `to` موجود باشد اما قابل تجزیه به تاریخ با فرمت `YYYY-MM-DD` نباشد.
        """
        qs = super().get_queryset()
        
        from_param = self.request.query_params.get("from")
        to_param = self.request.query_params.get("to")
        
        if from_param and not (parsed_from := parse_date(from_param)):
            raise ValidationError({"from": "فرمت تاریخ باید YYYY-MM-DD باشد."})
        elif from_param:
            qs = qs.filter(day__gte=parsed_from)
            
        if to_param and not (parsed_to := parse_date(to_param)):
            raise ValidationError({"to": "فرمت تاریخ باید YYYY-MM-DD باشد."})
        elif to_param:
            qs = qs.filter(day__lte=parsed_to)
            
        return qs


class EventViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = EventSerializer
    pagination_class = DefaultLimitPagination
    queryset = Event.objects.all().order_by("-at", "-id")

    def get_queryset(self):  # noqa: D401
        """
        QuerySet مربوط به ViewSet را بازمی‌گرداند و در صورت وجود پارامتر کوئری `name` آن را بر اساس برابری فیلد `name` محدود می‌کند.
        
        این متد QuerySet پایه را از سوپرجلس گرفته و اگر پارامتر کوئری `name` در request موجود باشد، خروجی را به رکوردهایی که مقدار فیلد `name` دقیقاً برابر آن مقدار هستند محدود می‌کند.
        
        Returns:
            QuerySet: مجموعه نتایج فیلترشده بر اساس مقدار `name` در صورت وجود، در غیر این صورت QuerySet پایه.
        """
        qs = super().get_queryset()
        name = self.request.query_params.get("name")
        if name:
            qs = qs.filter(name=name)
        return qs
