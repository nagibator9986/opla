---
phase: 01-infrastructure-data-model
plan: 01
type: execute
wave: 1
depends_on: ["00"]
files_modified:
  - backend/baqsy/__init__.py
  - backend/baqsy/settings/__init__.py
  - backend/baqsy/settings/base.py
  - backend/baqsy/settings/dev.py
  - backend/baqsy/settings/prod.py
  - backend/baqsy/urls.py
  - backend/baqsy/wsgi.py
  - backend/baqsy/asgi.py
  - backend/baqsy/celery.py
  - backend/manage.py
  - backend/Dockerfile
  - bot/pyproject.toml
  - bot/main.py
  - bot/Dockerfile
  - docker/docker-compose.yml
  - docker/entrypoint.sh
  - docker/nginx.conf
  - .env.example
  - .gitignore
  - README.md
autonomous: true
requirements:
  - INFRA-01
  - INFRA-02
  - INFRA-03
  - INFRA-04
  - INFRA-05
  - INFRA-07
must_haves:
  truths:
    - "`docker-compose up -d` starts 8 services (web, bot, worker, beat, db, redis, minio, nginx) and all report healthy"
    - "Web container runs `manage.py migrate` automatically at entrypoint"
    - "Django settings read all secrets from .env; .env is in .gitignore; .env.example is committed"
    - "Docker image contains libpango, libharfbuzz, and Cyrillic fonts (Liberation, DejaVu, FreeFont) verified via fc-list"
    - "README contains deployment instructions for ≤2-hour provision on a new host"
  artifacts:
    - path: docker/docker-compose.yml
      provides: "8-service stack with healthchecks and depends_on: service_healthy"
      contains: "web:|bot:|worker:|beat:|db:|redis:|minio:|nginx:"
    - path: backend/baqsy/settings/base.py
      provides: "Django base settings reading from environ, INSTALLED_APPS with apps.core..apps.content, AUTH_USER_MODEL=accounts.BaseUser"
      contains: "AUTH_USER_MODEL"
    - path: backend/Dockerfile
      provides: "Multi-stage Python 3.12 image with Poetry builder + runtime with WeasyPrint system deps and Cyrillic fonts"
      contains: "fonts-liberation|fc-cache"
    - path: docker/entrypoint.sh
      provides: "Wait-for-deps + migrate + collectstatic + gunicorn"
    - path: .env.example
      provides: "All required env vars with empty defaults and inline comments"
    - path: README.md
      provides: "Deployment runbook section"
    - path: bot/Dockerfile
      provides: "Minimal Python 3.12 image for aiogram bot (no WeasyPrint)"
  key_links:
    - from: docker/docker-compose.yml
      to: docker/entrypoint.sh
      via: "web service entrypoint"
      pattern: "entrypoint.*entrypoint.sh"
    - from: backend/baqsy/settings/base.py
      to: .env
      via: "environ.Env.read_env()"
      pattern: "environ\\.Env"
    - from: docker/docker-compose.yml
      to: backend/Dockerfile
      via: "build context"
      pattern: "build:|dockerfile: Dockerfile"
---

<objective>
Bring up the complete 8-service Docker Compose stack with a runnable Django 5.2 skeleton (no models yet — those come in Plan 02). Establishes project structure, settings split, Dockerfiles, env plumbing, and README deployment runbook. At end of plan: `docker-compose up -d` shows all 8 containers healthy; `docker-compose exec web python manage.py check` passes.

Purpose: This is the infrastructure foundation. Plan 02 (models) runs in parallel and writes into `backend/apps/` which this plan has already scaffolded via Plan 00. Plan 03 depends on both.

Output: Runnable Docker Compose stack, Django project that `check`s cleanly, .env.example, README runbook.
</objective>

<execution_context>
@/Users/a1111/.claude/get-shit-done/workflows/execute-plan.md
@/Users/a1111/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/REQUIREMENTS.md
@.planning/phases/01-infrastructure-data-model/01-CONTEXT.md
@.planning/phases/01-infrastructure-data-model/01-RESEARCH.md
@.planning/research/STACK.md
@.planning/research/ARCHITECTURE.md
@.planning/research/PITFALLS.md
@CLAUDE.md

