from __future__ import annotations

import os
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import dj_database_url
from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv()


def bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

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
    "apps.ops",
    "apps.system",
    "analytics",
    "telemedicine",
    "doctor_online",
    "certificate",
    "sub",
    "down",
    "chatbot",
    "perf",
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
CELERY_BEAT_SCHEDULE = {}

if os.getenv("ENABLE_PERF_SLOWLOG_BEAT", "false").lower() == "true":
    CELERY_BEAT_SCHEDULE["perf-slowlog-weekly"] = {
        "task": "perf.tasks.collect_slowlog",
        "schedule": crontab(hour=1, minute=0, day_of_week="sun"),
    }

PAYMENT_GATEWAY = os.getenv("PAYMENT_GATEWAY", "bitpay")
BITPAY_WEBHOOK_SECRET = os.getenv("BITPAY_WEBHOOK_SECRET")
if not BITPAY_WEBHOOK_SECRET and not DEBUG:
    raise ValueError("BITPAY_WEBHOOK_SECRET must be set in production")
BITPAY_SIGNATURE_HEADER = os.getenv("BITPAY_SIGNATURE_HEADER", "X-Signature")
BITPAY_TIMESTAMP_HEADER = os.getenv("BITPAY_TIMESTAMP_HEADER", "X-Timestamp")
PAY_SIG_MAX_SKEW_SECONDS = int(os.getenv("PAY_SIG_MAX_SKEW_SECONDS", "300"))
BITPAY_VERIFY_URL = os.getenv("BITPAY_VERIFY_URL", "https://bitpay.example/verify")

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

# Chatbot / OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL") or None
OPENAI_ORG = os.getenv("OPENAI_ORG") or None

CHATBOT_DEFAULT_MODEL = os.getenv("CHATBOT_DEFAULT_MODEL", "gpt-4o-mini")
CHATBOT_VISION_MODEL = os.getenv("CHATBOT_VISION_MODEL", CHATBOT_DEFAULT_MODEL)
CHATBOT_REASONING_MODEL = os.getenv(
    "CHATBOT_REASONING_MODEL", CHATBOT_DEFAULT_MODEL
)
_additional_models = set(filter(None, os.getenv("CHATBOT_ADDITIONAL_MODELS", "").split()))
CHATBOT_ALLOWED_MODELS = {
    model
    for model in {
        CHATBOT_DEFAULT_MODEL,
        CHATBOT_VISION_MODEL,
        CHATBOT_REASONING_MODEL,
        *_additional_models,
    }
    if model
}
CHATBOT_MAX_TOKENS = int(os.getenv("CHATBOT_MAX_TOKENS", "1024"))
CHATBOT_REQUEST_TIMEOUT = int(os.getenv("CHATBOT_REQUEST_TIMEOUT", "20"))
CHATBOT_SAVE_UPLOADS = os.getenv("CHATBOT_SAVE_UPLOADS", "false").lower() == "true"
CHATBOT_MAX_IMAGE_FILES = int(os.getenv("CHATBOT_MAX_IMAGE_FILES", "3"))
CHATBOT_MAX_PDF_FILES = int(os.getenv("CHATBOT_MAX_PDF_FILES", "2"))
CHATBOT_MAX_FILE_MB = int(os.getenv("CHATBOT_MAX_FILE_MB", "4"))
CHATBOT_MAX_PAYLOAD_MB = int(os.getenv("CHATBOT_MAX_PAYLOAD_MB", "12"))
CHATBOT_PDF_MAX_PAGES = int(os.getenv("CHATBOT_PDF_MAX_PAGES", "10"))
CHATBOT_PDF_MAX_CHARS = int(os.getenv("CHATBOT_PDF_MAX_CHARS", "8000"))

SMART_STORAGE_ENABLED = bool_env("SMART_STORAGE_ENABLED", True)
SMART_STORAGE_REQUIRE_CONSENT = bool_env("SMART_STORAGE_REQUIRE_CONSENT", True)
SMART_STORAGE_DEFAULT_MODE = os.getenv("SMART_STORAGE_DEFAULT_MODE", "summary")
SMART_STORAGE_TTL_DAYS = int(os.getenv("SMART_STORAGE_TTL_DAYS", "30"))
SMART_STORAGE_CACHE_TTL_SECONDS = int(
    os.getenv("SMART_STORAGE_CACHE_TTL_SECONDS", "86400")
)
SMART_STORAGE_MAX_TURNS = int(os.getenv("SMART_STORAGE_MAX_TURNS", "8"))
SMART_STORAGE_MAX_TOKENS = int(os.getenv("SMART_STORAGE_MAX_TOKENS", "3000"))
SMART_STORAGE_CLASSIFY_WITH_LLM = bool_env("SMART_STORAGE_CLASSIFY_WITH_LLM", False)
SMART_STORAGE_SUMMARIZE_WITH_LLM = bool_env("SMART_STORAGE_SUMMARIZE_WITH_LLM", False)
SMART_STORAGE_ALLOWED_STORE_VALUES = {"auto", "none", "summary", "full"}
