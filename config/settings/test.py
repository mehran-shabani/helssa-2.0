import dj_database_url

from .base import *  # noqa
from .base import BASE_DIR
from .base import DATABASES as BASE_DATABASES

DEBUG = False
SECRET_KEY = "test-secret-key"
DATABASES = BASE_DATABASES.copy()
DATABASES["default"] = dj_database_url.parse(
    f"sqlite:///{BASE_DIR / 'test.sqlite3'}",
    conn_max_age=0,
)
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
