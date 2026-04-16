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
