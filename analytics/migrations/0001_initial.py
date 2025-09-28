import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="StatsDaily",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("day", models.DateField(db_index=True, unique=True)),
                ("rx_started", models.PositiveIntegerField(default=0)),
                ("rx_delivered", models.PositiveIntegerField(default=0)),
                ("pay_success", models.PositiveIntegerField(default=0)),
                ("pay_tat_p50_ms", models.PositiveIntegerField(default=0)),
                ("pay_tat_p95_ms", models.PositiveIntegerField(default=0)),
                ("apk_downloads", models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name="Event",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=60)),
                ("props", models.JSONField(blank=True, default=dict)),
                ("at", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
