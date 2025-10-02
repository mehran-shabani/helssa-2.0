from django.contrib import admin

from .models import IdempotencyKey


@admin.register(IdempotencyKey)
class IdempotencyKeyAdmin(admin.ModelAdmin):
    list_display = ("key", "created_at")
    search_fields = ("key",)
    readonly_fields = ("key", "created_at")

    def has_add_permission(self, request):  # pragma: no cover
        return False

    def has_delete_permission(self, request, obj=None):  # pragma: no cover
        return False
