from django.db import migrations, models


INDEXES = [
    models.Index(
        name="telemed_trans_user_status_created_idx",
        fields=["user", "status", "-created_at"],
    ),
    models.Index(
        name="telemed_trans_created_idx",
        fields=["created_at"],
    ),
]


def forwards(apps, schema_editor):
    try:
        model = apps.get_model("telemedicine", "Transaction")
    except LookupError:
        return
    with schema_editor.connection.cursor() as cursor:
        constraints = schema_editor.connection.introspection.get_constraints(cursor, model._meta.db_table)
    existing = set(constraints)
    for index in INDEXES:
        if index.name in existing:
            continue
        schema_editor.add_index(model, index)


def backwards(apps, schema_editor):
    try:
        model = apps.get_model("telemedicine", "Transaction")
    except LookupError:
        return
    for index in INDEXES:
        try:
            schema_editor.remove_index(model, index)
        except Exception:
            # Index might not exist on some backends; swallow to keep reversible.
            continue


class Migration(migrations.Migration):

    dependencies = [
        ("telemedicine", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
