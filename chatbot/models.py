from __future__ import annotations

import uuid
from typing import Any

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import models
from django.utils import timezone


class Conversation(models.Model):
    """Represents a conversation thread with message history."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    session_key = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    summary = models.TextField(blank=True, default="")
    message_count = models.IntegerField(default=0)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["user_id", "-updated_at"]),
            models.Index(fields=["session_key", "-updated_at"]),
        ]

    def __str__(self):
        return f"Conversation {self.id} ({self.message_count} messages)"

    @classmethod
    async def aget_or_create_default(cls, conversation_id: str | None = None):
        """Get existing conversation or create a new one."""
        if conversation_id:
            try:
                return await cls.objects.aget(id=conversation_id)
            except cls.DoesNotExist:
                pass
        return await cls.objects.acreate()

    async def last_messages(self, limit: int = 6) -> list[dict[str, Any]]:
        """Return the last N messages as a list of dicts for context."""
        messages = []
        async for msg in self.messages.order_by("-created_at")[:limit]:
            messages.append({"role": msg.role, "content": msg.content})
        return list(reversed(messages))

    async def append_user_message(self, content: str) -> Message:
        """Append a user message to the conversation."""
        msg = await self.messages.acreate(role="user", content=content)
        self.message_count += 1
        await sync_to_async(self.save)(update_fields=["message_count", "updated_at"])
        return msg

    async def append_assistant_message(self, content: str) -> Message:
        """Append an assistant message to the conversation."""
        msg = await self.messages.acreate(role="assistant", content=content)
        self.message_count += 1
        await sync_to_async(self.save)(update_fields=["message_count", "updated_at"])
        return msg

    async def maybe_summarize(self):
        """
        Auto-summarize the conversation if message count exceeds the threshold.
        This helps reduce token usage by condensing older messages.
        """
        if self.message_count < settings.CHAT_SUMMARY_AFTER_TURNS:
            return

        # Import here to avoid circular dependency
        from chatbot.services.openai_client import summarize_conversation

        recent = await self.last_messages(limit=settings.CHAT_SUMMARY_AFTER_TURNS)
        summary_text = await summarize_conversation(recent)
        self.summary = summary_text
        await sync_to_async(self.save)(update_fields=["summary"])


class Message(models.Model):
    """Individual message in a conversation."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=20, choices=[("user", "User"), ("assistant", "Assistant")])
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
        ]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."
