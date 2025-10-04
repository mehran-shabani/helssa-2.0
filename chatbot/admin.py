from django.contrib import admin

from .models import Attachment, ChatConsent, ChatNote


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


@admin.register(ChatConsent)
class ChatConsentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "scope", "granted", "updated_at")
    readonly_fields = ("user", "scope", "granted", "updated_at")
    search_fields = ("scope", "user__username", "user__email")
    list_filter = ("scope", "granted")
    ordering = ("-updated_at",)

    def has_add_permission(self, request):  # pragma: no cover - admin UI
        return False

    def has_change_permission(self, request, obj=None):  # pragma: no cover - admin UI
        return False


@admin.register(ChatNote)
class ChatNoteAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "conversation_id",
        "user",
        "title",
        "attachments_present",
        "created_at",
        "retention_at",
    )
    readonly_fields = (
        "conversation_id",
        "user",
        "title",
        "summary",
        "tags",
        "source_turn_id",
        "attachments_present",
        "created_at",
        "retention_at",
    )
    search_fields = ("conversation_id", "title", "summary")
    list_filter = ("attachments_present", "created_at")
    ordering = ("-created_at",)

    def has_add_permission(self, request):  # pragma: no cover - admin UI
        return False

    def has_change_permission(self, request, obj=None):  # pragma: no cover - admin UI
        return False
