# Phase 1: Infrastructure & Data Model - Context

**Gathered:** 2026-04-15
**Status:** Ready for planning
**Mode:** auto (YOLO)

<domain>
## Phase Boundary

Поднять полный скелет проекта: Docker Compose со всеми 8 сервисами (web, bot, worker, beat, db, redis, nginx, minio), Django-проект с модульной структурой apps/, все 13 моделей данных с миграциями, инварианты версионирования шаблонов и неизменяемости `Submission.template_id`, seed-скрипт с минимальным набором отраслей, README с инструкцией развёртывания.

**Не делаем в этой фазе:** REST API endpoints (Phase 2), бизнес-логика бота (Phase 3), вебхуки оплаты (Phase 4), React (Phase 5), PDF (Phase 6), админка сверх Django Admin по умолчанию (Phase 7), CI/TLS/Sentry (Phase 8).

Требования: INFRA-01..07, DATA-01..13 (20 штук).

</domain>

<decisions>
## Implementation Decisions

### Python & пакетный менеджер
- **Poetry 1.8+** для зависимостей (pyproject.toml + poetry.lock)
- Группы: `main`, `dev` (pytest, ruff, mypy, django-debug-toolbar), `prod` (gunicorn)
- Python 3.12 slim-образ в Docker
- Отдельные pyproject для `backend/` и `bot/` — у бота свои зависимости (aiogram, httpx), не тянет Django

### Структура репозитория
```
baqsy-system/
├── backend/
│   ├── baqsy/           # settings, urls, asgi, wsgi, celery
│   │   ├── settings/    # base.py, dev.py, prod.py
│   │   ├── urls.py
│   │   ├── celery.py
│   │   └── asgi.py
│   ├── apps/
│   │   ├── core/        # base models (TimestampedModel, UUIDModel), mixins
│   │   ├── accounts/    # ClientProfile, BaseUser (custom), auth
│   │   ├── industries/  # Industry, QuestionnaireTemplate, Question
│   │   ├── submissions/ # Submission, Answer, FSM states
│   │   ├── payments/    # Tariff, Payment
│   │   ├── reports/     # AuditReport
│   │   ├── delivery/    # DeliveryLog
│   │   └── content/     # ContentBlock
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
├── frontend/            # создаётся в Phase 5 (пустая папка + placeholder)
├── docker/
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   ├── nginx.conf
│   ├── postgres-backup.sh
│   └── entrypoint.sh
├── .env.example
├── .gitignore
├── README.md
└── CLAUDE.md
```

### Settings split
- `backend/baqsy/settings/base.py` — общие настройки
- `settings/dev.py` — DEBUG=True, console email, local MinIO
- `settings/prod.py` — DEBUG=False, S3/MinIO, Sentry-hook (пустой, заполнится в Phase 8)
- `DJANGO_SETTINGS_MODULE` через `.env`

### Custom User model
- `apps.accounts.models.BaseUser` — наследник `AbstractBaseUser` с email-логином (для админа)
- `AUTH_USER_MODEL = "accounts.BaseUser"` с дня 1 (Django рекомендация — не менять потом)
- `ClientProfile` — отдельная модель для клиентов бота (не наследник User), связана по `telegram_id`
- Причина разделения: админы логинятся по email, клиенты идентифицируются по Telegram — разные модели аутентификации

### Core модели (apps/core)
- `TimestampedModel` — абстракт с `created_at`, `updated_at`
- `UUIDModel` — абстракт с `id = UUIDField(primary_key=True, default=uuid4)` для моделей, ID которых уходят во внешний мир (Submission, Payment)
- BigAutoField для внутренних моделей (Question, Answer)

