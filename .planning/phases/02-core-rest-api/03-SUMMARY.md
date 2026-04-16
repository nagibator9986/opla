---
phase: 02-core-rest-api
plan: 03
subsystem: api
tags: [drf, django-fsm, submission, answer, jwt, rest]

# Dependency graph
requires:
  - phase: 02-core-rest-api
    provides: DRF setup, SimpleJWT, ClientProfile onboarding, deeplink exchange
  - phase: 01-infrastructure-data-model
    provides: Submission model with FSM, Answer model, QuestionnaireTemplate, Industry, Tariff
provides:
  - POST /api/v1/submissions/ — create Submission linked to active template + tariff
  - GET /api/v1/submissions/{uuid}/ — status + progress
  - GET /api/v1/submissions/{uuid}/next-question/ — first unanswered question or 204
  - POST /api/v1/submissions/{uuid}/answers/ — save validated Answer
  - POST /api/v1/submissions/{uuid}/complete/ — FSM transition complete_questionnaire()
  - Client isolation: JWT user can only access own submissions
affects: [phase-03-telegram-bot, phase-04-payments, phase-05-frontend]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - _get_client_profile(user) helper resolves ClientProfile from tg_{id}@baqsy.internal email
    - AnswerCreateSerializer validates JSON value by field_type (text/number/choice/multichoice)
    - UUID primary keys in URL patterns via <uuid:pk>
    - FSM transitions called via submission.method() + submission.save() — never direct status assignment

key-files:
  created:
    - backend/apps/submissions/serializers.py
    - backend/apps/submissions/views.py
    - backend/apps/submissions/tests/test_api.py
  modified:
    - backend/apps/submissions/urls.py
    - backend/apps/accounts/tests/test_api.py

key-decisions:
  - "complete_questionnaire() requires IN_PROGRESS_FULL; tests advance FSM via _advance_to_in_progress_full() helper"
  - "NextQuestionView returns 204 No Content when all questions answered — sentinel for bot/frontend"
  - "AnswerCreateSerializer validates value shape per field_type before persisting; duplicate raises 400 (not 500)"
  - "total_questions counts only required=True questions; answered_count counts all submitted answers"

patterns-established:
  - "_get_client_profile(user): resolve ClientProfile from JWT synthetic email for all submission views"
  - "Answer field_type validation: always check dict shape + key presence + value type + valid_choices membership"
  - "UUID URL pattern: <uuid:pk> in urlpatterns — never <int:pk> for Submission"

requirements-completed: [API-05, API-06, API-07, API-08, API-09]

# Metrics
duration: 3min
completed: 2026-04-16
---

# Phase 02 Plan 03: Submission Lifecycle API Summary

**5-endpoint Submission REST API with FSM transitions, per-field_type Answer validation, and JWT client isolation**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-04-16T08:57:22Z
- **Completed:** 2026-04-16T09:00:01Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- Full Submission lifecycle API: create → next-question → answer → complete → status
- AnswerCreateSerializer validates JSON value shape by field_type (text/number/choice/multichoice) with option membership checks
- 9 integration tests cover happy path + all edge cases (404 isolation, 204 sentinel, duplicate 400, incomplete 400)

## Task Commits

1. **Task 03-01: Create submission serializers** - `20bf6a4` (feat)
2. **Task 03-02: Create submission views + URL patterns** - `2ae227c` (feat)
3. **Task 03-03: Full lifecycle integration tests** - `2e0e7ed` (test)

## Files Created/Modified

- `backend/apps/submissions/serializers.py` — 4 serializers with field_type validation
- `backend/apps/submissions/views.py` — 5 APIView classes with client isolation
- `backend/apps/submissions/urls.py` — 5 URL patterns with `<uuid:pk>`
- `backend/apps/submissions/tests/test_api.py` — 8 integration tests + FSM helper
- `backend/apps/accounts/tests/test_api.py` — removed xfail marker (endpoint now live)

## Decisions Made

- `complete_questionnaire()` FSM requires source status `IN_PROGRESS_FULL`. Tests that call the complete endpoint advance status via `_advance_to_in_progress_full()` helper (simulates paid → questionnaire flow). Real usage requires payment flow first.
- `total_questions` field counts only `required=True` questions to match progress tracking semantics; `answered_count` counts all answers including optional.
- `NextQuestionView` excludes already-answered questions by `question_id` and orders by `order` field to guarantee sequential delivery.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] FSM state mismatch in test_complete_submission**
- **Found during:** Task 03-03 (integration test authoring)
- **Issue:** Plan's test fixture creates a fresh Submission (status=`CREATED`), then calls `complete/` — `complete_questionnaire()` requires `IN_PROGRESS_FULL`, so the test would fail with `TransitionNotAllowed`
- **Fix:** Added `_advance_to_in_progress_full()` helper that advances `CREATED → IN_PROGRESS_BASIC → PAID → IN_PROGRESS_FULL` before answering questions. Applied to `test_complete_submission` and `test_complete_without_all_answers_returns_400`
- **Files modified:** `backend/apps/submissions/tests/test_api.py`
- **Verification:** All 9 tests pass
- **Committed in:** `2e0e7ed` (Task 03-03 commit)

**2. [Rule 1 - Bug] Stale xfail marker in accounts test**
- **Found during:** Task 03-03 (running full test suite)
- **Issue:** `test_unauthenticated_request_returns_401` was marked `xfail` pending submission endpoint — now xpassed since endpoint is live
- **Fix:** Removed `@pytest.mark.xfail` decorator
- **Files modified:** `backend/apps/accounts/tests/test_api.py`
- **Verification:** Test passes cleanly (59 passed, 0 xfail)
- **Committed in:** `2e0e7ed` (Task 03-03 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1 - bug)
**Impact on plan:** Both fixes necessary for correct test behavior. No scope creep.

## Issues Encountered

None beyond the FSM mismatch documented above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All 5 submission endpoints ready for consumption by Telegram bot (Phase 3)
- Client isolation enforced via JWT → synthetic email → ClientProfile lookup
- Payment integration point: `mark_paid()` + `start_questionnaire()` transitions reserved for Phase 4 CloudPayments webhook handler
- Phase 3 bot can call: POST /submissions/ → GET /next-question/ → POST /answers/ (loop) → POST /complete/

---
*Phase: 02-core-rest-api*
*Completed: 2026-04-16*
