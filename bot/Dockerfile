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
