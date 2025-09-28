import os

from django.core.asgi import get_asgi_application

from core.logging import setup_logging

setup_logging()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
application = get_asgi_application()