### Submission state machine
- **Библиотека:** `django-fsm 2.8+` для защищённых переходов состояний
- **Состояния:** `created → in_progress_basic → paid → in_progress_full → completed → under_audit → delivered`
  - `created` — клиент стартовал онбординг
  - `in_progress_basic` — бот задаёт 5 базовых вопросов
  - `paid` — оплата прошла (может быть пропущено, если модель воронки «анкета до оплаты» — обсудим в Phase 4)
  - `in_progress_full` — бот задаёт глубокую анкету
  - `completed` — все обязательные ответы есть
  - `under_audit` — админ работает с заказом
  - `delivered` — PDF отправлен
- **Альтернатива, если django-fsm окажется несовместимой с Django 5.2:** вручную через `TextChoices` + проверки в `clean()`/`save()`. Решает researcher в Phase 1 research.

### Questionnaire versioning (КРИТИЧЕСКИЙ инвариант)
- `QuestionnaireTemplate` — поля `industry`, `version` (int), `is_active` (bool), `name`, `published_at`
- `unique_together = [("industry", "version")]`
- Частичный уникальный индекс: `UniqueConstraint(fields=["industry"], condition=Q(is_active=True), name="one_active_template_per_industry")`
- Метод `QuestionnaireTemplate.create_new_version(cls, old_template, changes)` — классметод, атомарно создаёт новую версию с клонированием вопросов и деактивирует старую
- **Вопросы НЕ редактируются in-place** — любое изменение создаёт новую версию
- `Submission.template_id` — FK на конкретную версию, не на «активную»
- `Submission.save()` переопределён: при попытке изменить `template_id` после первого сохранения кидает `ValidationError`

### Answer.value
- `JSONField` (PostgreSQL JSONB)
- Схема хранения зависит от `question.field_type`:
  - `text` → `{"text": "..."}`
  - `number` → `{"number": 42}`
  - `choice` → `{"choice": "option_key"}`
  - `multichoice` → `{"choices": ["a", "b"]}`
- Нормализация через сериализаторы в Phase 2

### Timezone
- `TIME_ZONE = "UTC"` и `USE_TZ = True` в БД
- Отображение в админке/боте/фронте — `Asia/Almaty` (UTC+5)
- Конверсия на уровне представления, не хранения

### PostgreSQL
- Версия **16** (stable, matches research)
- Extension `pg_trgm` для поиска в админке (будет задействовано в Phase 7)
- Локаль `ru_RU.UTF-8` для корректной сортировки кириллицы
- Отдельный пользователь БД с ограниченными правами (не superuser)

### Redis layout
- Образ: `redis:7-alpine`
- Database index isolation:
  - **db=0** — Celery broker + result backend
  - **db=1** — aiogram FSM storage
  - **db=2** — deep-link tokens (UUID → client_id, TTL 30 min)
  - **db=3** — rate limiting / django-ratelimit (Phase 8)
- `appendonly yes` в prod для durability (pitfalls research)
- В dev можно без AOF — быстрее рестарт

### MinIO
- Образ: `minio/minio:latest` с `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` из env
- Single bucket `baqsy` с префиксами:
  - `pdfs/{submission_id}/{timestamp}.pdf` — готовые отчёты
  - `uploads/{submission_id}/...` — если клиент прикрепляет файлы в ответах (v2)
  - `backups/db/{YYYY-MM-DD}.sql.gz` — дампы PG
- Доступ через `django-storages[s3]` с S3-совместимым endpoint
- `MediaStorage` и `ReportStorage` как две разных storage-класса
- Bucket создаётся автоматически entrypoint-скриптом web-контейнера

### Docker Compose
- Один файл `docker-compose.yml` для dev с overrides через `docker-compose.prod.yml`
- Сервисы и порты:
  - `web` — Django, внутренний 8000 (через nginx)
  - `bot` — aiogram worker, без внешних портов
  - `worker` — Celery, `--pool=prefork --max-tasks-per-child=5 --concurrency=2`
  - `beat` — Celery beat
  - `db` — PostgreSQL 16, внутренний 5432
  - `redis` — Redis 7, внутренний 6379
  - `minio` — MinIO, 9000 (API) + 9001 (console)
  - `nginx` — 80/443 наружу