<interfaces>
<!-- From Plan 00 (Wave 0): backend/pyproject.toml exists with all deps and pytest config -->
<!-- From Plan 00: backend/conftest.py exists -->
<!-- From Plan 00: backend/apps/{core,accounts,industries,submissions,payments,reports,delivery,content}/__init__.py exist -->

Canonical django-environ usage (copy verbatim into base.py):
```python
import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(DEBUG=(bool, False), ALLOWED_HOSTS=(list, []))
environ.Env.read_env(BASE_DIR.parent / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")
DATABASES = {"default": env.db("DATABASE_URL")}
```

Canonical AUTH_USER_MODEL (MUST be present from day 1):
```python
AUTH_USER_MODEL = "accounts.BaseUser"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
```

Canonical INSTALLED_APPS ordering (accounts BEFORE any app that references it):
```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    "django_celery_beat",
    # Local apps (accounts must come before industries/submissions that reference it)
    "apps.core",
    "apps.accounts",
    "apps.industries",
    "apps.submissions",
    "apps.payments",
    "apps.reports",
    "apps.delivery",
    "apps.content",
]
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1-1: Django project skeleton (settings, urls, wsgi, celery, manage.py)</name>
  <read_first>
    - /Users/a1111/Desktop/projects/oplata project/.planning/phases/01-infrastructure-data-model/01-RESEARCH.md (lines 670-780 — django-environ, settings patterns, Celery setup)
    - /Users/a1111/Desktop/projects/oplata project/.planning/phases/01-infrastructure-data-model/01-CONTEXT.md (Settings split, Redis layout, Custom User model sections)
    - /Users/a1111/Desktop/projects/oplata project/CLAUDE.md (section 4 Структура репозитория)
  </read_first>
  <files>
backend/baqsy/__init__.py
backend/baqsy/settings/__init__.py
backend/baqsy/settings/base.py
backend/baqsy/settings/dev.py
backend/baqsy/settings/prod.py
backend/baqsy/urls.py
backend/baqsy/wsgi.py
backend/baqsy/asgi.py
backend/baqsy/celery.py
backend/manage.py
  </files>
  <action>
Create the Django project skeleton. Each file has specific required content.

### `backend/baqsy/__init__.py`
```python
from .celery import app as celery_app

__all__ = ("celery_app",)
```

### `backend/baqsy/settings/__init__.py`
Empty file.

### `backend/baqsy/settings/base.py`
Full base settings. MUST include (literal content, not paraphrased):

```python
"""Base settings shared by dev and prod."""
from __future__ import annotations

from pathlib import Path

import environ

# backend/baqsy/settings/base.py → project root is 3 levels up from this file
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
)
# .env lives at repo root (one level above backend/)
environ.Env.read_env(str(BASE_DIR.parent / ".env"))

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

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

DATABASES = {"default": env.db("DATABASE_URL")}

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
```

### `backend/baqsy/settings/dev.py`
```python
from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Structured logging — simple console output for dev
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
```

### `backend/baqsy/settings/prod.py`
```python
from .base import *  # noqa

DEBUG = False

SECURE_SSL_REDIRECT = env("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30  # 30 days
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Sentry stub — populated in Phase 8
# import sentry_sdk; sentry_sdk.init(...)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"json": {"format": "%(asctime)s %(name)s %(levelname)s %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
```

### `backend/baqsy/urls.py`
```python
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path


def health(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
]
```

### `backend/baqsy/wsgi.py`
```python
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "baqsy.settings.dev")
application = get_wsgi_application()
```

### `backend/baqsy/asgi.py`
```python
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "baqsy.settings.dev")
application = get_asgi_application()
```

### `backend/baqsy/celery.py`
```python
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "baqsy.settings.dev")

app = Celery("baqsy")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

### `backend/manage.py`
```python
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "baqsy.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and available on your PYTHONPATH?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
```

Make `manage.py` executable: `chmod +x backend/manage.py`.

