import os

from django.core.wsgi import get_wsgi_application

from core.logging import setup_logging

setup_logging()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")
application = get_wsgi_application()
