---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: Completed 04-payments-02-bot-notify-and-upsell-PLAN.md
last_updated: "2026-04-17T05:41:12.714Z"
last_activity: "2026-04-16 — Plan 00 executed: DRF + SimpleJWT bootstrap, /api/v1/ URL namespace, factory-boy factories"
progress:
  total_phases: 8
  completed_phases: 4
  total_plans: 13
  completed_plans: 13
  percent: 15
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-15)

**Core value:** Клиент платит за персональный PDF-аудит бизнеса и получает его автоматически после ручной проверки администратором — весь путь от первого контакта до доставки должен работать безотказно.
**Current focus:** Phase 1 — Infrastructure & Data Model

## Current Position

Phase: 2 of 8 (Core REST API)
Plan: 1 of 4 in current phase (Plan 00 complete)
Status: In progress
Last activity: 2026-04-16 — Plan 00 executed: DRF + SimpleJWT bootstrap, /api/v1/ URL namespace, factory-boy factories

Progress: [██░░░░░░░░] 15%

## Performance Metrics

**Velocity:**
- Total plans completed: 4
- Average duration: ~10 min
- Total execution time: 0.6 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-infrastructure-data-model | 4/4 | ~40 min | ~10 min |

**Recent Trend:**
- Last 5 plans: Plan 00 (~5 min), Plan 01 (~5 min), Plan 02 (~10 min), Plan 03 (~10 min)
- Trend: On track

*Updated after each plan completion*
| Phase 01 P02 | 10 | 8 tasks | 46 files |
| Phase 01 P03 | 10 | 4 tasks | 6 files |
| Phase 02-core-rest-api P01 | 5 | 3 tasks | 7 files |
| Phase 02-core-rest-api P02 | 7 | 2 tasks | 5 files |
| Phase 02-core-rest-api P03 | 3 | 3 tasks | 5 files |
| Phase 03-telegram-bot P00 | 10 | 2 tasks | 5 files |
| Phase 03-telegram-bot P01 | 3 | 3 tasks | 14 files |
| Phase 03-telegram-bot P02 | 5 | 2 tasks | 3 files |
| Phase 04-payments P01 | 167 | 3 tasks | 8 files |
| Phase 04-payments P02 | 137 | 3 tasks | 4 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Roadmap: Бот — тонкий REST-клиент; вся бизнес-логика в Django
- Roadmap: JSONB для Answer.value; версионирование QuestionnaireTemplate обязательно
- Roadmap: Docker Compose покрывает dev и prod; развёртывание ≤2 часов
- [Phase 01-infrastructure-data-model]: Wave 0: pytest-django harness с 14 xfail-заглушками создан до реализации — паттерн Nyquist feedback loop
- [Phase 01-infrastructure-data-model]: django-fsm-2 v4.2.4 выбран вместо archived django-fsm; django-environ ^0.11 (PyPI стабильный)
- [Phase 01-infrastructure-data-model Plan 01]: Multi-stage Dockerfile: builder (Poetry) + runtime (WeasyPrint+fonts); MinIO healthcheck mc ready local
- [Phase 01-infrastructure-data-model Plan 01]: POSTGRES_INITDB_ARGS C.UTF-8 (не ru_RU.UTF-8) — postgres:16 Debian не имеет ru_RU locale без locale-gen
- [Phase 01-infrastructure-data-model Plan 01]: AUTH_USER_MODEL=accounts.BaseUser установлен до создания модели — требование Django
- [Phase 01]: create_new_version deactivates OLD template BEFORE creating new (SQLite/PG partial unique constraint ordering)
- [Phase 01]: Industry.code SlugField (not slug) — UUIDModel for external models, BigAutoField for internal
- [Phase 01 Plan 03]: Tariff codes underscore convention: ashide_1, ashide_2, upsell (per CLAUDE.md)
- [Phase 01 Plan 03]: PGPASSWORD env var for pg_dump (not --password flag) — avoids credential leak in process list
- [Phase 01 Plan 03]: Backup cron scheduling deferred to Phase 8 (HARD-08); script only in Phase 1
- [Phase 02 Plan 00]: ClientProfile.user OneToOneField(BaseUser, null=True) для JWT — synthetic email tg_{id}@baqsy.internal
- [Phase 02 Plan 00]: Redis db=2 для deeplink через redis.Redis(host, port, db=2) — прямой клиент, не Django cache
- [Phase 02 Plan 00]: fakeredis добавлен в dev deps для изолированных тестов deeplink без реального Redis
- [Phase 02-core-rest-api]: authentication_classes=[] на bot views — IsBotAuthenticated возвращает 403, не 401 от JWT pipeline
- [Phase 02-core-rest-api]: Synthetic user pattern: tg_{telegram_id}@baqsy.internal email для BaseUser при onboarding
- [Phase 02-core-rest-api]: _get_deeplink_redis() factory function для mockability в тестах (Redis db=2)
- [Phase 02-core-rest-api]: Industries endpoint AllowAny (public), pagination PAGE_SIZE=20 from global settings
- [Phase 02-core-rest-api]: complete_questionnaire() requires IN_PROGRESS_FULL; test helper _advance_to_in_progress_full() advances FSM state for testing without payment
- [Phase 02-core-rest-api]: NextQuestionView returns 204 No Content sentinel when all questions answered — bot/frontend checks this before offering complete button
- [Phase 03-telegram-bot]: authentication_classes=[] на BotJWTView и ActiveSubmissionView — IsBotAuthenticated без JWT pipeline
- [Phase 03-telegram-bot]: BotJWTView переиспользует synthetic user email tg_{telegram_id}@baqsy.internal — единый паттерн идентификации
- [Phase 03-telegram-bot]: JWT ACCESS_TOKEN_LIFETIME 1h → 4h для длинных сессий прохождения анкеты в боте
- [Phase 03-telegram-bot]: Router order: start_router (deep_link) before commands_router — CommandStart(deep_link=True) must match before plain CommandStart
- [Phase 03-telegram-bot]: questionnaire.py stub in Plan 01 prevents import failure; full replacement in Plan 02
- [Phase 03-telegram-bot]: _send_next_question в start.py импортируется в questionnaire.py — единственный источник истины для отображения вопросов
- [Phase 03-telegram-bot]: Answer value always typed dict: {text:.., number:.., choice:.., choices:[..]} consistent with Answer.value JSONField
- [Phase 03-telegram-bot]: Multichoice done button shows live count 'Gotovo (N)' for UX clarity
- [Phase 04-payments]: Payment FK requires submission in get_or_create defaults — view fetches sub first via select_for_update then passes to defaults
- [Phase 04-payments]: mark_paid() requires in_progress_basic — PayView auto-advances created→in_progress_basic before FSM transition
- [Phase 04-payments]: Upsell tariff upgrade placed inside atomic PayView block; UpsellView reuses _get_client_profile for JWT identity; notify_bot_payment_success FSM transition catches errors silently for idempotency

### Pending Todos

None yet.

### Blockers/Concerns

- WhatsApp-провайдер не финализирован (Wazzup24 vs GreenAPI) — решить перед Phase 6
- Финальный список отраслей и тексты анкет не переданы — нужны для seed-скрипта в Phase 8
- Макеты лендинга и PDF («Вечный Иль») не получены — нужны перед Phase 5 и Phase 6

## Session Continuity

Last session: 2026-04-17T05:41:12.711Z
Stopped at: Completed 04-payments-02-bot-notify-and-upsell-PLAN.md
Resume file: None
