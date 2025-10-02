from __future__ import annotations

import os
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from urllib.parse import urlparse

import dj_database_url
from dotenv import load_dotenv

from django.core.exceptions import ImproperlyConfigured

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

try:
    APP_VERSION = version("helssa")
except PackageNotFoundError:
    APP_VERSION = os.getenv("HELSSA_VERSION", "2.0.0")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key")
DEBUG = False
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "").split() or ["127.0.0.1", "localhost"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "corsheaders",
    "apps.common",
    "apps.system",
    "analytics",
    "telemedicine",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.request_id.RequestIDMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": dj_database_url.parse(
        os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=600,
        ssl_require=False,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Helssa API",
    "VERSION": APP_VERSION,
    "SERVE_INCLUDE_SCHEMA": False,
}

CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "").split()
CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS", "").split()

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)
CELERY_TASK_TRACK_STARTED = True
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
# CELERY_BEAT_SCHEDULE = {
#     "nightly-analytics": {
#         "task": "analytics.tasks.aggregate_daily_stats",
#         "schedule": 24 * 60 * 60,
#     }
# }

PAYMENT_GATEWAY = os.getenv("PAYMENT_GATEWAY", "bitpay")
BITPAY_WEBHOOK_SECRET = os.getenv("BITPAY_WEBHOOK_SECRET")
if not BITPAY_WEBHOOK_SECRET:
    if os.getenv("DJANGO_SETTINGS_MODULE", "").endswith(".test"):
        BITPAY_WEBHOOK_SECRET = "test-bitpay-secret"
    elif not DEBUG:
        raise ValueError("BITPAY_WEBHOOK_SECRET must be set")

BITPAY_SIGNATURE_HEADER = os.getenv("BITPAY_SIGNATURE_HEADER", "X-Signature")
BITPAY_TIMESTAMP_HEADER = os.getenv("BITPAY_TIMESTAMP_HEADER", "X-Timestamp")
PAY_SIG_MAX_SKEW_SECONDS = int(os.getenv("PAY_SIG_MAX_SKEW_SECONDS", "60"))
BITPAY_VERIFY_URL = os.getenv("BITPAY_VERIFY_URL")
if BITPAY_VERIFY_URL:
    BITPAY_VERIFY_URL = BITPAY_VERIFY_URL.strip()
if not BITPAY_VERIFY_URL:
    if os.getenv("DJANGO_SETTINGS_MODULE", "").endswith(".test"):
        BITPAY_VERIFY_URL = "https://bitpay.test/verify"
    else:
        raise ImproperlyConfigured("BITPAY_VERIFY_URL must be set")

_parsed_bitpay_verify = urlparse(BITPAY_VERIFY_URL)
if _parsed_bitpay_verify.scheme != "https" or not _parsed_bitpay_verify.netloc:
    raise ImproperlyConfigured(
        "BITPAY_VERIFY_URL must be an https URL with a valid host"
    )

BITPAY_REQUEST_TIMEOUT = int(os.getenv("BITPAY_REQUEST_TIMEOUT", "10"))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        }
    },
    "formatters": {
        "json": {
            "()": "core.logging.JsonFormatter",
        }
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
