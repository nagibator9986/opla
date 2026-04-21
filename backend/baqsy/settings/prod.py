import logging

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa

DEBUG = False

_prod_log = logging.getLogger("baqsy.prod")

# Hard-fail checks — these leave the service insecure if missing, so we refuse
# to boot at all. Payment secrets (CloudPayments, WhatsApp) degrade features
# but don't compromise the rest of the app, so they only log a warning.
if not ALLOWED_HOSTS or ALLOWED_HOSTS == ["*"]:
    raise ImproperlyConfigured(
        "ALLOWED_HOSTS must be explicitly set in production (comma-separated env)."
    )

if SECRET_KEY.startswith("dev-"):
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set in production.")

if not env("BOT_API_SECRET", default="") or BOT_API_SECRET == "dev-bot-secret":
    raise ImproperlyConfigured("BOT_API_SECRET must be set in production.")

if not env("CLOUDPAYMENTS_API_SECRET", default=""):
    _prod_log.warning(
        "CLOUDPAYMENTS_API_SECRET is not set — webhooks will reject all payments "
        "until it is configured. Safe for pre-launch; required before going live."
    )

SECURE_SSL_REDIRECT = env("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30  # 30 days
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
X_FRAME_OPTIONS = "DENY"

# CORS must be explicitly configured in prod — never allow-all.
# If neither CORS_ALLOWED_ORIGINS nor CSRF_TRUSTED_ORIGINS are set we fall
# back to ALLOWED_HOSTS-derived https:// origins and warn, so a misconfigured
# deployment doesn't silently break the frontend.
CORS_ALLOW_ALL_ORIGINS = False
if not CORS_ALLOWED_ORIGINS:
    _derived = [f"https://{h}" for h in ALLOWED_HOSTS if "." in h and h != "localhost"]
    if _derived:
        CORS_ALLOWED_ORIGINS = _derived
        _prod_log.warning(
            "CORS_ALLOWED_ORIGINS not set — using derived defaults: %s", _derived
        )
    else:
        raise ImproperlyConfigured(
            "CORS_ALLOWED_ORIGINS must be set in production (comma-separated)."
        )

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=CORS_ALLOWED_ORIGINS)

# Sentry stub — populated in Phase 8
# import sentry_sdk; sentry_sdk.init(...)

# Structured JSON logging via structlog (installed via pyproject.toml).
# Falls back to plain JSON-ish format when structlog isn't available yet.
try:
    import structlog

    _pre_chain = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.processors.JSONRenderer(),
                "foreign_pre_chain": _pre_chain,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
            },
        },
        "root": {"handlers": ["console"], "level": "INFO"},
        "loggers": {
            "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
            "celery": {"handlers": ["console"], "level": "INFO", "propagate": False},
            "apps": {"handlers": ["console"], "level": "INFO", "propagate": False},
        },
    }

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
except ImportError:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {"format": "%(asctime)s %(name)s %(levelname)s %(message)s"}
        },
        "handlers": {
            "console": {"class": "logging.StreamHandler", "formatter": "json"}
        },
        "root": {"handlers": ["console"], "level": "INFO"},
    }
