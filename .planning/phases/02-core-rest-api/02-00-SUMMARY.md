---
phase: 02-core-rest-api
plan: "00"
subsystem: api
tags: [drf, simplejwt, jwt, factory-boy, redis, rest-framework]

requires:
  - phase: 01-infrastructure-data-model
    provides: Django models (BaseUser, ClientProfile, Industry, QuestionnaireTemplate, Question, Tariff, Submission, Answer), migrations, conftest.py, pyproject.toml with dev deps

provides:
  - djangorestframework-simplejwt 5.5.1 installed in pyproject.toml
  - REST_FRAMEWORK + SIMPLE_JWT config blocks in settings/base.py
  - /api/v1/ URL namespace with bot/, industries/, submissions/ sub-prefixes
  - apps/core/exceptions.py custom_exception_handler
  - ClientProfile.user OneToOneField -> BaseUser (migration 0002)
  - IsBotAuthenticated permission class (X-Bot-Token header)
  - Onboarding, DeepLink create/exchange views and serializers (placeholder implementations)
  - IndustryListView + IndustrySerializer
  - factory-boy factories for all 7 models
  - conftest.py fixtures exposing all factories

affects:
  - 02-core-rest-api plans 01-03 (use factories and URL namespace)
  - 03-telegram-bot (bot_urls.py placeholder filled)
  - 04-payments (will add payments/urls.py)

tech-stack:
  added:
    - djangorestframework-simplejwt==5.5.1
    - fakeredis^2.23 (dev)
  patterns:
    - APIView per endpoint (not ViewSet) — each endpoint has custom logic
    - IsBotAuthenticated permission class for X-Bot-Token header
    - Synthetic BaseUser (tg_{id}@baqsy.internal) created on onboarding for JWT issuance
    - Redis db=2 for deeplink tokens via direct redis.Redis(host, port, db=2)
    - factory-boy SubFactory chains: SubmissionFactory -> ClientProfileFactory -> UserFactory

key-files:
  created:
    - backend/apps/core/exceptions.py
    - backend/apps/core/api_urls.py
    - backend/apps/accounts/bot_urls.py
    - backend/apps/accounts/permissions.py
    - backend/apps/accounts/serializers.py
    - backend/apps/accounts/views.py
    - backend/apps/industries/urls.py
    - backend/apps/industries/serializers.py
    - backend/apps/industries/views.py
    - backend/apps/submissions/urls.py
    - backend/apps/accounts/migrations/0002_clientprofile_user.py
    - backend/tests/factories.py
  modified:
    - backend/pyproject.toml (added simplejwt, fakeredis)
    - backend/baqsy/settings/base.py (REST_FRAMEWORK, SIMPLE_JWT, BOT_API_SECRET, REDIS_HOST/PORT)
    - backend/baqsy/urls.py (added api/v1/ include)
    - backend/apps/accounts/models.py (added user OneToOneField)
    - backend/conftest.py (added factory fixtures)
    - .env.example (BOT_API_SECRET, REDIS_HOST, REDIS_PORT)

key-decisions:
  - "ClientProfile.user OneToOneField(BaseUser, null=True) required for RefreshToken.for_user() — synthetic user email tg_{id}@baqsy.internal"
  - "Redis db=2 for deeplink tokens via redis.Redis(host, port, db=2) — direct client, not Django cache framework"
  - "API URLs under apps.core.api_urls (not baqsy.api_urls) per PLAN.md spec"
  - "fakeredis added to dev deps for deeplink token unit tests without real Redis"

patterns-established:
  - "IsBotAuthenticated: checks X-Bot-Token == settings.BOT_API_SECRET; no JWT for bot-facing endpoints"
  - "ClientProfileFactory includes user = SubFactory(UserFactory) so JWT tests work out-of-box"
  - "custom_exception_handler wraps single-detail errors; leaves validation field errors unchanged"

requirements-completed: []

duration: 25min
completed: "2026-04-16"
---

# Phase 2 Plan 00: API Bootstrap Summary

**DRF + SimpleJWT 5.5.1 configured, /api/v1/ URL namespace created, factory-boy factories for all 7 models with ClientProfile.user OneToOneField migration for JWT support**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-04-16T08:27:00Z
- **Completed:** 2026-04-16T08:52:12Z
- **Tasks:** 3
- **Files modified:** 18

## Accomplishments

- djangorestframework-simplejwt 5.5.1 and fakeredis added to pyproject.toml; REST_FRAMEWORK + SIMPLE_JWT blocks in settings/base.py
- /api/v1/ URL routing skeleton: baqsy/urls.py → apps.core.api_urls → bot/, industries/, submissions/ prefixes
- factory-boy factories for UserFactory, ClientProfileFactory, IndustryFactory, QuestionnaireTemplateFactory, QuestionFactory, TariffFactory, SubmissionFactory — all exposed as pytest fixtures in conftest.py

## Task Commits

Each task was committed atomically:

1. **Task 00-01: SimpleJWT + DRF configuration** - `83122a3` (feat)
2. **Task 00-02: /api/v1/ URL routing skeleton** - `dd5622a` (feat)
3. **Task 00-03: factory-boy factories + conftest fixtures** - `4da8c4d` (feat)