- Volumes: `pg_data`, `redis_data`, `minio_data`, `static_files`, `media_files`
- Healthchecks для всех сервисов, `depends_on: condition: service_healthy`
- Сети: default bridge достаточно

### Dockerfiles
- `backend/Dockerfile` — multi-stage:
  - Stage 1 (builder): poetry install
  - Stage 2 (runtime): python:3.12-slim + системные пакеты для WeasyPrint (`libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 libharfbuzz0b`)
  - Шрифты: `fonts-liberation fonts-dejavu-core fonts-roboto` + `fc-cache -f`
- `bot/Dockerfile` — отдельный, минимальный (без WeasyPrint)
- `entrypoint.sh` — ждёт PG/Redis/MinIO через `nc`, затем `migrate` + `collectstatic` + запуск gunicorn

### Migrations strategy
- Одна миграция на app при создании моделей (`0001_initial.py`)
- Автоматический `migrate` в entrypoint web-контейнера
- Никаких ручных SQL, только Django migrations

### Seed data
- Management command `python manage.py seed_initial`:
  - Создаёт суперюзера из `DJANGO_SUPERUSER_EMAIL` / `DJANGO_SUPERUSER_PASSWORD`
  - Создаёт 5 отраслей: Ритейл, IT/Digital, Производство, Услуги, F&B
  - Создаёт по одному демо-шаблону на отрасль с минимальным набором вопросов (блок А — 5 базовых, блок Б — 1 содержательный, блок В — 3 глубоких) — просто чтобы было что протестировать
  - Создаёт 3 тарифа: Ashıde 1 (45000), Ashıde 2 (135000), Upsell (90000)
  - Идемпотентно (проверяет существование перед созданием)

### Env & secrets
- `.env.example` в репо с пустыми ключами и комментариями
- `.env` в `.gitignore`
- Читается через `django-environ` или `os.getenv` + валидация на старте
- Ключевые переменные:
  ```
  DJANGO_SETTINGS_MODULE=baqsy.settings.dev
  DJANGO_SECRET_KEY=
  DATABASE_URL=postgres://baqsy:baqsy@db:5432/baqsy
  REDIS_URL=redis://redis:6379
  CELERY_BROKER_URL=redis://redis:6379/0
  AIOGRAM_REDIS_URL=redis://redis:6379/1
  MINIO_ENDPOINT=minio:9000
  MINIO_ACCESS_KEY=
  MINIO_SECRET_KEY=
  MINIO_BUCKET=baqsy
  TELEGRAM_BOT_TOKEN=
  CLOUDPAYMENTS_PUBLIC_ID=
  CLOUDPAYMENTS_API_SECRET=
  WAZZUP24_API_KEY=
  WAZZUP24_CHANNEL_ID=
  ```

### Backups
- Скрипт `docker/postgres-backup.sh` делает `pg_dump | gzip` и кладёт в MinIO через `mc` CLI
- Запускается через отдельный контейнер `backup` с cron (в Phase 1 — ручной запуск, cron в Phase 8)
- Retention: 7 дней (реализовано в скрипте)

### README скелет для INFRA-07
- «Установите Docker Desktop»
- «Склонируйте репо»
- «Скопируйте `.env.example` → `.env` и заполните»
- «`docker-compose up -d`»
- «`docker-compose exec web python manage.py seed_initial`»
- «Откройте http://localhost/admin/»
- Отдельный раздел «Deployment на новый хостинг за 2 часа»: что положить в `.env`, как запустить nginx с TLS (пока placeholder, детали в Phase 8)

