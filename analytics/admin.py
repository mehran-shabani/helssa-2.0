from django.contrib import admin

from .models import Event, StatsDaily


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "at")
    search_fields = ("name", "user__email")
    list_filter = ("at",)


@admin.register(StatsDaily)
class StatsDailyAdmin(admin.ModelAdmin):
    list_display = ("day", "rx_started", "rx_delivered", "pay_success")
    search_fields = ("day",)