CRITICAL: Do NOT create any models in this task. Plan 02 handles models. However, Plan 02 defines `apps.accounts.models.BaseUser` — this settings file references `AUTH_USER_MODEL = "accounts.BaseUser"` which will resolve once Plan 02 creates it. Plans 01 and 02 run in parallel (same wave) — the resolution only matters when `migrate` runs, which happens in Plan 03's integration.
  </action>
  <verify>
    <automated>test -f backend/manage.py && test -f backend/baqsy/settings/base.py && test -f backend/baqsy/settings/dev.py && test -f backend/baqsy/settings/prod.py && test -f backend/baqsy/celery.py && grep -q 'AUTH_USER_MODEL = "accounts.BaseUser"' backend/baqsy/settings/base.py && grep -q 'DATABASES = {"default": env.db' backend/baqsy/settings/base.py && grep -q 'CELERY_BROKER_URL' backend/baqsy/settings/base.py && python -c "import ast; ast.parse(open('backend/baqsy/settings/base.py').read()); ast.parse(open('backend/baqsy/celery.py').read()); ast.parse(open('backend/manage.py').read())"</automated>
  </verify>
  <acceptance_criteria>
    - `backend/baqsy/settings/base.py` contains literal `AUTH_USER_MODEL = "accounts.BaseUser"`
    - `backend/baqsy/settings/base.py` contains all 8 `apps.*` entries in INSTALLED_APPS
    - `backend/baqsy/settings/base.py` uses `env.db("DATABASE_URL")` for DATABASES
    - `backend/baqsy/settings/dev.py` has `DEBUG = True`
    - `backend/baqsy/settings/prod.py` has `DEBUG = False` and `SESSION_COOKIE_SECURE = True`
    - `backend/baqsy/celery.py` contains `Celery("baqsy")` and `autodiscover_tasks()`
    - `backend/baqsy/urls.py` has `/health/` route
    - `backend/manage.py` is executable and references `baqsy.settings.dev`
    - All created Python files parse with `ast.parse`
  </acceptance_criteria>
  <done>Django project skeleton exists. `python manage.py check` would pass once dependencies are installed via Docker build (Task 1-2).</done>
</task>

<task type="auto">
  <name>Task 1-2: Dockerfiles (backend multi-stage + bot minimal) + bot skeleton</name>
  <read_first>
    - /Users/a1111/Desktop/projects/oplata project/.planning/phases/01-infrastructure-data-model/01-RESEARCH.md (Pattern 1 Multi-Stage Dockerfile, lines 200-280)
    - /Users/a1111/Desktop/projects/oplata project/.planning/research/PITFALLS.md (Pitfall 4 — Cyrillic fonts in Docker, lines 88-115)
    - /Users/a1111/Desktop/projects/oplata project/.planning/phases/01-infrastructure-data-model/01-CONTEXT.md (Dockerfiles section lines 161-167)
  </read_first>
  <files>
backend/Dockerfile
bot/pyproject.toml
bot/main.py
bot/Dockerfile
docker/entrypoint.sh
  </files>
  <action>
### `backend/Dockerfile` — multi-stage with WeasyPrint deps and Cyrillic fonts

```dockerfile
# syntax=docker/dockerfile:1

## Stage 1: builder — install Python deps via Poetry
FROM python:3.12-slim AS builder

ENV POETRY_VERSION=1.8.3 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

WORKDIR $PYSETUP_PATH
COPY pyproject.toml ./
# poetry.lock is optional on first build; Poetry will generate + install
RUN poetry install --no-root --only main

## Stage 2: runtime — slim image with WeasyPrint system libs + Cyrillic fonts
FROM python:3.12-slim AS runtime

ENV VENV_PATH="/opt/pysetup/.venv" \
    PATH="/opt/pysetup/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=baqsy.settings.dev

# WeasyPrint system libs + Cyrillic font coverage + netcat for entrypoint wait loop
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libharfbuzz-subset0 \
    libpq5 \
    fonts-liberation \
    fonts-dejavu-core \
    fonts-freefont-ttf \
    fonts-roboto \
    netcat-openbsd \
    curl \
    && fc-cache -f \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -g 1001 baqsy && useradd -u 1001 -g baqsy -m appuser

WORKDIR /app

COPY --from=builder --chown=appuser:baqsy /opt/pysetup/.venv /opt/pysetup/.venv
COPY --chown=appuser:baqsy . /app/

# Copy entrypoint from repo's docker/ dir — docker-compose build context will include it via volume or context
# Since build context is backend/, entrypoint is copied in at compose run time via volume mount.

USER appuser

EXPOSE 8000

# Default command overridden by docker-compose; entrypoint script runs from mounted /docker/entrypoint.sh
CMD ["gunicorn", "baqsy.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "2", "--timeout", "120"]
```