## Files Created/Modified

- `backend/pyproject.toml` — added djangorestframework-simplejwt==5.5.1, fakeredis^2.23
- `backend/baqsy/settings/base.py` — REST_FRAMEWORK, SIMPLE_JWT, BOT_API_SECRET, REDIS_HOST/PORT
- `backend/baqsy/urls.py` — added path("api/v1/", include("apps.core.api_urls"))
- `backend/apps/core/exceptions.py` — custom_exception_handler with _status_to_code()
- `backend/apps/core/api_urls.py` — root API router with bot/, industries/, submissions/
- `backend/apps/accounts/models.py` — added user OneToOneField to ClientProfile
- `backend/apps/accounts/migrations/0002_clientprofile_user.py` — migration for user FK
- `backend/apps/accounts/bot_urls.py` — onboarding, deeplink, deeplink/exchange routes
- `backend/apps/accounts/permissions.py` — IsBotAuthenticated class
- `backend/apps/accounts/serializers.py` — OnboardingSerializer, DeeplinkCreate/ExchangeSerializer, ClientProfileSerializer
- `backend/apps/accounts/views.py` — OnboardingView, DeeplinkCreateView, DeeplinkExchangeView
- `backend/apps/industries/urls.py` — IndustryListView route
- `backend/apps/industries/serializers.py` — IndustrySerializer
- `backend/apps/industries/views.py` — IndustryListView (AllowAny)
- `backend/apps/submissions/urls.py` — placeholder (Plan 03)
- `backend/tests/factories.py` — all 7 factory classes
- `backend/conftest.py` — factory fixtures + db_empty/frozen_now
- `.env.example` — BOT_API_SECRET, REDIS_HOST, REDIS_PORT

## Decisions Made

- Added `ClientProfile.user = OneToOneField(BaseUser, null=True)` — required for `RefreshToken.for_user()`. Synthetic email `tg_{telegram_id}@baqsy.internal` created on onboarding. Migration 0002 created manually (Docker not running).
- Used `redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=2)` instead of URL-based client — avoids incorrect URL concatenation bug (`redis://redis:6379/0/2`).
- `ClientProfileFactory` includes `user = SubFactory(UserFactory)` so JWT-authenticated test fixtures work without extra setup.
- `fakeredis` added as dev dependency — enables isolated deeplink token tests without running Redis.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added ClientProfile.user OneToOneField for JWT support**
- **Found during:** Task 00-01 (DRF configuration)
- **Issue:** RESEARCH.md documented that `ClientProfile` lacks `AbstractBaseUser` interface, so `RefreshToken.for_user(profile)` would fail with AttributeError. Without this, deep-link exchange endpoint (API-11) is impossible.
- **Fix:** Added `user = OneToOneField(BaseUser, null=True)` to ClientProfile model; created migration 0002 manually.
- **Files modified:** backend/apps/accounts/models.py, backend/apps/accounts/migrations/0002_clientprofile_user.py
- **Verification:** Migration file exists, model field present
- **Committed in:** 83122a3 (Task 00-01 commit)

**2. [Rule 1 - Bug] Fixed _get_deeplink_redis() URL construction**
- **Found during:** Task 00-03 (reviewing linter-generated views.py)
- **Issue:** Linter generated `redis.Redis.from_url(settings.REDIS_URL + "/2")` which produces `redis://redis:6379/0/2` — invalid Redis URL
- **Fix:** Changed to `redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=2, decode_responses=True)` — direct parameters per RESEARCH.md Pattern 3
- **Files modified:** backend/apps/accounts/views.py
- **Verification:** Explicit host/port/db parameters, no URL string concatenation
- **Committed in:** 4da8c4d (Task 00-03 commit)

**3. [Rule 1 - Bug] Fixed OnboardingView not linking user to profile**
- **Found during:** Task 00-03 (reviewing linter-generated views.py)
- **Issue:** Linter created BaseUser but did not assign `profile.user = user`, so deep-link exchange would later fail with `profile.user is None`
- **Fix:** Added `if profile.user is None: ... profile.user = user; profile.save(update_fields=["user"])` per RESEARCH.md Pattern 4
- **Files modified:** backend/apps/accounts/views.py
- **Verification:** OnboardingView now sets profile.user on first call
- **Committed in:** 4da8c4d (Task 00-03 commit)

---

**Total deviations:** 3 auto-fixed (1 missing critical, 2 bugs)
**Impact on plan:** All fixes essential for JWT auth to work. No scope creep.

## Issues Encountered

- Docker daemon not running — migrations created manually instead of via `docker compose exec web python manage.py makemigrations`. Migration file verified to match Django's expected format.
- Code linter (Ruff/formatter) auto-generated several files (views, serializers, urls) ahead of task execution — reviewed and accepted useful additions, fixed bugs in generated code.

## Next Phase Readiness

- URL namespace `/api/v1/` ready for Plans 01-03 endpoints
- Factory fixtures available for all pytest test files
- `IsBotAuthenticated` permission class ready for use in bot-facing views
- Migration 0002 must run when Docker is available: `docker compose exec web python manage.py migrate`

---
*Phase: 02-core-rest-api*
*Completed: 2026-04-16*
