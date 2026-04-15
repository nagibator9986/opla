# Phase 1: Infrastructure & Data Model - Research

**Researched:** 2026-04-15
**Domain:** Django 5.2 project skeleton, Docker Compose 8-service stack, 13 data models with versioning invariants
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Python & package manager:** Poetry 1.8+; groups `main`, `dev`, `prod`; Python 3.12 slim in Docker
- **Separate pyproject.toml** for `backend/` and `bot/` (bot has aiogram/httpx, no Django)
- **Repository structure:** `baqsy-system/backend/baqsy/` (settings/), `backend/apps/` (core, accounts, industries, submissions, payments, reports, delivery, content), `bot/`, `frontend/`, `docker/`
- **Settings split:** `settings/base.py`, `settings/dev.py`, `settings/prod.py`; `DJANGO_SETTINGS_MODULE` from `.env`
- **Custom User model:** `apps.accounts.models.BaseUser` (AbstractBaseUser, email login); `AUTH_USER_MODEL = "accounts.BaseUser"` from day 1; `ClientProfile` separate model linked by `telegram_id`
- **Core abstract models:** `TimestampedModel` (created_at, updated_at), `UUIDModel` (UUID PK) in `apps/core`; BigAutoField for internal models
- **Submission FSM library:** `django-fsm-2` (maintained fork of archived django-fsm; v4.2.4; confirmed Django 5.2 compatible)
- **Submission states:** `created → in_progress_basic → paid → in_progress_full → completed → under_audit → delivered`
- **QuestionnaireTemplate versioning:** `unique_together = [("industry", "version")]` + partial UniqueConstraint with `Q(is_active=True)`; `create_new_version` classmethod; atomic deactivation of old version
- **Answer.value:** JSONField (PostgreSQL JSONB); schema per `field_type`
- **Timezone:** `TIME_ZONE = "UTC"`, `USE_TZ = True`; display in Asia/Almaty at the view layer
- **PostgreSQL 16** with `pg_trgm`, locale `ru_RU.UTF-8`, restricted DB user
- **Redis DB isolation:** db=0 Celery, db=1 aiogram FSM, db=2 deep-link tokens, db=3 rate limiting
- **MinIO:** single `baqsy` bucket; `MediaStorage` and `ReportStorage` as two storage classes; bucket auto-created by entrypoint
- **Docker Compose:** 8 services (web, bot, worker, beat, db, redis, minio, nginx); healthchecks + `depends_on: condition: service_healthy`
- **Dockerfile (backend):** multi-stage; Stage 1 builder (poetry install); Stage 2 runtime (python:3.12-slim + WeasyPrint system deps + Cyrillic fonts + `fc-cache -f`)
- **Migrations:** one `0001_initial.py` per app; auto-applied in `web` entrypoint only
- **Seed command:** `python manage.py seed_initial`; idempotent; creates superuser, 5 industries, demo templates, 3 tariffs
- **Env management:** read via `django-environ` or `os.getenv` (researcher to recommend one — see Claude's Discretion)
- **Backups:** `docker/postgres-backup.sh` (pg_dump | gzip → MinIO via `mc`); manual trigger in Phase 1, cron in Phase 8

### Claude's Discretion

- Exact minor dependency versions (Poetry locks them at install time)
- Celery queue names (default: `default`)
- Healthcheck endpoint structure (simple `/health/` for web, `celery inspect ping` for worker)
- Volume names in docker-compose
- Gunicorn worker config (`--workers 2 --threads 2` for dev)
- `apps/core/mixins.py` structure
- **Env library choice:** researcher to recommend `django-environ` vs `python-decouple`

### Deferred Ideas (OUT OF SCOPE)

- CI pipeline (GitHub Actions) — Phase 8
- TLS via certbot — Phase 8
- Sentry integration — Phase 8
- Backup cron automation — Phase 8
- Production-grade admin UI — Phase 7
- Seed production data (real industry content) — post-v1
- KZ data residency hosting decision — business decision noted in STATE.md
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INFRA-01 | Docker Compose deploys full stack (8 services) with one command | Docker Compose healthcheck patterns; MinIO `mc ready local` healthcheck; `depends_on: condition: service_healthy` |
| INFRA-02 | Project starts in dev via `docker-compose up` without additional steps | entrypoint.sh pattern: wait for PG/Redis → migrate → collectstatic → gunicorn |
| INFRA-03 | All secrets read from `.env`; only `.env.example` in repo | `django-environ` recommended (DATABASE_URL parsing built-in); `.gitignore` pattern |
| INFRA-04 | Django migrations automatically applied at web container start | `web` entrypoint runs `manage.py migrate --noinput`; other services `depends_on: web: condition: service_healthy` |
| INFRA-05 | Docker image contains Cyrillic system fonts for WeasyPrint | `fonts-liberation fonts-dejavu-core fonts-freefont-ttf` + `fc-cache -f` + WeasyPrint system libs |
| INFRA-06 | PostgreSQL backed up to MinIO daily | `postgres-backup.sh` with `pg_dump | gzip | mc pipe`; manual trigger in Phase 1 |
| INFRA-07 | README contains deployment instructions (new host in ≤2 hours) | Skeleton structure in CONTEXT.md |
| DATA-01 | `Industry` model | Simple model with `name`, `slug`, `is_active` — no special complexity |
| DATA-02 | `QuestionnaireTemplate` with `industry_id`, `version`, `is_active`, `name` | Partial UniqueConstraint pattern for one-active-per-industry |
| DATA-03 | `Question` with `template_id`, `order`, `text`, `field_type`, `options` JSONB, `required`, `block` | JSONB field for options; CharField choices for `field_type` and `block` |
| DATA-04 | `ClientProfile` with `telegram_id`, `name`, `company`, `phone_wa`, `city`, `industry_id` | Separate from User model; `telegram_id` as BigIntegerField unique |
| DATA-05 | `Submission` with `client_id`, `template_id`, `status`, `created_at`, `completed_at` | FSMField for status; UUID primary key; immutability constraint on `template_id` |
| DATA-06 | `Answer` with `submission_id`, `question_id`, `value` JSONB, `answered_at` | JSONField for value; index on `(submission_id, question_id)` |
| DATA-07 | `Tariff` with `code`, `title`, `price_kzt`, `description`, `is_active` | Simple model; prices in DB not code |
| DATA-08 | `Payment` with `submission_id`, `tariff_id`, `transaction_id` unique, `status`, `amount`, `raw_webhook` JSONB | `transaction_id` unique constraint for idempotency |
| DATA-09 | `AuditReport` with `submission_id`, `admin_text`, `pdf_url`, `status`, `approved_at` | OneToOneField to Submission |
| DATA-10 | `DeliveryLog` with `report_id`, `channel`, `status`, `external_id`, `error` | ForeignKey to AuditReport; separate rows per channel |
| DATA-11 | `ContentBlock` for landing texts (key-value with HTML content) | Simple model; `key` unique CharField, `value` TextField |
| DATA-12 | QuestionnaireTemplate versioning: any edit creates new version, exactly one active | `create_new_version` classmethod; atomic transaction; partial UniqueConstraint |
| DATA-13 | `Submission.template_id` immutable after creation | `save()` override raises ValidationError on change |
</phase_requirements>

---

## Summary

Phase 1 establishes the entire project skeleton: Docker Compose with 8 services, the Django project structure with 7 domain apps + 1 core app, 13 data models with migrations, and two critical data invariants (template versioning and submission immutability). Every decision has been locked in CONTEXT.md — this phase has zero exploratory work, only implementation of known choices.

The two most technically tricky items are: (1) the `django-fsm` situation — the original package was **archived in October 2025** and must be replaced with `django-fsm-2` (v4.2.4, drop-in compatible, Django 5.2 confirmed), and (2) the WeasyPrint system dependencies in Docker, which require specific apt packages AND Cyrillic font packages to be installed correctly in the runtime stage, or PDFs will silently produce unreadable output.

**Primary recommendation:** Use `django-environ` for config (has DATABASE_URL/REDIS_URL parsing built-in), `django-fsm-2` (not `django-fsm`), and install WeasyPrint system deps + Cyrillic fonts in the runtime stage (not builder stage) of the multi-stage Dockerfile.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Django | 5.2 LTS | Web framework, ORM, Admin | LTS until 2028-04; explicit client requirement for "popular stack" |
| django-fsm-2 | 4.2.4 | Submission state machine | Drop-in replacement for archived django-fsm; confirmed Django 5.2 compatible |
| psycopg2-binary | 2.9.10 | PostgreSQL adapter | Binary for Docker simplicity; no C compilation needed |
| django-storages[s3] | 1.14.6 | MinIO/S3 file storage | `AWS_S3_ENDPOINT_URL` points to MinIO; handles two storage backends |
| boto3 | >=1.35 | S3 SDK used by django-storages | Required by django-storages[s3]; pin >=1.35 for Python 3.12 |
| django-environ | 2.x | `.env` file parsing with type casting | Built-in `DATABASE_URL`, `REDIS_URL`, `CACHE_URL` parsing; cleaner than os.getenv |
| WeasyPrint | 68.1 | HTML+CSS → PDF (used in Phase 6) | System deps installed in Phase 1 so Phase 6 has no infra surprises |
| gunicorn | 23.x | WSGI server | Standard prod WSGI; `--workers 2 --threads 2` for dev |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| celery | 5.6.3 | Task queue (worker + beat services) | PDF, delivery, notifications in later phases |
| django-celery-beat | 2.7.0 | Periodic tasks via DB | Beat service needs this; schedule visible in Admin |
| redis | 5.3.0 | Python Redis client | Used by Celery and aiogram FSM |
| django-cors-headers | 4.6.0 | CORS for React dev server | React at :5173 calling Django at :8000 |
| structlog | 25.5.0 | Structured logging | JSON in prod, colorized in dev |
| django-structlog | 10.0.0 | Adds request context to logs | Auto-adds request_id, user, IP |
| pytest | 8.x | Test runner | Standard |
| pytest-django | 4.x | Django test fixtures | `@pytest.mark.django_db` |
| factory-boy | 3.x | Test data factories | Model factories for tests |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| django-fsm-2 | Manual TextChoices + clean() | django-fsm-2 gives protected transitions, guards, and `can_proceed()` helper — use it |
| django-environ | python-decouple | python-decouple is more generic; django-environ has Django-specific URL parsers (`env.db()`, `env.cache()`). Prefer django-environ for this project |
| django-environ | os.getenv | os.getenv has no type casting, no URL parsing, no validation on startup |
| psycopg2-binary | psycopg (v3) | psycopg v3 is excellent but psycopg2-binary has wider tutorial coverage for a "popular stack" requirement |

**Installation (backend):**

```bash
# Run inside backend/ directory
poetry add django==5.2 django-fsm-2==4.2.4 psycopg2-binary==2.9.10 \
  "django-storages[s3]==1.14.6" "boto3>=1.35" django-environ==2.0 \
  WeasyPrint==68.1 gunicorn==23.0.0 celery==5.6.3 django-celery-beat==2.7.0 \
  redis==5.3.0 django-cors-headers==4.6.0 structlog==25.5.0 django-structlog==10.0.0

poetry add --group dev pytest==8.x pytest-django==4.x factory-boy==3.x ruff mypy django-debug-toolbar
poetry add --group prod gunicorn==23.0.0
```

---

## Architecture Patterns

### Recommended Project Structure

```
baqsy-system/
├── backend/
│   ├── baqsy/
│   │   ├── settings/
│   │   │   ├── base.py      # shared settings
│   │   │   ├── dev.py       # DEBUG=True, console email, local MinIO
│   │   │   └── prod.py      # DEBUG=False, S3/MinIO, Sentry stub
│   │   ├── urls.py
│   │   ├── celery.py
│   │   └── asgi.py / wsgi.py
│   ├── apps/
│   │   ├── core/            # TimestampedModel, UUIDModel, mixins
│   │   ├── accounts/        # BaseUser (AbstractBaseUser), ClientProfile
│   │   ├── industries/      # Industry, QuestionnaireTemplate, Question
│   │   ├── submissions/     # Submission (FSM), Answer
│   │   ├── payments/        # Tariff, Payment
│   │   ├── reports/         # AuditReport
│   │   ├── delivery/        # DeliveryLog
│   │   └── content/         # ContentBlock
│   ├── manage.py
│   ├── pyproject.toml
│   └── Dockerfile
├── bot/
│   ├── main.py
│   ├── handlers/
│   ├── states/
│   ├── services/
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/                # empty placeholder, Phase 5
├── docker/
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   ├── nginx.conf
│   ├── entrypoint.sh
│   └── postgres-backup.sh
├── .env.example
├── .gitignore
└── README.md
```

### Pattern 1: Multi-Stage Dockerfile (backend)

**What:** Builder stage installs Python dependencies via Poetry into an in-project `.venv`. Runtime stage copies only the `.venv` and adds system packages + fonts. This keeps the final image lean and separates build tools from runtime.

**Critical rule:** WeasyPrint system libraries and Cyrillic fonts must be in the **runtime** stage (where WeasyPrint actually executes), not just the builder stage.

```dockerfile
# backend/Dockerfile
# syntax=docker/dockerfile:1

## Stage 1: Builder — installs Python deps via Poetry
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

RUN pip install "poetry==$POETRY_VERSION"

WORKDIR $PYSETUP_PATH
COPY pyproject.toml poetry.lock ./

# --only main = no dev/prod extras; change to --without dev for prod
RUN --mount=type=cache,target=/root/.cache/pypoetry \
    poetry install --no-root --only main

## Stage 2: Runtime — python:3.12-slim + system libs + fonts + app code
FROM python:3.12-slim AS runtime

ENV VENV_PATH="/opt/pysetup/.venv" \
    PATH="/opt/pysetup/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# WeasyPrint system libs (Debian bookworm / python:3.12-slim base)
# Cyrillic fonts: Liberation (metric-compatible w/ Times/Arial), DejaVu, FreeFont
RUN apt-get update && apt-get install -y --no-install-recommends \
    # WeasyPrint required libs
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libharfbuzz-subset0 \
    # Cyrillic font coverage
    fonts-liberation \
    fonts-dejavu-core \
    fonts-freefont-ttf \
    # netcat for entrypoint wait loop
    netcat-openbsd \
    # MinIO client for backup script
    curl \
    && fc-cache -f \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -g 1001 baqsy && useradd -u 1001 -g baqsy -m appuser

WORKDIR /app

# Copy venv from builder
COPY --from=builder --chown=appuser:baqsy /opt/pysetup/.venv /opt/pysetup/.venv

# Copy app code
COPY --chown=appuser:baqsy . .

USER appuser

ENTRYPOINT ["/app/../docker/entrypoint.sh"]
```

**Note on Roboto:** `fonts-roboto` is not available in Debian bookworm minimal repos. Either use `fonts-freefont-ttf` as a substitute for generic sans-serif or bundle Roboto as project static files in `backend/static/fonts/` and reference via `@font-face` with absolute path in CSS — the latter gives exact brand rendering.

### Pattern 2: Docker Compose Healthchecks

**What:** Every service has a `healthcheck`. Dependent services use `condition: service_healthy`. The `web` service runs migrations; all other services wait for `web` to be healthy before starting.

```yaml
# docker/docker-compose.yml (key excerpts)
version: "3.9"

services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: baqsy
      POSTGRES_USER: baqsy
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      LANG: ru_RU.UTF-8
      LC_ALL: ru_RU.UTF-8
    volumes:
      - pg_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U baqsy -d baqsy"]
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
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY}
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"
    healthcheck:
      # mc is bundled in the minio image; curl is NOT available
      test: ["CMD", "mc", "ready", "local"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s

  web:
    build:
      context: ./backend
      dockerfile: Dockerfile
    env_file: .env
    volumes:
      - static_files:/app/staticfiles
      - media_files:/app/media
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
      start_period: 30s   # migrations take time on fresh DB

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A baqsy worker -Q default --pool=prefork --concurrency=2 --max-tasks-per-child=5
    env_file: .env
    depends_on:
      web:
        condition: service_healthy   # wait for migrations to complete

  beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A baqsy beat --scheduler django_celery_beat.schedulers:DatabaseScheduler
    env_file: .env
    depends_on:
      web:
        condition: service_healthy

  bot:
    build:
      context: ./bot
      dockerfile: Dockerfile
    env_file: .env
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
      - ./docker/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - static_files:/usr/share/nginx/html/static:ro
    depends_on:
      - web

volumes:
  pg_data:
  redis_data:
  minio_data:
  static_files:
  media_files:
```

**Why `mc ready local` for MinIO:** The MinIO Docker image does NOT include `curl`. GitHub issue #18389 confirmed this. The `mc` (MinIO Client) IS bundled in the MinIO image and `mc ready local` checks server readiness. The alias `local` is pre-configured automatically by MinIO for the local instance.

### Pattern 3: entrypoint.sh (web service)

**What:** Waits for dependencies (belt-and-suspenders alongside healthchecks), runs migrations once, creates MinIO bucket, runs collectstatic, then starts gunicorn. Only `web` runs migrations.

```bash
#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
until nc -z db 5432; do sleep 1; done

echo "Waiting for Redis..."
until nc -z redis 6379; do sleep 1; done

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Creating MinIO bucket..."
python manage.py ensure_bucket || true  # idempotent management command

echo "Starting gunicorn..."
exec gunicorn baqsy.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers ${GUNICORN_WORKERS:-2} \
  --threads ${GUNICORN_THREADS:-2} \
  --timeout 120
```

**Note on MinIO bucket creation:** A simple management command `ensure_bucket` that calls `boto3.client().create_bucket()` with `if_not_exists` is cleaner than running the `mc` CLI in entrypoint. The command checks existence before creating, making it idempotent.

### Pattern 4: Custom User Model (BaseUser)

**What:** Django requires `AUTH_USER_MODEL` to be set from day 1. Changing it after migrations exist is extremely painful. The `BaseUser` uses email as the `USERNAME_FIELD`.

```python
# apps/accounts/models.py
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class BaseUserManager(BaseUserManager):
    def create_user(self, email: str, password: str = None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class BaseUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = BaseUserManager()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.email
```

```python
# baqsy/settings/base.py
AUTH_USER_MODEL = "accounts.BaseUser"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
```

**Critical:** Set `AUTH_USER_MODEL` before running `migrate` for the first time. It cannot be changed after `0001_initial` migrations exist without squashing or recreating the DB.

### Pattern 5: QuestionnaireTemplate Versioning

**What:** Partial unique index ensures at most one active template per industry. `create_new_version` classmethod atomically creates new version and deactivates old.

```python
# apps/industries/models.py
from django.db import models, transaction
from django.db.models import Q, UniqueConstraint
from apps.core.models import TimestampedModel


class Industry(TimestampedModel):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class QuestionnaireTemplate(TimestampedModel):
    industry = models.ForeignKey(
        Industry, on_delete=models.PROTECT, related_name="templates"
    )
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=False)
    name = models.CharField(max_length=255)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("industry", "version")]
        constraints = [
            UniqueConstraint(
                fields=["industry"],
                condition=Q(is_active=True),
                name="one_active_template_per_industry",
            )
        ]
        indexes = [
            models.Index(fields=["industry", "is_active"]),
        ]

    @classmethod
    def create_new_version(cls, industry_id: int, name: str) -> "QuestionnaireTemplate":
        """
        Create new version atomically. Deactivates old active template.
        Returns the new (inactive) template ready for question population.
        Caller must set is_active=True after populating questions.
        """
        with transaction.atomic():
            current = cls.objects.filter(
                industry_id=industry_id, is_active=True
            ).select_for_update().first()
            new_version = (current.version + 1) if current else 1
            new_tmpl = cls.objects.create(
                industry_id=industry_id,
                version=new_version,
                is_active=False,  # caller activates after adding questions
                name=name,
            )
            if current:
                current.is_active = False
                current.save(update_fields=["is_active"])
            return new_tmpl

    def activate(self):
        """Activate this template, deactivating any currently active one."""
        with transaction.atomic():
            QuestionnaireTemplate.objects.filter(
                industry=self.industry, is_active=True
            ).exclude(pk=self.pk).update(is_active=False)
            self.is_active = True
            self.save(update_fields=["is_active", "published_at"])

    def __str__(self):
        return f"{self.industry.name} v{self.version} ({'active' if self.is_active else 'inactive'})"
```

**Migration for the partial unique index** (auto-generated by Django, but worth knowing what it produces):

```python
# In the generated 0001_initial.py — Django translates UniqueConstraint with condition to:
# migrations.AddConstraint(
#     model_name='questionnairetemplate',
#     constraint=models.UniqueConstraint(
#         condition=models.Q(is_active=True),
#         fields=['industry'],
#         name='one_active_template_per_industry'
#     ),
# )
```

Django 5.2 fully supports `UniqueConstraint` with `Q` conditions — this generates a PostgreSQL partial UNIQUE INDEX. No raw SQL needed.

### Pattern 6: Submission.template_id Immutability

**What:** Override `save()` to raise `ValidationError` if `template_id` is changed on an existing record. Check by comparing against DB state in `__init__`.

```python
# apps/submissions/models.py
import uuid
from django.core.exceptions import ValidationError
from django.db import models
from django_fsm import FSMField, transition as fsm_transition
from apps.core.models import TimestampedModel, UUIDModel
from apps.industries.models import QuestionnaireTemplate
from apps.accounts.models import ClientProfile


class SubmissionStatus(models.TextChoices):
    CREATED = "created", "Created"
    IN_PROGRESS_BASIC = "in_progress_basic", "In Progress (Basic)"
    PAID = "paid", "Paid"
    IN_PROGRESS_FULL = "in_progress_full", "In Progress (Full)"
    COMPLETED = "completed", "Completed"
    UNDER_AUDIT = "under_audit", "Under Audit"
    DELIVERED = "delivered", "Delivered"


class Submission(UUIDModel, TimestampedModel):
    client = models.ForeignKey(
        ClientProfile, on_delete=models.PROTECT, related_name="submissions"
    )
    template = models.ForeignKey(
        QuestionnaireTemplate,
        on_delete=models.PROTECT,
        related_name="submissions",
    )
    status = FSMField(
        default=SubmissionStatus.CREATED,
        choices=SubmissionStatus.choices,
        protected=True,  # prevents direct assignment; use transition methods
    )
    completed_at = models.DateTimeField(null=True, blank=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Track original template_id to detect mutations
        self._original_template_id = self.template_id

    def save(self, *args, **kwargs):
        # DATA-13: Submission.template_id is immutable after creation
        if self.pk is not None and self.template_id != self._original_template_id:
            raise ValidationError(
                "Submission.template_id cannot be changed after creation."
            )
        super().save(*args, **kwargs)
        self._original_template_id = self.template_id  # update after successful save

    # FSM transitions
    @fsm_transition(field=status, source=SubmissionStatus.CREATED, target=SubmissionStatus.IN_PROGRESS_BASIC)
    def start_basic(self):
        pass

    @fsm_transition(field=status, source=SubmissionStatus.IN_PROGRESS_BASIC, target=SubmissionStatus.PAID)
    def mark_paid(self):
        pass

    @fsm_transition(field=status, source=SubmissionStatus.PAID, target=SubmissionStatus.IN_PROGRESS_FULL)
    def start_full(self):
        pass

    @fsm_transition(field=status, source=SubmissionStatus.IN_PROGRESS_FULL, target=SubmissionStatus.COMPLETED)
    def complete(self):
        from django.utils import timezone
        self.completed_at = timezone.now()

    @fsm_transition(field=status, source=SubmissionStatus.COMPLETED, target=SubmissionStatus.UNDER_AUDIT)
    def send_to_audit(self):
        pass

    @fsm_transition(field=status, source=SubmissionStatus.UNDER_AUDIT, target=SubmissionStatus.DELIVERED)
    def deliver(self):
        pass
```

**Important:** `django-fsm-2` uses `FSMModelMixin` or `FSMField(protected=True)` to prevent direct `submission.status = "paid"` assignment. The transition method is the only valid way to change state.

**Import path:** `from django_fsm import FSMField, transition` — the package name is `django-fsm-2` in pyproject.toml but the import name is still `django_fsm` (drop-in replacement).

### Pattern 7: MinIO Storage Configuration (django-storages)

**What:** Two custom storage classes inheriting `S3Boto3Storage`. MinIO requires `path` addressing style (not virtual-host) and `s3v4` signature.

```python
# baqsy/settings/base.py
import environ

env = environ.Env()
environ.Env.read_env()  # reads .env file

# MinIO / S3-compatible storage
AWS_ACCESS_KEY_ID = env("MINIO_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = env("MINIO_SECRET_KEY")
AWS_STORAGE_BUCKET_NAME = env("MINIO_BUCKET", default="baqsy")
AWS_S3_ENDPOINT_URL = env("MINIO_ENDPOINT_URL", default="http://minio:9000")
AWS_S3_ADDRESSING_STYLE = "path"          # MinIO requires path-style, not virtual-host
AWS_S3_SIGNATURE_VERSION = "s3v4"         # default; explicit for clarity
AWS_DEFAULT_ACL = "private"              # bucket is private; use presigned URLs
AWS_S3_FILE_OVERWRITE = False
AWS_QUERYSTRING_AUTH = True              # generate presigned URLs
AWS_S3_PRESIGNED_EXPIRY = 60 * 60 * 24 * 7  # 7 days — PDF links must survive
```

```python
# apps/reports/storage.py
from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    """For client-uploaded files (future v2 feature)."""
    location = "uploads"
    default_acl = "private"


class ReportStorage(S3Boto3Storage):
    """For generated PDF audit reports."""
    location = "pdfs"
    default_acl = "private"
    file_overwrite = False  # unique filenames always
```

**Key MinIO gotcha:** MinIO in Docker is accessed at `http://minio:9000` (internal Docker network). For presigned URLs served to external clients (bot, WhatsApp), the URL must use the public-facing hostname. In dev, use `AWS_S3_CUSTOM_DOMAIN` or manually replace the host when constructing public URLs.

### Pattern 8: django-environ Configuration

**Why django-environ over python-decouple:**
- `env.db("DATABASE_URL")` parses `postgres://user:pass@host/db` into Django `DATABASES` dict in one line
- `env.cache("REDIS_URL")` does the same for `CACHES`
- Type casting (bool, int, list) built-in
- Raises `ImproperlyConfigured` at startup if required vars are missing — fail-fast

```python
# baqsy/settings/base.py
import environ

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
)

# Read .env file (in dev); in prod, vars come from Docker env
environ.Env.read_env(env.path("BASE_DIR")(".env"))

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

DATABASES = {"default": env.db("DATABASE_URL")}

CACHES = {"default": env.cache("REDIS_URL")}

CELERY_BROKER_URL = env("CELERY_BROKER_URL")  # redis://redis:6379/0
```

### Pattern 9: Seed Command Idempotency

**What:** `get_or_create()` ensures re-runs don't duplicate data. Superuser creation checks `BaseUser.objects.filter(email=...).exists()` before calling `create_superuser`.

```python
# apps/core/management/commands/seed_initial.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.industries.models import Industry
from apps.payments.models import Tariff
import os

User = get_user_model()


class Command(BaseCommand):
    help = "Seed initial data: superuser, industries, tariffs"

    def handle(self, *args, **kwargs):
        self._create_superuser()
        self._create_industries()
        self._create_tariffs()
        self.stdout.write(self.style.SUCCESS("Seed complete."))

    def _create_superuser(self):
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@baqsy.kz")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")
        if not User.objects.filter(email=email).exists():
            User.objects.create_superuser(email=email, password=password)
            self.stdout.write(f"  Created superuser: {email}")
        else:
            self.stdout.write(f"  Superuser already exists: {email}")

    def _create_industries(self):
        names = ["Ритейл", "IT/Digital", "Производство", "Услуги", "F&B"]
        for name in names:
            industry, created = Industry.objects.get_or_create(
                name=name,
                defaults={"slug": name.lower().replace("/", "-").replace(" ", "-"), "is_active": True}
            )
            if created:
                self.stdout.write(f"  Created industry: {name}")

    def _create_tariffs(self):
        tariffs = [
            {"code": "ashide_1", "title": "Ashıde 1", "price_kzt": 45000, "is_active": True},
            {"code": "ashide_2", "title": "Ashıde 2", "price_kzt": 135000, "is_active": True},
            {"code": "upsell",   "title": "Upsell",   "price_kzt": 90000,  "is_active": True},
        ]
        for t in tariffs:
            obj, created = Tariff.objects.get_or_create(
                code=t["code"], defaults={k: v for k, v in t.items() if k != "code"}
            )
            if created:
                self.stdout.write(f"  Created tariff: {t['title']}")
```

### Anti-Patterns to Avoid

- **Running `migrate` in both `web` and `worker` entrypoints:** Django's `django_migrations` lock table can deadlock. Only `web` runs migrations; `worker`/`beat`/`bot` wait for `web` to be healthy.
- **Using `django-fsm` (original):** Package archived October 2025. Install `django-fsm-2` instead. Import path stays `from django_fsm import ...`.
- **Setting `status = "paid"` directly on Submission:** `FSMField(protected=True)` raises `AttributeError`. Always call transition methods.
- **Editing QuestionnaireTemplate questions in-place:** Must always create new version. See Pattern 5.
- **Generating presigned URLs before MinIO bucket exists:** The entrypoint `ensure_bucket` command must run before gunicorn starts.
- **Missing `fc-cache -f` after font install:** Without font cache rebuild, WeasyPrint uses Fontconfig which won't find newly installed fonts.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Partial unique index (one active template per industry) | Raw SQL UNIQUE INDEX migration | `UniqueConstraint(condition=Q(is_active=True), ...)` | Django ORM generates correct PostgreSQL partial index |
| State machine transitions | `if status == 'created': status = 'paid'` | `django-fsm-2` `@transition` + `FSMField` | Guards, `can_proceed()`, protected field assignment, audit log extension available |
| .env file parsing | `os.environ.get()` manually | `django-environ` | Type casting, URL parsing (`env.db()`), fail-fast on missing vars |
| S3/MinIO file storage | boto3 calls in every view | `django-storages[s3]` `S3Boto3Storage` subclasses | Handles presigned URLs, streaming, ACLs, Django file field integration |
| Migration race between services | `sleep 10` in entrypoint | Docker Compose `healthcheck` + `depends_on: condition: service_healthy` | Reliable, Docker-native; no fragile sleep timers |
| MinIO readiness check | `curl localhost:9000` | `mc ready local` | `curl` not available in minio image; `mc` is bundled |

---

## Common Pitfalls

### Pitfall 1: django-fsm is Archived — Use django-fsm-2

**What goes wrong:** Developer installs `django-fsm` from PyPI. The package exists but was archived in October 2025 and receives no updates. On Django 5.2 it may work today but will break as Django evolves.

**How to avoid:** Install `django-fsm-2==4.2.4`. Import path is identical: `from django_fsm import FSMField, transition`. It is a certified drop-in replacement maintained by django-commons.

**Confidence:** HIGH — verified from PyPI and GitHub django-commons/django-fsm-2.

### Pitfall 2: WeasyPrint Cyrillic Fonts in Docker

**What goes wrong:** `python:3.12-slim` has zero fonts. WeasyPrint generates a PDF but Cyrillic characters render as boxes (`.notdef` glyphs). The log says `No glyph for character U+0410`.

**How to avoid:**
1. Install font packages in the Dockerfile runtime stage: `fonts-liberation fonts-dejavu-core fonts-freefont-ttf`
2. Run `fc-cache -f` after font installation
3. For guaranteed brand fonts, bundle exact font files in `backend/static/fonts/` and use `@font-face` with `file:///app/static/fonts/Font.ttf` path in CSS

**Warning signs:** Generated PDF byte size is unusually small; `pdftotext output.pdf -` returns empty/garbled Cyrillic.

### Pitfall 3: Migration Race in Docker Compose

**What goes wrong:** `web` and `worker` start simultaneously. Both call `migrate`. `django_migrations` table deadlocks or migrations run twice.

**How to avoid:** Only `web` runs `manage.py migrate` in entrypoint. `worker`, `beat`, `bot` have `depends_on: web: condition: service_healthy`. The `web` healthcheck must return healthy only AFTER migrations complete (i.e., after gunicorn starts on port 8000).

### Pitfall 4: MinIO mc Healthcheck Alias

**What goes wrong:** The `minio/minio` image does NOT have `curl`. Healthcheck using `curl http://localhost:9000/minio/health/live` fails silently with "executable not found", marking the container healthy immediately (Docker ignores the error after retries exhaust) or never healthy depending on Docker version.

**How to avoid:** Use `test: ["CMD", "mc", "ready", "local"]`. The `mc` binary IS bundled in the MinIO image, and the `local` alias is pre-configured for `http://localhost:9000`.

### Pitfall 5: AUTH_USER_MODEL Set Too Late

**What goes wrong:** Developer runs `migrate` with the default `auth.User`, then tries to swap to custom `accounts.BaseUser`. Django requires squashing or dropping the entire database.

**How to avoid:** Set `AUTH_USER_MODEL = "accounts.BaseUser"` in `settings/base.py` BEFORE any `migrate` call. The `accounts` app must be in `INSTALLED_APPS` before `makemigrations` runs.

### Pitfall 6: Submission template_id Check via __init__

**What goes wrong:** `save()` override checks `self.template_id != original` but `__init__` is not overridden, so `_original_template_id` doesn't exist on fresh instances loaded from DB.

**How to avoid:** Always override `__init__` alongside `save()` when using this immutability pattern (see Pattern 6 code above). The `__init__` stores `self._original_template_id = self.template_id` immediately after calling `super().__init__()`.

### Pitfall 7: PostgreSQL locale for Cyrillic sorting

**What goes wrong:** Default `POSTGRES_INITDB_ARGS` doesn't set locale. Cyrillic text sorts incorrectly (ASCII sort order instead of locale-aware collation).

**How to avoid:** In docker-compose.yml, set environment variables:
```yaml
LANG: ru_RU.UTF-8
LC_ALL: ru_RU.UTF-8
POSTGRES_INITDB_ARGS: "--locale=ru_RU.UTF-8 --encoding=UTF8"
```
These must be set before the PostgreSQL data directory is initialized (first `docker-compose up`). Changing them later requires recreating the volume.

---

## Code Examples

### Core Abstract Models

```python
# apps/core/models.py
import uuid
from django.db import models


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True
```

### Answer Model with JSONB

```python
# apps/submissions/models.py (Answer)
class Answer(TimestampedModel):
    submission = models.ForeignKey(
        Submission, on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(
        "industries.Question", on_delete=models.PROTECT, related_name="answers"
    )
    value = models.JSONField()   # PostgreSQL JSONB; schema varies by field_type
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("submission", "question")]
        indexes = [models.Index(fields=["submission", "question"])]
```

### Question Model

```python
# apps/industries/models.py
class Question(TimestampedModel):
    class FieldType(models.TextChoices):
        TEXT = "text", "Text"
        NUMBER = "number", "Number"
        CHOICE = "choice", "Single Choice"
        MULTICHOICE = "multichoice", "Multiple Choice"

    class Block(models.TextChoices):
        A = "A", "Block A (Basic)"
        B = "B", "Block B (Core)"
        C = "C", "Block C (Deep)"

    template = models.ForeignKey(
        QuestionnaireTemplate, on_delete=models.CASCADE, related_name="questions"
    )
    order = models.PositiveSmallIntegerField()
    text = models.TextField()
    field_type = models.CharField(max_length=20, choices=FieldType.choices)
    options = models.JSONField(default=dict, blank=True)  # for choice/multichoice
    required = models.BooleanField(default=True)
    block = models.CharField(max_length=1, choices=Block.choices, default=Block.A)

    class Meta:
        unique_together = [("template", "order")]
        ordering = ["order"]
```

### Celery Setup

```python
# baqsy/celery.py
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "baqsy.settings.dev")

app = Celery("baqsy")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

```python
# baqsy/settings/base.py (Celery config)
CELERY_BROKER_URL = env("CELERY_BROKER_URL")          # redis://redis:6379/0
CELERY_RESULT_BACKEND = env("CELERY_BROKER_URL")
CELERY_BROKER_TRANSPORT_OPTIONS = {
    "visibility_timeout": 43200,  # 12 hours — prevents task duplication on long tasks
}
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = "UTC"
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `django-fsm` (original) | `django-fsm-2` (maintained fork) | Oct 2025 (original archived) | Must use `django-fsm-2`; import path unchanged |
| `aioredis` for async Redis | `redis` package directly | aiogram 3.x switch | `pip install redis`, not `aioredis` |
| MinIO healthcheck via `curl` | `mc ready local` | MinIO removed curl from image (issue #18389) | Use `["CMD", "mc", "ready", "local"]` in healthcheck |
| `wkhtmltopdf` for PDF | WeasyPrint | wkhtmltopdf abandoned ~2023 | WeasyPrint is the current standard for HTML→PDF |
| `pip install` in Dockerfile | Poetry multi-stage (builder stage) | 2023-2025 mainstream | Smaller images, reproducible builds via `poetry.lock` |
| `CRA (create-react-app)` | Vite | Meta abandoned CRA 2023 | Vite for all new React projects |

**Deprecated/outdated:**
- `django-fsm` (pip package): archived October 2025 — replace with `django-fsm-2`
- `aioredis`: deprecated, aiogram 3 switched to `redis` package
- `wkhtmltopdf`: abandoned, no updates since 2023

---

## Open Questions

1. **Roboto font in Docker**
   - What we know: `fonts-roboto` may not be in Debian bookworm apt repos for slim image
   - What's unclear: whether the project's brand actually requires Roboto specifically or can use Liberation/DejaVu as web-safe substitutes
   - Recommendation: bundle the exact brand fonts as static files in `backend/static/fonts/` and reference via `@font-face` with absolute filesystem path — this is the only approach that guarantees pixel-identical rendering regardless of server environment

2. **`pg_trgm` extension creation**
   - What we know: `pg_trgm` must be enabled via `CREATE EXTENSION IF NOT EXISTS pg_trgm`
   - What's unclear: whether to enable in a Django migration or in PostgreSQL init script
   - Recommendation: add a Django migration in `apps/core` with `migrations.RunSQL("CREATE EXTENSION IF NOT EXISTS pg_trgm;")` — this is version-controlled and runs automatically

3. **MinIO bucket public URL for external access**
   - What we know: presigned URLs are generated with `http://minio:9000/...` (internal Docker hostname)
   - What's unclear: external clients (bot, WhatsApp) need public-facing URLs
   - Recommendation: set `AWS_S3_ENDPOINT_URL` to internal (`http://minio:9000`) for uploads, and configure `AWS_S3_CUSTOM_DOMAIN` or rewrite URLs when serving to external clients; details can be deferred to Phase 6 (PDF delivery)

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.x + pytest-django 4.x |
| Config file | `backend/pytest.ini` or `backend/pyproject.toml` `[tool.pytest.ini_options]` — created in Wave 0 |
| Quick run command | `docker-compose exec web pytest apps/ -x -q` |
| Full suite command | `docker-compose exec web pytest apps/ --cov=apps --cov-report=term-missing` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INFRA-01 | All 8 services start and pass healthchecks | smoke | `docker-compose up -d && docker-compose ps` (assert all healthy) | Wave 0 |
| INFRA-02 | `docker-compose up` requires no extra steps | smoke | manual + `docker-compose logs web` assert no errors | manual |
| INFRA-03 | Secrets not in repo; `.env.example` present | smoke | `grep -r "SECRET_KEY" . --include="*.py" -l` returns only `.env.example` | manual |
| INFRA-04 | Migrations applied at web start | smoke | `docker-compose logs web` assert "Running migrations" | manual |
| INFRA-05 | Docker image has Cyrillic fonts | unit | `docker-compose exec web fc-list | grep -i liberation` | Wave 0 |
| INFRA-06 | Backup script creates file in MinIO | smoke | `docker-compose exec web bash docker/postgres-backup.sh && mc ls local/baqsy/backups/` | manual |
| INFRA-07 | README has deployment section | manual | Human review | manual |
| DATA-01 | Industry CRUD, unique name | unit | `pytest apps/industries/tests/test_models.py::TestIndustry -x` | Wave 0 |
| DATA-02 | QuestionnaireTemplate created with correct fields | unit | `pytest apps/industries/tests/test_models.py::TestQuestionnaireTemplate -x` | Wave 0 |
| DATA-12 | One active template per industry (DB constraint) | unit | `pytest apps/industries/tests/test_versioning.py::test_one_active_constraint -x` | Wave 0 |
| DATA-12 | create_new_version deactivates old atomically | unit | `pytest apps/industries/tests/test_versioning.py::test_create_new_version -x` | Wave 0 |
| DATA-13 | Submission.template_id immutable after creation | unit | `pytest apps/submissions/tests/test_models.py::test_template_immutable -x` | Wave 0 |
| DATA-05 | Submission FSM transitions in correct order | unit | `pytest apps/submissions/tests/test_fsm.py -x` | Wave 0 |
| DATA-05 | Submission FSM rejects invalid transitions | unit | `pytest apps/submissions/tests/test_fsm.py::test_invalid_transition -x` | Wave 0 |
| DATA-06 | Answer.value stores JSONB correctly | unit | `pytest apps/submissions/tests/test_models.py::TestAnswer -x` | Wave 0 |
| DATA-08 | Payment.transaction_id is unique | unit | `pytest apps/payments/tests/test_models.py::test_transaction_id_unique -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `docker-compose exec web pytest apps/ -x -q --tb=short`
- **Per wave merge:** `docker-compose exec web pytest apps/ --cov=apps --cov-report=term-missing`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps (files that do not yet exist)

- [ ] `backend/pytest.ini` — pytest config with `DJANGO_SETTINGS_MODULE=baqsy.settings.dev`
- [ ] `backend/apps/industries/tests/__init__.py`
- [ ] `backend/apps/industries/tests/test_models.py` — covers DATA-01, DATA-02
- [ ] `backend/apps/industries/tests/test_versioning.py` — covers DATA-12
- [ ] `backend/apps/submissions/tests/__init__.py`
- [ ] `backend/apps/submissions/tests/test_models.py` — covers DATA-05, DATA-06, DATA-13
- [ ] `backend/apps/submissions/tests/test_fsm.py` — covers DATA-05 FSM transitions
- [ ] `backend/apps/payments/tests/__init__.py`
- [ ] `backend/apps/payments/tests/test_models.py` — covers DATA-08
- [ ] `backend/conftest.py` — shared pytest fixtures (DB setup, factory-boy factories)

---

## Sources

### Primary (HIGH confidence)

- [django-fsm-2 PyPI — v4.2.4](https://pypi.org/project/django-fsm-2/) — version, Django 5.2 compatibility, drop-in status confirmed
- [django-commons/django-fsm-2 README](https://github.com/django-commons/django-fsm-2/blob/main/README.md) — FSMField, @transition decorator, FSMModelMixin pattern
- [WeasyPrint 68.1 official docs — First Steps](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html) — exact apt packages: `libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0`
- [MinIO official docker-compose.yaml](https://github.com/minio/minio/blob/master/docs/orchestration/docker-compose/docker-compose.yaml) — `mc ready local` healthcheck pattern
- [MinIO GitHub issue #18389](https://github.com/minio/minio/issues/18389) — confirms curl removed from MinIO image
- [Django 5.2 docs — Constraints reference](https://django.readthedocs.io/en/stable/ref/models/constraints.html) — UniqueConstraint with Q condition
- [Django 5.2 docs — AUTH_USER_MODEL customization](https://docs.djangoproject.com/en/5.2/topics/auth/customizing/) — AbstractBaseUser pattern
- [depot.dev — Optimal Poetry Dockerfile](https://depot.dev/docs/container-builds/optimal-dockerfiles/python-poetry-dockerfile) — multi-stage Poetry builder pattern
- [STACK.md](../../../research/STACK.md) — all library versions pre-verified
- [ARCHITECTURE.md](../../../research/ARCHITECTURE.md) — component patterns, Redis DB isolation
- [PITFALLS.md](../../../research/PITFALLS.md) — migration race (Pitfall 9), WeasyPrint fonts (Pitfall 4), template versioning (Pitfall 3)

### Secondary (MEDIUM confidence)

- [django-storages S3 docs 1.14.6](https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html) — `AWS_S3_ADDRESSING_STYLE = "path"` for MinIO, `AWS_S3_SIGNATURE_VERSION = "s3v4"`
- [Docker Compose healthcheck guide (2025)](https://www.tvaidyan.com/2025/02/13/health-checks-in-docker-compose-a-practical-guide/) — `depends_on: condition: service_healthy` pattern
- [django-environ vs python-decouple comparison](https://pypy-django.github.io/blog/2024/07/06/comparing-django-environ-python-decouple-and-python-dotenv/) — recommendation rationale

### Tertiary (LOW confidence)

- None — all critical claims are backed by primary sources.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions verified from PyPI and official sources; django-fsm-2 migration verified
- Architecture: HIGH — patterns sourced from existing ARCHITECTURE.md (pre-verified research) + official docs
- Pitfalls: HIGH — sources from existing PITFALLS.md (pre-verified) + new finding: django-fsm archival
- Validation architecture: MEDIUM — test structure is standard pytest-django pattern; exact test names are provisional

**Research date:** 2026-04-15
**Valid until:** 2026-07-15 (90 days; stable stack, no fast-moving dependencies)