### `docker/entrypoint.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] Waiting for PostgreSQL at db:5432..."
until nc -z db 5432; do sleep 1; done
echo "[entrypoint] Waiting for Redis at redis:6379..."
until nc -z redis 6379; do sleep 1; done
echo "[entrypoint] Waiting for MinIO at minio:9000..."
until nc -z minio 9000; do sleep 1; done

echo "[entrypoint] Running migrations..."
python manage.py migrate --noinput

echo "[entrypoint] Collecting static files..."
python manage.py collectstatic --noinput || true

echo "[entrypoint] Starting gunicorn..."
exec gunicorn baqsy.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-2}" \
  --threads "${GUNICORN_THREADS:-2}" \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
```

Make executable: `chmod +x docker/entrypoint.sh`.

### `bot/pyproject.toml`

```toml
[tool.poetry]
name = "baqsy-bot"
version = "0.1.0"
description = "Baqsy Telegram bot (aiogram 3 thin client)"
authors = ["Baqsy Team"]
package-mode = false

[tool.poetry.dependencies]
python = "^3.12"
aiogram = "3.27.0"
redis = "5.3.0"
httpx = "0.27.0"
python-decouple = "^3.8"
structlog = "25.5.0"

[build-system]
requires = ["poetry-core>=1.8.0"]
build-backend = "poetry.core.masonry.api"
```

### `bot/main.py`

Minimal placeholder that does nothing but boot cleanly. Real handlers are Phase 3. For Phase 1 we just need the container to start without crashing so healthchecks pass.

```python
"""Baqsy Telegram bot — Phase 1 skeleton.

This file intentionally does nothing beyond logging a startup banner.
Full aiogram 3 FSM handlers arrive in Phase 3.
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("baqsy.bot")


async def main() -> None:
    log.info("baqsy-bot skeleton started (Phase 1 — no handlers yet)")
    log.info("TELEGRAM_BOT_TOKEN present: %s", bool(os.environ.get("TELEGRAM_BOT_TOKEN")))
    # Keep the process alive so Docker considers the container running.
    # Phase 3 replaces this with aiogram polling loop.
    while True:
        await asyncio.sleep(60)
        log.info("baqsy-bot heartbeat")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
```

### `bot/Dockerfile`

```dockerfile
# syntax=docker/dockerfile:1

FROM python:3.12-slim AS builder

ENV POETRY_VERSION=1.8.3 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

WORKDIR $PYSETUP_PATH
COPY pyproject.toml ./
RUN poetry install --no-root --only main

FROM python:3.12-slim AS runtime

ENV VENV_PATH="/opt/pysetup/.venv" \
    PATH="/opt/pysetup/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

RUN groupadd -g 1001 baqsy && useradd -u 1001 -g baqsy -m botuser

WORKDIR /app

COPY --from=builder --chown=botuser:baqsy /opt/pysetup/.venv /opt/pysetup/.venv
COPY --chown=botuser:baqsy . /app/

USER botuser

CMD ["python", "main.py"]
```

Bot has NO WeasyPrint system deps — minimal image.
  </action>
  <verify>
    <automated>test -f backend/Dockerfile && test -f bot/Dockerfile && test -f bot/main.py && test -f bot/pyproject.toml && test -f docker/entrypoint.sh && test -x docker/entrypoint.sh && grep -q "fonts-liberation" backend/Dockerfile && grep -q "libpango-1.0-0" backend/Dockerfile && grep -q "fc-cache -f" backend/Dockerfile && grep -q "aiogram = \"3.27.0\"" bot/pyproject.toml && grep -q "python manage.py migrate" docker/entrypoint.sh && bash -n docker/entrypoint.sh</automated>
  </verify>
  <acceptance_criteria>
    - `backend/Dockerfile` has `FROM python:3.12-slim AS builder` AND `FROM python:3.12-slim AS runtime`
    - `backend/Dockerfile` runtime stage installs `libpango-1.0-0`, `libharfbuzz0b`, `fonts-liberation`, `fonts-dejavu-core`
    - `backend/Dockerfile` runs `fc-cache -f` after font install
    - `backend/Dockerfile` installs Poetry in builder stage and copies `.venv` to runtime
    - `bot/Dockerfile` does NOT contain `libpango` or `weasyprint` (minimal image)
    - `bot/pyproject.toml` has `aiogram = "3.27.0"`
    - `docker/entrypoint.sh` is executable (`ls -l` shows `x` bit) and starts with `#!/usr/bin/env bash`
    - `docker/entrypoint.sh` contains `python manage.py migrate --noinput` and `exec gunicorn`
    - `bash -n docker/entrypoint.sh` (syntax check) exits 0
    - `python -c "import ast; ast.parse(open('bot/main.py').read())"` exits 0
  </acceptance_criteria>
  <done>Backend Dockerfile builds a runtime image with all WeasyPrint deps + Cyrillic fonts; bot has its own minimal Dockerfile; entrypoint.sh orchestrates wait-migrate-gunicorn.</done>
</task>

<task type="auto">
  <name>Task 1-3: docker-compose.yml + nginx.conf + .env.example + .gitignore + README</name>
  <read_first>
    - /Users/a1111/Desktop/projects/oplata project/.planning/phases/01-infrastructure-data-model/01-RESEARCH.md (Pattern 2 Docker Compose Healthchecks lines 275-400, django-environ lines 714-745)
    - /Users/a1111/Desktop/projects/oplata project/.planning/phases/01-infrastructure-data-model/01-CONTEXT.md (Docker Compose lines 146-170, Env & secrets lines 181-204, README skeleton lines 210-219)
    - /Users/a1111/Desktop/projects/oplata project/.planning/research/PITFALLS.md (Pitfall 9 Migration Race, Pitfall 7 PostgreSQL locale)
  </read_first>
  <files>
docker/docker-compose.yml
docker/nginx.conf
.env.example
.gitignore
README.md
  </files>
  <action>
### `docker/docker-compose.yml` — 8 services with healthchecks

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-baqsy}
      POSTGRES_USER: ${POSTGRES_USER:-baqsy}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-baqsy}
      LANG: ru_RU.UTF-8
      LC_ALL: ru_RU.UTF-8
      POSTGRES_INITDB_ARGS: "--locale=C.UTF-8 --encoding=UTF8"
    volumes:
      - pg_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-baqsy} -d ${POSTGRES_DB:-baqsy}"]
      interval: 5s
      timeout: 5s
      retries: 10
      start_period: 10s

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY:-baqsyminio}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY:-baqsyminio123}
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"
    healthcheck:
      test: ["CMD", "mc", "ready", "local"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s

  web:
    build:
      context: ../backend
      dockerfile: Dockerfile
    env_file: ../.env
    volumes:
      - ../backend:/app
      - ./entrypoint.sh:/docker/entrypoint.sh:ro
      - static_files:/app/staticfiles
      - media_files:/app/media
    entrypoint: ["/docker/entrypoint.sh"]
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000/health/ || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 40s

  worker:
    build:
      context: ../backend
      dockerfile: Dockerfile
    env_file: ../.env
    volumes:
      - ../backend:/app
    command: celery -A baqsy worker -Q default --pool=prefork --concurrency=2 --max-tasks-per-child=5 --loglevel=INFO
    depends_on:
      web:
        condition: service_healthy

  beat:
    build:
      context: ../backend
      dockerfile: Dockerfile
    env_file: ../.env
    volumes:
      - ../backend:/app
    command: celery -A baqsy beat --scheduler django_celery_beat.schedulers:DatabaseScheduler --loglevel=INFO
    depends_on:
      web:
        condition: service_healthy

  bot:
    build:
      context: ../bot
      dockerfile: Dockerfile
    env_file: ../.env
    volumes:
      - ../bot:/app
    depends_on:
      web:
        condition: service_healthy
      redis:
        condition: service_healthy

  nginx:
    image: nginx:1.27-alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - static_files:/usr/share/nginx/html/static:ro
    depends_on:
      web:
        condition: service_healthy

volumes:
  pg_data:
  redis_data:
  minio_data:
  static_files:
  media_files:
```

NOTE on locale: Debian postgres:16 image doesn't ship `ru_RU.UTF-8` locale out of the box (requires `locale-gen`). Using `C.UTF-8` as `POSTGRES_INITDB_ARGS` is safer for Phase 1; Cyrillic data still stores correctly, sorting is byte-order which is adequate for MVP. Upgrading to full ru_RU locale is a Phase 8 concern.

### `docker/nginx.conf`

```nginx
upstream django {
    server web:8000;
}

server {
    listen 80;
    server_name _;
    client_max_body_size 20M;

    location /static/ {
        alias /usr/share/nginx/html/static/;
        expires 7d;
    }

    location /health/ {
        proxy_pass http://django/health/;
    }

    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### `.env.example`

```dotenv
# Django
DJANGO_SETTINGS_MODULE=baqsy.settings.dev
DJANGO_SECRET_KEY=change-me-to-a-long-random-string
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
POSTGRES_DB=baqsy
POSTGRES_USER=baqsy
POSTGRES_PASSWORD=baqsy
DATABASE_URL=postgres://baqsy:baqsy@db:5432/baqsy

# Redis + Celery
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
AIOGRAM_REDIS_URL=redis://redis:6379/1

# MinIO
MINIO_ACCESS_KEY=baqsyminio
MINIO_SECRET_KEY=baqsyminio123
MINIO_BUCKET=baqsy
MINIO_ENDPOINT_URL=http://minio:9000

# Superuser (for seed_initial)
DJANGO_SUPERUSER_EMAIL=admin@baqsy.kz
DJANGO_SUPERUSER_PASSWORD=changeme

# Telegram (Phase 3)
TELEGRAM_BOT_TOKEN=

# CloudPayments (Phase 4)
CLOUDPAYMENTS_PUBLIC_ID=
CLOUDPAYMENTS_API_SECRET=

# Wazzup24 (Phase 6)
WAZZUP24_API_KEY=
WAZZUP24_CHANNEL_ID=
```

### `.gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
env/
.eggs/
*.egg-info/
dist/
build/

# Django
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal
staticfiles/
media/

# Poetry
poetry.lock

# Env — NEVER commit
.env
.env.local
.env.*.local

# Editors
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Docker
docker-compose.override.yml

# Test
.pytest_cache/
.coverage
htmlcov/
.tox/

# Node (Phase 5)
node_modules/
```

IMPORTANT: `poetry.lock` IS typically committed. For Phase 1 we exclude it because the first Docker build will generate it fresh; we'll add it in a subsequent task. For now keep it in .gitignore to prevent lock conflicts across dev machines.

Actually correct this: committing `poetry.lock` is best practice. Include it in `.gitignore` ONLY for Phase 1 initial builds; unstick by removing the line once the first lockfile lands. For now include this guidance as a comment:

Replace the `poetry.lock` line above with:
```gitignore
# Poetry — commit lockfile after first build
# poetry.lock
```

### `README.md`

```markdown
# Baqsy System

Платформа автоматизированного бизнес-аудита: Telegram-бот → сайт с тарифами → CloudPayments → анкета → ручной аудит → PDF-отчёт → Telegram+WhatsApp.

## Стек

- Python 3.12, Django 5.2 LTS, DRF, Celery 5.6
- aiogram 3.27 (Telegram бот)
- PostgreSQL 16, Redis 7, MinIO (S3-совместимое хранилище)
- React 18 + Vite + TypeScript (Phase 5)
- Docker Compose для dev и prod

## Быстрый старт (локально)

**Требования:** Docker Desktop 26+, Docker Compose v2.

```bash
# 1. Склонировать репозиторий
git clone <repo-url> baqsy-system
cd baqsy-system

# 2. Скопировать env-файл и заполнить секреты
cp .env.example .env
# Открыть .env в редакторе и заполнить DJANGO_SECRET_KEY, POSTGRES_PASSWORD и прочее.

# 3. Поднять стек
docker compose -f docker/docker-compose.yml up -d

# 4. Проверить состояние
docker compose -f docker/docker-compose.yml ps
# Все 8 сервисов должны быть "healthy" через ~60 секунд.

# 5. Засидить начальные данные (superuser, отрасли, тарифы)
docker compose -f docker/docker-compose.yml exec web python manage.py seed_initial

# 6. Открыть админку
#    http://localhost/admin/
#    Логин из .env: DJANGO_SUPERUSER_EMAIL / DJANGO_SUPERUSER_PASSWORD
```

## Архитектура (8 сервисов)

| Сервис | Порт (внеш.) | Назначение |
|--------|--------------|------------|
| `nginx` | 80 | Reverse proxy → web |
| `web` | — | Django + gunicorn (API + админка) |
| `bot` | — | aiogram 3 воркер (long-polling в dev) |
| `worker` | — | Celery воркер (PDF, delivery, webhooks) |
| `beat` | — | Celery beat (периодические задачи) |
| `db` | — | PostgreSQL 16 |
| `redis` | — | Celery broker + aiogram FSM storage |
| `minio` | 9000, 9001 | MinIO (S3-совместимое) |

Внутренние сервисы (web, bot, worker, beat, db, redis) не пробрасывают порты наружу.

## Команды

```bash
# Миграции (применяются автоматически в entrypoint, но можно форсить)
docker compose -f docker/docker-compose.yml exec web python manage.py migrate

# Создать суперпользователя
docker compose -f docker/docker-compose.yml exec web python manage.py createsuperuser

# Django shell
docker compose -f docker/docker-compose.yml exec web python manage.py shell

# Тесты
docker compose -f docker/docker-compose.yml exec web pytest -x

# Логи
docker compose -f docker/docker-compose.yml logs -f web
docker compose -f docker/docker-compose.yml logs -f bot
```

## Deployment на новый хостинг за ≤2 часа

**Цель:** с чистого Ubuntu 24.04 VPS до рабочего `/admin/` за 2 часа или меньше.

### Чек-лист (Ubuntu 24.04)

1. **Установить Docker + Compose** (5 мин)
   ```bash
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER
   newgrp docker
   ```

2. **Склонировать репо** (2 мин)
   ```bash
   git clone <repo-url> /opt/baqsy
   cd /opt/baqsy
   ```

3. **Сконфигурировать `.env`** (10 мин)
   - `cp .env.example .env`
   - Заполнить `DJANGO_SECRET_KEY` (использовать `python -c "import secrets; print(secrets.token_urlsafe(50))"`)
   - Заполнить `POSTGRES_PASSWORD`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY` — сильные пароли
   - `DJANGO_SUPERUSER_EMAIL` + `DJANGO_SUPERUSER_PASSWORD`
   - `TELEGRAM_BOT_TOKEN` (если бот нужен сразу)
   - Опционально: `CLOUDPAYMENTS_*`, `WAZZUP24_*` (можно оставить пустыми для Phase 1)

4. **Настроить prod settings** (5 мин)
   - Установить `DJANGO_SETTINGS_MODULE=baqsy.settings.prod`
   - Установить `DEBUG=False`, `ALLOWED_HOSTS=your-domain.kz`

5. **Поднять стек** (15 мин — первая сборка долгая)
   ```bash
   docker compose -f docker/docker-compose.yml up -d --build
   docker compose -f docker/docker-compose.yml ps  # дождаться healthy
   ```

6. **Засидить данные** (1 мин)
   ```bash
   docker compose -f docker/docker-compose.yml exec web python manage.py seed_initial
   ```

7. **Проверить админку** (5 мин)
   - Открыть `http://<ip>/admin/`
   - Войти с seeded superuser
   - Убедиться, что видны отрасли, тарифы

8. **TLS + домен** — Phase 8 (certbot + nginx). На Phase 1 запускаем по IP:80.

**Итого: ~45–60 минут** (сборка Docker image — самая долгая часть). Phase 8 добавит CI, TLS, мониторинг.

## Phases roadmap

См. `.planning/ROADMAP.md` — 8 фаз от фундамента до production hardening.

## Документация

- `CLAUDE.md` — архитектура, стек, команды (для Claude Code)
- `.planning/PROJECT.md` — Core Value, Key Decisions
- `.planning/REQUIREMENTS.md` — все требования с трассировкой по фазам
```
  </action>
  <verify>
    <automated>test -f docker/docker-compose.yml && test -f docker/nginx.conf && test -f .env.example && test -f .gitignore && test -f README.md && grep -q "postgres:16" docker/docker-compose.yml && grep -q "redis:7-alpine" docker/docker-compose.yml && grep -q "minio/minio" docker/docker-compose.yml && grep -q 'mc.*ready.*local' docker/docker-compose.yml && grep -q "service_healthy" docker/docker-compose.yml && grep -c "^  [a-z]*:$" docker/docker-compose.yml && grep -q "DJANGO_SECRET_KEY" .env.example && grep -q "DATABASE_URL" .env.example && grep -q "^\.env$" .gitignore && grep -q "Deployment" README.md && grep -q "docker compose" README.md</automated>
  </verify>
  <acceptance_criteria>
    - `docker/docker-compose.yml` defines exactly 8 services: `db`, `redis`, `minio`, `web`, `worker`, `beat`, `bot`, `nginx` (verify with `grep -c "^  [a-z][a-z]*:$" docker/docker-compose.yml` — should output >= 8 including volumes line, manually confirm services)
    - `docker-compose.yml` has `healthcheck` block for db, redis, minio, web
    - `docker-compose.yml` uses `test: ["CMD", "mc", "ready", "local"]` for MinIO (NOT curl)
    - `docker-compose.yml` has `depends_on: condition: service_healthy` for web and worker/beat/bot
    - `.env.example` contains literal `DJANGO_SECRET_KEY=`, `DATABASE_URL=`, `MINIO_ACCESS_KEY=`, `TELEGRAM_BOT_TOKEN=`, `CLOUDPAYMENTS_PUBLIC_ID=`, `WAZZUP24_API_KEY=`
    - `.gitignore` contains `.env` (not .env.example)
    - `README.md` contains section `## Deployment на новый хостинг за ≤2 часа`
    - `README.md` mentions `seed_initial` management command
    - `docker/nginx.conf` proxies to `web:8000`
    - YAML parses: `python -c "import yaml; yaml.safe_load(open('docker/docker-compose.yml'))"` exits 0
  </acceptance_criteria>
  <done>Complete Docker Compose configuration with 8 services, correct healthchecks (mc ready for MinIO, not curl), strict service_healthy dependencies, full .env.example with all env vars, README with INFRA-07 deployment runbook.</done>
</task>

</tasks>

<verification>
After Plan 01 tasks complete (and after Plan 02 completes in parallel, Plan 03 runs integration):

```bash
# Static checks (can run without Docker)
python -c "import yaml; yaml.safe_load(open('docker/docker-compose.yml'))"
python -c "import ast; ast.parse(open('backend/baqsy/settings/base.py').read())"
bash -n docker/entrypoint.sh

# File existence
for f in backend/manage.py backend/Dockerfile bot/Dockerfile docker/docker-compose.yml \
         docker/entrypoint.sh docker/nginx.conf .env.example .gitignore README.md; do
  test -f "$f" || { echo "MISSING: $f"; exit 1; }
done

# Docker (requires Plan 02 models merged; runs in Plan 03 integration)
# cp .env.example .env
# docker compose -f docker/docker-compose.yml config --quiet
# docker compose -f docker/docker-compose.yml build web bot
```
</verification>

<success_criteria>
- 8-service Docker Compose definition exists and parses as valid YAML
- backend Django project skeleton (`baqsy/`, `manage.py`) passes `ast.parse` for all .py files
- Dockerfile (backend) is multi-stage with Cyrillic font install + fc-cache
- Dockerfile (bot) is minimal (no WeasyPrint)
- `.env.example` covers all env vars from CONTEXT.md §Env
- README contains Phase 1 deployment runbook targeting ≤2 hours
- `AUTH_USER_MODEL = "accounts.BaseUser"` is set in base.py BEFORE any models exist — Plan 02 will create the model
- NO models/migrations yet — those are Plan 02
- NO backup script or seed command — those are Plan 03
</success_criteria>

<output>
After completion, create `.planning/phases/01-infrastructure-data-model/01-01-SUMMARY.md`
</output>