### Claude's Discretion
- Точные версии минорных зависимостей (через Poetry, фиксированные на момент установки)
- Имена Celery-очередей (по умолчанию `default`)
- Конкретная вёрстка healthcheck-эндпоинтов (простой `/health/` для web, Celery inspect для worker)
- Имена volumes в docker-compose
- Детали gunicorn workers (`--workers 2 --threads 2` для dev)
- Структура `apps/core/mixins.py` (база, добавляется по необходимости)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project-level
- `/Users/a1111/Desktop/projects/oplata project/CLAUDE.md` — архитектура, стек, принципы разработки, команды
- `/Users/a1111/Desktop/projects/oplata project/.planning/PROJECT.md` — Core Value, скоуп, ограничения, Key Decisions
- `/Users/a1111/Desktop/projects/oplata project/.planning/REQUIREMENTS.md` — требования INFRA-01..07, DATA-01..13
- `/Users/a1111/Desktop/projects/oplata project/.planning/ROADMAP.md` — фаза 1, success criteria

### Research artifacts (обязательно к прочтению)
- `/Users/a1111/Desktop/projects/oplata project/.planning/research/STACK.md` — версии Django 5.2, DRF, Celery, WeasyPrint, системные зависимости
- `/Users/a1111/Desktop/projects/oplata project/.planning/research/ARCHITECTURE.md` — компонентные границы, build order, Redis DB изоляция, template versioning паттерн
- `/Users/a1111/Desktop/projects/oplata project/.planning/research/PITFALLS.md` — Cyrillic fonts, WeasyPrint memory leak, FSM durability, template versioning traps
- `/Users/a1111/Desktop/projects/oplata project/.planning/research/SUMMARY.md` — синтез всего research, roadmap implications
- `/Users/a1111/Desktop/projects/oplata project/.planning/research/FEATURES.md` — фичи по категориям (для контекста моделей)

### External docs (для researcher Phase 1 — верифицировать актуальность)
- Django 5.2 LTS release notes — миграции, новый async ORM
- `django-fsm` docs — транзишны и декораторы
- `django-storages[s3]` — S3-совместимые настройки для MinIO
- `poetry` docs — groups, lock, multistage Docker builds
- WeasyPrint system dependencies — точный список apt-пакетов для python:3.12-slim

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **CLAUDE.md** уже написан с архитектурным guidance — planner и executor обязаны с ним сверяться
- Никаких других assets — greenfield проект, голый каталог с `CLAUDE.md`, `.planning/`, `.git`

### Established Patterns
- Нет — устанавливаются этой фазой

### Integration Points
- Нет — фаза 1 создаёт всё с нуля
- Последующие фазы будут интегрироваться через `apps/*` и REST endpoints

</code_context>

<specifics>
## Specific Ideas

- **Docker Compose разворачивает всё одной командой** — пользователь явно хочет «положил код, `docker-compose up`, работает». Никаких ручных `pip install`, `npm install`, `postgres setup`.
- **Автономная админка** — требование заказчика «не звонить разработчику, чтобы поменять цену». Для Phase 1 это означает: цены хранятся в БД, а не в коде; тексты в ContentBlock, а не в шаблонах.
- **WeasyPrint-готовый образ** — Cyrillic-шрифты и Pango ставятся в Phase 1, чтобы Phase 6 не упиралась в инфраструктуру
- **Версионирование — не фича, а инвариант** — из research PITFALLS.md: «must be built before the first real order, not after». Никаких компромиссов.
- **Бэкапы — с дня 1** — скрипт и интеграция с MinIO есть сразу, автоматизация cron в Phase 8

</specifics>

<deferred>
## Deferred Ideas

- CI pipeline (GitHub Actions) — Phase 8 (HARD-03)
- TLS через certbot — Phase 8 (HARD-04)
- Sentry интеграция — Phase 8 (HARD-02)
- Cron для бэкапов — Phase 8
- Production-grade admin UI (поверх Django Admin) — Phase 7
- Seed продакшн-данных (реальные отрасли с реальными анкетами) — требует контента от заказчика, после v1
- KZ data residency hosting — бизнес-решение, не кодовое; отмечено в STATE.md

</deferred>

---

*Phase: 01-infrastructure-data-model*
*Context gathered: 2026-04-15*
