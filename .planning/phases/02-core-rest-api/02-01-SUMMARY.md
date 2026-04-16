---
phase: 02-core-rest-api
plan: 01
subsystem: auth
tags: [jwt, simplejwt, redis, deeplink, bot-auth, permissions, drf]

# Dependency graph
requires:
  - phase: 01-infrastructure-data-model
    provides: BaseUser+ClientProfile models, migrations, pytest fixtures, conftest factories
  - phase: 02-core-rest-api plan 00
    provides: REST_FRAMEWORK+SIMPLE_JWT settings, api_urls.py routing, bot_urls.py placeholder, factories
provides:
  - IsBotAuthenticated DRF permission class (X-Bot-Token header)
  - OnboardingView POST /api/v1/bot/onboarding/ — create/update ClientProfile + synthetic BaseUser
  - DeeplinkCreateView POST /api/v1/bot/deeplink/ — UUID token in Redis db=2 (TTL 30min)
  - DeeplinkExchangeView POST /api/v1/bot/deeplink/exchange/ — UUID → JWT access+refresh pair
  - Full test coverage: 17 passing tests, 1 xfail (submissions pending)
affects: [03-telegram-bot, 04-payments, 05-frontend]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "IsBotAuthenticated: authentication_classes=[] bypasses JWT pipeline so IsBotAuthenticated runs first (returning 403, not 401)"
    - "Synthetic user pattern: tg_{telegram_id}@baqsy.internal email for BaseUser JWT subject"
    - "Redis deep-link: redis.Redis(host, port, db=2) module-level factory via _get_deeplink_redis() for mockability"
    - "override_settings per method (not class) when using pytest-style classes (Django restriction)"

key-files:
  created:
    - backend/apps/accounts/permissions.py
    - backend/apps/accounts/serializers.py
    - backend/apps/accounts/views.py
    - backend/apps/accounts/tests/test_api.py
    - backend/apps/accounts/tests/test_deeplink.py
  modified:
    - backend/apps/accounts/bot_urls.py
    - backend/baqsy/settings/base.py

key-decisions:
  - "authentication_classes=[] on bot views so IsBotAuthenticated returns 403 (not 401 masked by JWT auth pipeline)"
  - "REDIS_URL setting derived from REDIS_HOST+REDIS_PORT for clean deep-link client construction"
  - "profile.user OneToOneField already added by Plan 00 — OnboardingView links user to profile on creation"
  - "test_unauthenticated_request_returns_401 marked xfail until submissions endpoint added in Plan 03"

patterns-established:
  - "Bot endpoints: authentication_classes=[] + permission_classes=[IsBotAuthenticated]"
  - "Deep-link Redis: _get_deeplink_redis() factory function for easy mock patching in tests"
  - "Mock pattern: @patch('apps.accounts.views._get_deeplink_redis') + MagicMock().get.return_value = str(profile.id)"

requirements-completed: [API-01, API-02, API-10, API-11]

# Metrics
duration: 5min
completed: 2026-04-16
---

# Phase 2 Plan 01: JWT Auth, Bot Auth, Deep-Link Endpoints Summary

**IsBotAuthenticated permission class + three bot API endpoints with Redis deep-link token flow and full pytest coverage (17 tests, 1 xfail)**

## Performance

- **Duration:** 5 min
- **Started:** 2026-04-16T08:48:34Z
- **Completed:** 2026-04-16T08:53:34Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments

- `IsBotAuthenticated` DRF permission verifies `X-Bot-Token` header against `BOT_API_SECRET` setting
- Three bot endpoints: onboarding (create/update ClientProfile + synthetic BaseUser), deeplink create (UUID in Redis db=2), deeplink exchange (UUID → JWT access+refresh, one-time delete)
- 17 tests pass with mocked Redis — no live Redis required for test suite

## Task Commits

1. **Task 01-01: IsBotAuthenticated permission** - `770da51` (feat)
2. **Task 01-02: deep-link views + bot_urls** - `6a26bd1` (feat)
3. **Task 01-03: auth + deep-link tests** - committed by Plan 00 executor `04bb1d1` (docs)

## Files Created/Modified

- `backend/apps/accounts/permissions.py` — IsBotAuthenticated permission class
- `backend/apps/accounts/serializers.py` — OnboardingSerializer, DeeplinkCreate/ExchangeSerializer, ClientProfileSerializer
- `backend/apps/accounts/views.py` — OnboardingView, DeeplinkCreateView, DeeplinkExchangeView with `authentication_classes=[]`
- `backend/apps/accounts/bot_urls.py` — wired 3 routes (onboarding, deeplink create, deeplink exchange)
- `backend/apps/accounts/tests/test_api.py` — JWT token test, bot token 403 guard, admin redirect
- `backend/apps/accounts/tests/test_deeplink.py` — full onboarding/deeplink flow with mocked Redis
- `backend/baqsy/settings/base.py` — added `REDIS_URL` setting

## Decisions Made

- Set `authentication_classes = []` on `OnboardingView` and `DeeplinkCreateView` so `IsBotAuthenticated` is evaluated directly. Without this, DRF's default `JWTAuthentication` runs first and returns 401 for anonymous requests before permissions are checked — masking the intended 403 behavior.
- `REDIS_URL` derived from `REDIS_HOST:REDIS_PORT` in settings for clean URL construction in `_get_deeplink_redis()`.
- Marked `test_unauthenticated_request_returns_401` as `xfail(strict=False)` — the test is correct in intent but requires a JWT-protected endpoint which doesn't exist until Plan 03 (submissions).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Add authentication_classes=[] to bot views**
- **Found during:** Task 01-03 (test execution)
- **Issue:** `test_missing_bot_token_returns_403` got 401 instead of 403. DRF's default authentication pipeline (`JWTAuthentication`) returns 401 for unauthenticated requests before permissions run.
- **Fix:** Added `authentication_classes = []` to `OnboardingView` and `DeeplinkCreateView` so the permission class is evaluated first.
- **Files modified:** `backend/apps/accounts/views.py`
- **Verification:** `pytest apps/accounts/tests/ -x -q` → 17 passed, 1 xfailed
- **Committed in:** `04bb1d1` (Plan 00 executor committed simultaneously)

**2. [Rule 1 - Bug] Fix override_settings usage in pytest class**
- **Found during:** Task 01-03 (collection error)
- **Issue:** `@override_settings` as class decorator raises `ValueError: Only subclasses of Django SimpleTestCase can be decorated with override_settings` in pytest-django context.
- **Fix:** Moved `@override_settings(BOT_API_SECRET="test-secret")` to each individual test method.
- **Files modified:** `backend/apps/accounts/tests/test_api.py`, `backend/apps/accounts/tests/test_deeplink.py`
- **Verification:** No collection errors, all tests pass.
- **Committed in:** `04bb1d1`

---

**Total deviations:** 2 auto-fixed (1 blocking issue, 1 bug)
**Impact on plan:** Both fixes required for tests to run correctly. No scope creep.

## Issues Encountered

- Plan 00 ran in parallel and committed several of our files (test stubs, `authentication_classes=[]` on views). Final state is correct and consistent — all 17 tests pass.

## Next Phase Readiness

- Bot auth layer complete: bots can authenticate via `X-Bot-Token`, onboard clients, create deep-link tokens
- JWT foundation in place: synthetic users support `RefreshToken.for_user()` calls
- Ready for Plan 02 (industries list endpoint) and Plan 03 (submissions CRUD)
- `test_unauthenticated_request_returns_401` will auto-pass once Plan 03 adds `SubmissionCreateView`

---
*Phase: 02-core-rest-api*
*Completed: 2026-04-16*
