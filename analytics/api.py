from __future__ import annotations

from django.utils.dateparse import parse_date
from rest_framework import permissions, serializers, viewsets
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
        بازگرداندن queryset از مدل آمار روزانه که در صورت وجود، براساس پارامترهای کوئری `from` و `to` بر اساس فیلتر تاریخ محدود شده است.
        
        پارامترها:
            - این متد پارامتر مستقیمی دریافت نمی‌کند؛ از `self.request.query_params` پارامترهای `from` و `to` را می‌خواند. هر پارامتر در صورت وجود با `parse_date` تجزیه می‌شود و در صورت موفقیت فیلتر مناسب اعمال می‌گردد. مقادیر نامعتبر یا غایب نادیده گرفته می‌شوند.
        
        Returns:
            QuerySet: یک QuerySet از مدل `StatsDaily` محدود شده به روزهای بزرگتر یا مساوی تاریخ `from` و/یا کوچکتر یا مساوی تاریخ `to` در صورت ارائه و معتبر بودن آن‌ها.
        """
        qs = super().get_queryset()
        from_param = self.request.query_params.get("from")
        to_param = self.request.query_params.get("to")
        if from_param:
            parsed_from = parse_date(from_param)
            if parsed_from:
                qs = qs.filter(day__gte=parsed_from)
        if to_param:
            parsed_to = parse_date(to_param)
            if parsed_to:
                qs = qs.filter(day__lte=parsed_to)
        return qs


class EventViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = EventSerializer
    pagination_class = DefaultLimitPagination
    queryset = Event.objects.all().order_by("-at", "-id")

    def get_queryset(self):  # noqa: D401
        """
        QuerySet پایه را آماده می‌کند و در صورت وجود پارامتر query با نام "name" آن را بر اساس مقدار برابر فیلتر می‌کند.
        
        این متد مقدار "name" را از request.query_params می‌خواند و اگر مقدار داده شده وجود داشته باشد، QuerySet را به رکوردهایی محدود می‌کند که فیلد `name` برابر آن مقدار باشند.
        
        Returns:
            QuerySet: مجموعه نتایج فیلترشده بر اساس `name` یا QuerySet اصلی در صورت عدم وجود پارامتر.
        """
        qs = super().get_queryset()
        name = self.request.query_params.get("name")
        if name:
            qs = qs.filter(name=name)
        return qs
