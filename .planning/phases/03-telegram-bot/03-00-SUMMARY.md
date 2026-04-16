---
phase: 03-telegram-bot
plan: 00
subsystem: api
tags: [django, drf, jwt, simplejwt, bot, telegram, pytest-asyncio]

# Dependency graph
requires:
  - phase: 02-core-rest-api
    provides: accounts views, bot_urls, Submission model, IsBotAuthenticated permission
provides:
  - POST /api/v1/bot/jwt/ endpoint for bot session recovery by telegram_id
  - GET /api/v1/bot/active-submission/ endpoint for in-progress submission lookup
  - Submission.last_reminded_at field for 24h reminder deduplication
  - JWT ACCESS_TOKEN_LIFETIME=4h for long questionnaire bot sessions
  - pytest-asyncio + pytest-mock dev deps in bot/pyproject.toml
affects: [03-telegram-bot, 02-core-rest-api, 04-payments]

# Tech tracking
tech-stack:
  added: [pytest-asyncio 0.24, pytest-mock 3.14]
  patterns: [bot API endpoints use authentication_classes=[] + IsBotAuthenticated, BotJWT issues synthetic user JWT for session recovery]

key-files:
  created:
    - backend/apps/submissions/migrations/0002_submission_last_reminded_at.py
  modified:
    - backend/apps/accounts/views.py
    - backend/apps/accounts/bot_urls.py
    - backend/apps/submissions/models.py
    - backend/baqsy/settings/base.py
    - bot/pyproject.toml

key-decisions:
  - "authentication_classes=[] на BotJWTView и ActiveSubmissionView — IsBotAuthenticated возвращает 403, не 401 от JWT pipeline (паттерн из Phase 02)"
  - "BotJWTView переиспользует synthetic user email tg_{telegram_id}@baqsy.internal — не создаёт дублирующий паттерн"
  - "asyncio_mode=auto в pytest.ini_options — все async тесты без декораторов"

patterns-established:
  - "Bot session recovery: POST /bot/jwt/ → get/create synthetic user → RefreshToken.for_user() → return access+refresh+client_profile_id"
  - "Active submission lookup: filter status__in=[in_progress_full, paid, in_progress_basic] → order by -created_at → first()"

requirements-completed: []

# Metrics
duration: 10min
completed: 2026-04-16
---

# Phase 3 Plan 00: Bot Bootstrap Summary

**BotJWTView и ActiveSubmissionView добавлены в Django API, Submission.last_reminded_at мигрирован, JWT lifetime 4h, pytest-asyncio в bot deps**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-04-16T10:23:00Z
- **Completed:** 2026-04-16T10:33:32Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- POST /api/v1/bot/jwt/ — бот запрашивает JWT по telegram_id для восстановления сессии после обрыва
- GET /api/v1/bot/active-submission/ — бот проверяет незавершённые Submission при /start
- Submission.last_reminded_at добавлен с миграцией — Celery beat использует его для деплупликации 24h-напоминаний
- JWT ACCESS_TOKEN_LIFETIME увеличен до 4h — покрывает длинные сессии прохождения анкеты
- pytest-asyncio + pytest-mock добавлены в dev зависимости бота

## Task Commits

1. **Task 00-01: Добавить BotJWTView и ActiveSubmissionView** - `a94683c` (feat)
2. **Task 00-02: last_reminded_at + JWT lifetime + pytest-asyncio** - `3fe4c41` (feat)

## Files Created/Modified
- `backend/apps/accounts/views.py` — добавлены классы BotJWTView и ActiveSubmissionView
- `backend/apps/accounts/bot_urls.py` — добавлены маршруты jwt/ и active-submission/
- `backend/apps/submissions/models.py` — добавлено поле last_reminded_at
- `backend/apps/submissions/migrations/0002_submission_last_reminded_at.py` — миграция поля
- `backend/baqsy/settings/base.py` — ACCESS_TOKEN_LIFETIME 1h → 4h
- `bot/pyproject.toml` — group dev: pytest, pytest-asyncio, pytest-mock; asyncio_mode=auto

## Decisions Made
- `authentication_classes = []` на обоих новых вью: паттерн Phase 02 — IsBotAuthenticated работает через X-Bot-Token header, не через JWT pipeline
- BotJWTView использует тот же synthetic user email `tg_{telegram_id}@baqsy.internal` что и OnboardingView — единый паттерн идентификации
- `asyncio_mode = "auto"` в pytest.ini_options — async тесты бота без ручных `@pytest.mark.asyncio` декораторов

## Deviations from Plan

None - план выполнен точно как написан.

## Issues Encountered
- `python` не найден в окружении — использован `python3 manage.py makemigrations`. Команда сработала без ошибок.

## User Setup Required
None — внешние сервисы не задействованы. Миграция применяется стандартным `python3 manage.py migrate`.

## Next Phase Readiness
- Plan 00 завершён: все prerequisites для бота добавлены в Django API
- Plan 01 (bot core + onboarding) может начаться: все необходимые endpoints существуют
- Celery beat task для 24h-напоминаний в Plan 02 может использовать Submission.last_reminded_at

---
*Phase: 03-telegram-bot*
*Completed: 2026-04-16*
