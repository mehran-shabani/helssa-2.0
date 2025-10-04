"""
Admin interface for chatbot models.
"""
from django.contrib import admin

from chatbot.models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """Admin interface for Conversation model."""

    list_display = ("id", "user_id", "session_key", "message_count", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("id", "user_id", "session_key")
    readonly_fields = ("id", "created_at", "updated_at", "message_count")
    ordering = ("-updated_at",)

    fieldsets = (
        (
            "Conversation Info",
            {
                "fields": (
                    "id",
                    "user_id",
                    "session_key",
                    "message_count",
                )
            },
        ),
        (
            "Summary",
            {
                "fields": ("summary",),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin interface for Message model."""

    list_display = ("id", "conversation", "role", "content_preview", "created_at")
    list_filter = ("role", "created_at")
    search_fields = ("id", "content", "conversation__id")
    readonly_fields = ("id", "created_at")
    ordering = ("-created_at",)

    def content_preview(self, obj):
        """Show a preview of the message content."""
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content

    content_preview.short_description = "Content Preview"

    fieldsets = (
        (
            "Message Info",
            {
                "fields": (
                    "id",
                    "conversation",
                    "role",
                    "content",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": ("metadata", "created_at"),
            },
        ),
    )
