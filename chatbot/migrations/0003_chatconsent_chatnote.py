from __future__ import annotations

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chatbot", "0002_attachment"),
    ]

    operations = [
        migrations.CreateModel(
            name="ChatConsent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("granted", models.BooleanField(default=False)),
                ("scope", models.CharField(default="medical_history", max_length=32)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "unique_together": {("user", "scope")},
            },
        ),
        migrations.CreateModel(
            name="ChatNote",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("conversation_id", models.UUIDField(db_index=True)),
                ("title", models.CharField(blank=True, max_length=200)),
                ("summary", models.TextField()),
                ("tags", models.JSONField(default=dict)),
                ("source_turn_id", models.CharField(blank=True, max_length=64)),
                ("attachments_present", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("retention_at", models.DateTimeField(db_index=True)),
                (
                    "user",
                    models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
        migrations.AddIndex(
            model_name="chatnote",
            index=models.Index(fields=["conversation_id", "created_at"], name="chatbot_chatnote_conversation_id_created_at_idx"),
        ),
    ]
