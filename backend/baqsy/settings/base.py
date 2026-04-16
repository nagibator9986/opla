"""Base settings shared by dev and prod."""
from __future__ import annotations

from pathlib import Path

import environ

# backend/baqsy/settings/base.py -> project root is 3 levels up from this file
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
)
# .env lives at repo root (one level above backend/)
environ.Env.read_env(str(BASE_DIR.parent / ".env"))

SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-secret-key-change-in-prod")
DEBUG = env("DEBUG", default=True)
ALLOWED_HOSTS = env("ALLOWED_HOSTS", default=["*"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "django_celery_beat",
    "django_fsm",
    "apps.core",
    "apps.accounts",
    "apps.industries",
    "apps.submissions",
    "apps.payments",
    "apps.reports",
    "apps.delivery",
    "apps.content",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "baqsy.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "baqsy.wsgi.application"
ASGI_APPLICATION = "baqsy.asgi.application"

DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="sqlite:///db.sqlite3",
    )
}

AUTH_USER_MODEL = "accounts.BaseUser"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ru"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Celery
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://redis:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_BROKER_URL", default="redis://redis:6379/0")
CELERY_BROKER_TRANSPORT_OPTIONS = {"visibility_timeout": 43200}
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = "UTC"

# S3 / MinIO
AWS_ACCESS_KEY_ID = env("MINIO_ACCESS_KEY", default="")
AWS_SECRET_ACCESS_KEY = env("MINIO_SECRET_KEY", default="")
AWS_STORAGE_BUCKET_NAME = env("MINIO_BUCKET", default="baqsy")
AWS_S3_ENDPOINT_URL = env("MINIO_ENDPOINT_URL", default="http://minio:9000")
AWS_S3_ADDRESSING_STYLE = "path"
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_DEFAULT_ACL = "private"
AWS_S3_FILE_OVERWRITE = False
AWS_QUERYSTRING_AUTH = True
AWS_QUERYSTRING_EXPIRE = 60 * 60 * 24 * 7  # 7 days

# CORS
CORS_ALLOW_ALL_ORIGINS = DEBUG  # locked down in prod
