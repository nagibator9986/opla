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

# Belt-and-suspenders: install critical newer deps with pip so we don't rely on
# Poetry's resolver inside the cache layer. openai 1.50 (what pyproject used to
# pin) is incompatible with httpx 0.28+ (drops `proxies` kwarg) — use 1.60+.
# Pillow is needed for Django ImageField (Case.logo, Case.cover_image).
RUN /opt/pysetup/.venv/bin/pip install --no-cache-dir \
    "openai>=1.60,<3" \
    "Pillow>=10.4"

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
