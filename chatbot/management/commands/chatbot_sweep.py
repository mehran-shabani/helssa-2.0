from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from chatbot.models import ChatNote


class Command(BaseCommand):
    help = "Remove expired chatbot smart storage notes."

    def handle(self, *args, **options):
        now = timezone.now()
        expired_qs = ChatNote.objects.filter(retention_at__lt=now)
        deleted, _ = expired_qs.delete()
        self.stdout.write(self.style.SUCCESS(f"Removed {deleted} expired notes."))

        history_backend = getattr(settings, "CHATBOT_HISTORY_BACKEND", "")
        if history_backend == "cache":
            self.stdout.write(
                "History backend uses cache; schedule manual eviction for conversation caches if required."
            )
