---
phase: 03-telegram-bot
plan: 01
subsystem: bot
tags: [aiogram, redis, httpx, fsm, telegram, python-decouple]

# Dependency graph
requires:
  - phase: 02-core-rest-api
    provides: Django REST API endpoints (bot/onboarding, bot/deeplink, bot/jwt, industries, submissions)
provides:
  - aiogram 3 Dispatcher with RedisStorage FSM
  - OnboardingStates 5-step FSM (name, company, industry, phone, city)
  - QuestionnaireStates FSM (answering, multichoice_selecting)
  - /start handler with deep-link detection (questionnaire_{uuid})
  - Returning-user vs new-user detection in /start
  - Onboarding flow calling POST /bot/onboarding/ + POST /bot/deeplink/
  - /status and /help commands
  - httpx async API client with X-Bot-Token and JWT auth
  - Industry inline keyboard builder
  - Questionnaire stub handler (full implementation in Plan 02)
affects: [03-02-bot-questionnaire-fsm, 04-payments, 06-pdf-delivery]

# Tech tracking
tech-stack:
  added: [aiogram 3.27, redis FSM storage db=1, httpx.AsyncClient, python-decouple]
  patterns:
    - Router-based handler organisation (one file per concern)
    - Lazy router import inside main() to prevent circular imports
    - Singleton httpx.AsyncClient via get_client() factory
    - Per-request JWT client (_jwt_client) for authenticated submission ops
    - FSM data carries submission_id + jwt_token for questionnaire context

key-files:
  created:
    - bot/config.py
    - bot/services/api_client.py
    - bot/states/onboarding.py
    - bot/states/questionnaire.py
    - bot/keyboards/industry.py
    - bot/handlers/start.py
    - bot/handlers/onboarding.py
    - bot/handlers/commands.py
    - bot/handlers/questionnaire.py
    - bot/handlers/__init__.py
    - bot/services/__init__.py
    - bot/states/__init__.py
    - bot/keyboards/__init__.py
  modified:
    - bot/main.py

key-decisions:
  - "Router registration order: start_router (deep_link) BEFORE commands_router — ensures CommandStart(deep_link=True) matches first"
  - "questionnaire.py stub created in Plan 01 so main.py import doesn't fail at startup; full replacement in Plan 02"
  - "_jwt_client creates per-request AsyncClient context manager for JWT endpoints; singleton client only for bot-token endpoints"
  - "_send_next_question lives in start.py and is imported by questionnaire.py — single source of truth for question display"

patterns-established:
  - "Bot handler files: one Router per file, imported lazily in main()"
  - "API client: get_client() singleton for X-Bot-Token calls; _jwt_client() context-manager for JWT calls"
  - "FSM data keys: submission_id, jwt_token, current_question_id, current_field_type, current_options, mc_selected"

requirements-completed: [BOT-01, BOT-02, BOT-03, BOT-04, BOT-08, BOT-09]

# Metrics
duration: 3min
completed: 2026-04-16
---

# Phase 3 Plan 01: Bot Core + Onboarding FSM Summary

**aiogram 3 bot with RedisStorage FSM, 5-step onboarding, deep-link /start dispatch, /status + /help commands, and httpx async API client wiring bot to Django REST**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-04-16T10:32:22Z
- **Completed:** 2026-04-16T10:35:04Z
- **Tasks:** 3
- **Files modified:** 14

## Accomplishments
- Full aiogram 3 Dispatcher replacing Phase 1 skeleton — bot is now runnable with real long-polling
- 5-step onboarding FSM: name, company, industry (inline keyboard from GET /industries/), WhatsApp phone, city — ends with POST /bot/onboarding/ + deep-link to site
- /start smart routing: new user starts onboarding, returning user with active submission offered resume, returning user without submission shown tariff link
- Deep-link handler: /start questionnaire_{uuid} sets FSM state and starts questionnaire flow immediately
- httpx async API client with singleton X-Bot-Token client and per-request JWT client for submission endpoints

## Task Commits

Each task was committed atomically:

1. **Task 01-01: Config, API client, FSM states** - `1008c13` (feat)
2. **Task 01-02: /start handler, onboarding FSM, commands** - `c1c275c` (feat)
3. **Task 01-03: main.py Dispatcher + questionnaire stub** - `4c1e253` (feat)

## Files Created/Modified
- `bot/config.py` - env vars via python-decouple (BOT_TOKEN, API_BASE_URL, BOT_API_SECRET, REDIS_URL, SITE_URL)
- `bot/services/api_client.py` - async httpx client: onboard, create_deeplink, get_industries, get_jwt, get_active_submission, get_next_question, save_answer, complete_submission
- `bot/states/onboarding.py` - OnboardingStates: waiting_name/company/industry/phone/city
- `bot/states/questionnaire.py` - QuestionnaireStates: answering, multichoice_selecting
- `bot/keyboards/industry.py` - build_industry_keyboard() from industries list
- `bot/handlers/start.py` - /start dispatch, deep-link handling, resume_questionnaire callback, _send_next_question shared function
- `bot/handlers/onboarding.py` - 5-step FSM handlers with validation
- `bot/handlers/commands.py` - /status and /help
- `bot/handlers/questionnaire.py` - stub handlers for text/choice/multichoice (full implementation Plan 02)
- `bot/main.py` - replaced skeleton with Dispatcher + RedisStorage + 4 routers

## Decisions Made
- Router registration order is critical: `start_router` (with deep_link=True filter) must come before `commands_router` to ensure deep-link /start is matched before plain CommandStart
- questionnaire.py stub created now (rather than waiting for Plan 02) so main.py can import it without NameError at startup
- `_send_next_question` placed in start.py and imported into questionnaire.py to avoid circular imports while maintaining single definition

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created questionnaire.py stub to prevent import failure**
- **Found during:** Task 03-03 (main.py creation)
- **Issue:** main.py imports `from bot.handlers.questionnaire import router` but questionnaire.py is scoped to Plan 02 — import would fail at bot startup
- **Fix:** Created bot/handlers/questionnaire.py with full working stub handlers (text, choice, multichoice) that import _send_next_question from start.py. Plan 02 will replace this with the full implementation.
- **Files modified:** bot/handlers/questionnaire.py (created)
- **Verification:** Import chain complete; router registered correctly in Dispatcher
- **Committed in:** 4c1e253 (Task 03 commit)

---

**Total deviations:** 1 auto-fixed (Rule 3 — blocking)
**Impact on plan:** Necessary to make bot startable in Plan 01. Stub is functional for text/choice/multichoice questions; Plan 02 replaces it with full implementation.

## Issues Encountered
None beyond the questionnaire stub deviation above.

## User Setup Required
None — no external service configuration required for bot code. TELEGRAM_BOT_TOKEN and AIOGRAM_REDIS_URL must be set in .env (already documented in .env.example).

## Next Phase Readiness
- Bot core is complete and startable with all env vars set
- Plan 02 (questionnaire FSM) can replace bot/handlers/questionnaire.py without touching any other files
- Celery beat 24h reminder task (BOT-11) is scoped to Plan 02 or later

---
*Phase: 03-telegram-bot*
*Completed: 2026-04-16*
