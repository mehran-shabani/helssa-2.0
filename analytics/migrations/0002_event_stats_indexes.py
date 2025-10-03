from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("analytics", "0001_initial"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="event",
            index=models.Index(
                name="analytics_event_at_idx",
                fields=["at"],
            ),
        ),
        migrations.AddIndex(
            model_name="statsdaily",
            index=models.Index(
                name="analytics_statsdaily_day_idx",
                fields=["day"],
            ),
        ),
    ]
