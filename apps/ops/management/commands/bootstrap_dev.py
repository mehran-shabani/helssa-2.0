import os

from django.contrib.auth import get_user_model
from django.core.management import BaseCommand, call_command


class Command(BaseCommand):
    help = "Apply migrations and ensure a default staff user exists for development."

    def handle(self, *args, **options):
        self.stdout.write("Applying database migrations...")
        call_command("migrate")

        User = get_user_model()
        if User.objects.filter(is_staff=True).exists():
            self.stdout.write("Staff user already present; skipping creation.")
        else:
            username = os.getenv("BOOTSTRAP_ADMIN_USER", "admin")
            email = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "admin@example.com")
            password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "admin1234")

            self.stdout.write(
                f"Creating initial staff user `{username}` <{email}> (password set from env)."
            )
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
            )
            updates = []
            if not user.is_staff:
                user.is_staff = True
                updates.append("is_staff")
            if updates:
                user.save(update_fields=updates)
            self.stdout.write("Staff user created.")

        self.stdout.write("")
        self.stdout.write("Next steps:")
        self.stdout.write("  python manage.py diag_probe --md")
        self.stdout.write("  # Optional for Celery ping:")
        self.stdout.write("  make redis-up")
