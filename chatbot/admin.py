from django.contrib import admin

from .models import Attachment


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "kind", "sha256", "created_at")
    readonly_fields = ("file", "kind", "sha256", "created_at")
    search_fields = ("sha256",)
    ordering = ("-created_at",)

    def has_add_permission(self, request):  # pragma: no cover - admin UI
        return False

    def has_change_permission(self, request, obj=None):  # pragma: no cover - admin UI
        return False
