"""Base settings shared by dev and prod."""
from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import environ
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

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
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"] if DEBUG else [])

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_celery_beat",
    "django_fsm",
    "axes",
    "adminsortable2",
    "django_ckeditor_5",
    "apps.core",
    "apps.accounts",
    "apps.industries",
    "apps.submissions",
    "apps.payments",
    "apps.reports",
    "apps.delivery",
    "apps.content",
    "apps.dashboard",
    "apps.ai",
    "apps.cases",
    "apps.blog",
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
    "axes.middleware.AxesMiddleware",  # MUST be last
]

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
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
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOW_CREDENTIALS = True

# Redis
REDIS_HOST = env("REDIS_HOST", default="redis")
REDIS_PORT = env.int("REDIS_PORT", default=6379)
REDIS_URL = env("REDIS_URL", default=f"redis://{REDIS_HOST}:{REDIS_PORT}")

# Bot API secret (X-Bot-Token header)
BOT_API_SECRET = env("BOT_API_SECRET", default="dev-bot-secret")

# CloudPayments KZ
CLOUDPAYMENTS_PUBLIC_ID = env("CLOUDPAYMENTS_PUBLIC_ID", default="")
CLOUDPAYMENTS_API_SECRET = env("CLOUDPAYMENTS_API_SECRET", default="")

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/min",
        "user": "240/min",
    },
    "EXCEPTION_HANDLER": "apps.core.exceptions.custom_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=4),  # extended for bot questionnaire sessions (was 1h)
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# django-axes brute-force protection
AXES_ENABLED = True
AXES_FAILURE_LIMIT = 10
AXES_COOLOFF_TIME = timedelta(hours=1)
AXES_LOCKOUT_PARAMETERS = ["ip_address"]
AXES_RESET_ON_SUCCESS = True

# django-unfold CRM admin
UNFOLD = {
    "SITE_TITLE": "Baqsy CRM",
    "SITE_HEADER": "Baqsy System",
    "SITE_URL": "/",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "DASHBOARD_CALLBACK": "apps.dashboard.views.dashboard_callback",
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": _("Аналитика"),
                "items": [
                    {
                        "title": _("Дашборд"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": _("Заказы"),
                "items": [
                    {
                        "title": _("Заявки"),
                        "icon": "description",
                        "link": reverse_lazy("admin:submissions_submission_changelist"),
                    },
                    {
                        "title": _("Отчёты"),
                        "icon": "picture_as_pdf",
                        "link": reverse_lazy("admin:reports_auditreport_changelist"),
                    },
                    {
                        "title": _("Оплаты"),
                        "icon": "credit_card",
                        "link": reverse_lazy("admin:payments_payment_changelist"),
                    },
                ],
            },
            {
                "title": _("Контент"),
                "items": [
                    {
                        "title": _("Тарифы"),
                        "icon": "payments",
                        "link": reverse_lazy("admin:payments_tariff_changelist"),
                    },
                    {
                        "title": _("Блоки лендинга"),
                        "icon": "web",
                        "link": reverse_lazy("admin:content_contentblock_changelist"),
                    },
                    {
                        "title": _("Кейсы"),
                        "icon": "auto_stories",
                        "link": reverse_lazy("admin:cases_case_changelist"),
                    },
                    {
                        "title": _("Статьи"),
                        "icon": "article",
                        "link": reverse_lazy("admin:blog_blogpost_changelist"),
                    },
                ],
            },
            {
                "title": _("AI-ассистент"),
                "items": [
                    {
                        "title": _("Конфигурация"),
                        "icon": "smart_toy",
                        "link": reverse_lazy("admin:ai_aiassistantconfig_changelist"),
                    },
                    {
                        "title": _("Чат-сессии"),
                        "icon": "chat",
                        "link": reverse_lazy("admin:ai_chatsession_changelist"),
                    },
                ],
            },
            {
                "title": _("Конфигурация"),
                "items": [
                    {
                        "title": _("Отрасли"),
                        "icon": "category",
                        "link": reverse_lazy("admin:industries_industry_changelist"),
                    },
                    {
                        "title": _("Шаблоны анкет"),
                        "icon": "assignment",
                        "link": reverse_lazy("admin:industries_questionnairetemplate_changelist"),
                    },
                ],
            },
            {
                "title": _("Пользователи"),
                "items": [
                    {
                        "title": _("Клиенты"),
                        "icon": "people",
                        "link": reverse_lazy("admin:accounts_clientprofile_changelist"),
                    },
                    {
                        "title": _("Доставка"),
                        "icon": "local_shipping",
                        "link": reverse_lazy("admin:delivery_deliverylog_changelist"),
                    },
                ],
            },
        ],
    },
}

# OpenAI — used by apps.ai for the landing chat widget
OPENAI_API_KEY = env("OPENAI_API_KEY", default="")

# Email — used by group-audit invitations (apps/submissions/group_invites.py).
# Falls back to console backend in DEBUG so dev environments don't try to talk
# to a real SMTP server.
EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend"
    if DEBUG
    else "django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@baqsy.kz")
EMAIL_TIMEOUT = 15

# CKEditor 5
CKEDITOR_5_CONFIGS = {
    "content_block": {
        "toolbar": {
            "items": [
                "heading", "|",
                "bold", "italic", "underline", "|",
                "link", "bulletedList", "numberedList", "|",
                "blockQuote", "insertTable", "|",
                "undo", "redo",
            ]
        },
        "language": "ru",
    },
}
