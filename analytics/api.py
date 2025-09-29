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
        پرس‌وجوی پایه را بر اساس پارامترهای کوئری HTTP `from` و `to` فیلتر می‌کند.
        
        پارامترها:
        - از پارامترهای کوئری `from` و `to` برای محدود کردن بازه تاریخ استفاده می‌شود. هر پارامتر با `django.utils.dateparse.parse_date` تجزیه می‌شود (فرمت منتظر: YYYY-MM-DD). در صورت موفقیت‌آمیز بودن تجزیه، به ترتیب فیلترهای `day__gte` و `day__lte` روی QuerySet اعمال می‌گردد. پارامترهای نامعتبر یا غیریکسان نادیده گرفته می‌شوند.
        
        Returns:
        - QuerySet: همان QuerySet ورودی پس از اعمال فیلترهای تاریخ (در صورت وجود پارامترهای معتبر).
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
        مجموعه QuerySet مربوط به Eventها را تهیه می‌کند و در صورت وجود پارامتر query با نام "name" آن را بر اساس نام فیلتر می‌کند.
        
        شرح:
            ابتدا QuerySet پیش‌فرض والد را دریافت می‌کند. سپس پارامتر query با کلید "name" را از درخواست می‌خواند و در صورت وجود، QuerySet را محدود به رویدادهایی می‌کند که فیلد `name` برابر مقدار ارائه‌شده باشند.
        
        Returns:
            QuerySet: مجموعه‌ای از شیءهای Event (مرتب‌شده طبق queryset پیش‌فرض کلاس) که در صورت مشخص شدن پارامتر `name` تنها شامل Eventهایی با نام برابر آن مقدار است.
        """
        qs = super().get_queryset()
        name = self.request.query_params.get("name")
        if name:
            qs = qs.filter(name=name)
        return qs
