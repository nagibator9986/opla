---
phase: 01-infrastructure-data-model
plan: 02
subsystem: database
tags: [django, postgresql, fsm, django-fsm-2, migrations, models, admin]

requires:
  - phase: 01-infrastructure-data-model (plan 01)
    provides: Django project skeleton with baqsy settings, INSTALLED_APPS, AUTH_USER_MODEL

provides:
  - All 8 Django apps created: core, accounts, industries, submissions, payments, reports, delivery, content
  - All 13 models with correct fields, constraints, and Meta
  - QuestionnaireTemplate.create_new_version() classmethod (atomic, deactivate-first)
  - Submission.template_id immutability via __init__ + save() override
  - Submission FSM with 7 states via django-fsm-2 (protected transitions)
  - Payment.transaction_id unique constraint for CloudPayments idempotency
  - All migrations generated and applied cleanly
  - 31 model tests passing (no xfails)

affects: [02-api-layer, 03-bot, 04-payments, 06-pdf-delivery]

tech-stack:
  added:
    - django-fsm-2 (FSMField, @transition decorator)
  patterns:
    - TimestampedModel + UUIDModel abstract base classes from apps.core
    - Atomic deactivate-before-create pattern for partial unique constraints
    - __init__ + save() override pattern for field immutability
    - Separate ClientProfile (telegram_id) from BaseUser (email) — two auth models

key-files:
  created:
    - backend/apps/core/models.py (TimestampedModel, UUIDModel)
    - backend/apps/accounts/models.py (BaseUser, ClientProfile)
    - backend/apps/accounts/managers.py (UserManager)
    - backend/apps/industries/models.py (Industry, QuestionnaireTemplate, Question)
    - backend/apps/submissions/models.py (Submission with FSM, Answer)
    - backend/apps/payments/models.py (Tariff, Payment)
    - backend/apps/reports/models.py (AuditReport)
    - backend/apps/delivery/models.py (DeliveryLog)
    - backend/apps/content/models.py (ContentBlock)
    - backend/apps/*/migrations/0001_initial.py (x7 apps)
    - backend/apps/*/tests/test_*.py (all test files)
  modified:
    - backend/baqsy/settings/base.py (AUTH_USER_MODEL, INSTALLED_APPS — already existed)

key-decisions:
  - "create_new_version deactivates OLD template BEFORE creating new to avoid partial unique constraint violation in both SQLite (tests) and PostgreSQL (prod)"
  - "Industry.code (SlugField) not Industry.slug — follows PLAN.md field specification"
  - "Submission.tariff nullable FK — created before payment, tariff assigned at payment time"
  - "Answer ordering by question__order not answered_at — preserves questionnaire sequence"

patterns-established:
  - "Pattern: Deactivate-before-create for partial unique constraint — prevents constraint violations when atomically swapping active records"
  - "Pattern: __init__ + save() for field immutability — stores _original_field_id in __init__, checks in save() before first DB roundtrip"
  - "Pattern: UUIDModel for externally-referenced models (Submission, Payment), BigAutoField for internal (Question, Answer)"

requirements-completed:
  - DATA-01
  - DATA-02
  - DATA-03
  - DATA-04
  - DATA-05
  - DATA-06
  - DATA-07
  - DATA-08
  - DATA-09
  - DATA-10
  - DATA-11
  - DATA-12
  - DATA-13

duration: 10min
completed: 2026-04-16
---

# Phase 1 Plan 02: App Skeletons and All 13 Data Models Summary

**All 13 Django models across 8 apps, FSM Submission with 7 states, atomic template versioning, and 31 passing tests on SQLite**

## Performance

- **Duration:** 10 min
- **Started:** 2026-04-16T05:41:27Z
- **Completed:** 2026-04-16T05:51:49Z
- **Tasks:** 8
- **Files modified:** 46

## Accomplishments

- 13 models created across 7 domain apps + 1 core app, all with migrations
- `QuestionnaireTemplate.create_new_version()` works correctly: deactivates old before creating new, atomically within SELECT FOR UPDATE transaction
- `Submission.template_id` immutability enforced: raises ValidationError on any post-creation change
- Submission FSM: 7 states with protected transitions via django-fsm-2; invalid transitions raise `TransitionNotAllowed`
- `Payment.transaction_id` unique constraint ensures CloudPayments webhook idempotency
- 31 tests pass: versioning invariant, immutability, FSM transitions, JSONB fields, unique constraints

## Task Commits

1. **Task 02-01: apps/core abstract models + Django skeleton** - `e2c3857` (feat)
2. **Task 02-02: apps/accounts — BaseUser + ClientProfile** - `e2c3857` (feat)
3. **Task 02-03: apps/industries — Industry + QuestionnaireTemplate + Question** - `51c1fc5` (feat)
4. **Task 02-04: apps/submissions — Submission FSM + Answer** - `7e0e8a7` (feat)
5. **Task 02-05: apps/payments — Tariff + Payment** - `6530ad8` (feat)
6. **Task 02-06: apps/reports + apps/delivery + apps/content** - `fe9f354` (feat)
7. **Task 02-07: Generate and verify all migrations** - `e7a64ff` (feat)
8. **Task 02-08: Real model tests replacing xfail stubs** - `6e05855` (feat)

## Files Created/Modified

- `backend/apps/core/models.py` — TimestampedModel, UUIDModel abstract bases
- `backend/apps/accounts/models.py` — BaseUser (AbstractBaseUser + email auth), ClientProfile (telegram_id)
- `backend/apps/accounts/managers.py` — UserManager with create_user/create_superuser
- `backend/apps/industries/models.py` — Industry (code SlugField unique), QuestionnaireTemplate (versioning), Question (JSONField options)
- `backend/apps/submissions/models.py` — Submission (UUID PK, FSMField, immutability), Answer (JSONField value)
- `backend/apps/payments/models.py` — Tariff (price_kzt DecimalField), Payment (transaction_id unique, raw_webhook JSONField)
- `backend/apps/reports/models.py` — AuditReport (OneToOne Submission, pdf_url, admin_text)
- `backend/apps/delivery/models.py` — DeliveryLog (channel telegram/whatsapp, status queued/sent/delivered/failed)
- `backend/apps/content/models.py` — ContentBlock (key SlugField unique, HTML/text content type)
- `backend/apps/*/migrations/0001_initial.py` — 7 migration files generated and applied
- `backend/apps/*/admin.py` — all models registered in Django Admin
- `backend/apps/*/tests/test_*.py` — 10 test files, 31 tests total

## Decisions Made

- **Deactivate-before-create** in `create_new_version`: SQLite enforces partial unique constraints at INSERT time, so the old template must be deactivated before inserting the new one
- **Industry.code** (SlugField, unique) per PLAN.md — not `slug` as older test stubs assumed
- **Submission.tariff** is nullable FK: created before tariff assignment (payment comes later in flow)
- **Apps.core has no migrations**: only abstract base models, no concrete DB tables

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed create_new_version constraint violation ordering**
- **Found during:** Task 02-08 (tests)
- **Issue:** Original `create_new_version` created new active template BEFORE deactivating old one, causing `UNIQUE constraint failed: industries_questionnairetemplate.industry_id` on the partial unique index (both SQLite and PostgreSQL enforce constraint at INSERT time)
- **Fix:** Reordered to deactivate old → create new (both within same `transaction.atomic()`)
- **Files modified:** `backend/apps/industries/models.py`
- **Verification:** `pytest apps/industries/tests/test_versioning.py -x` exits 0 (4 tests pass)
- **Committed in:** `6e05855` (Task 02-08 commit)

**2. [Rule 3 - Blocking] Created Django skeleton files (Plan 01/00 not previously executed)**
- **Found during:** Task 02-01 (prerequisite check)
- **Issue:** Plan 02 assumes Django skeleton from Plan 01 (baqsy/ settings, manage.py, urls.py). Investigation showed these were already committed in a prior session (commits 5ccd56c, 8ac5ed9) — no additional work required
- **Fix:** No action needed — files confirmed in git history
- **Impact:** None

---

**Total deviations:** 1 auto-fixed (Rule 1 — Bug)
**Impact on plan:** Single bug fix needed for correctness of `create_new_version`. No scope creep.

## Issues Encountered

- Test stubs (from Plan 00 Wave 0) used `Industry.slug` instead of `Industry.code` — fixed by writing real tests matching actual model fields

## Next Phase Readiness

- All 13 models with clean migrations ready for Plan 03 (backups + seed command)
- `seed_initial` management command can now use all models
- REST API (Phase 2) has complete data model to build on
- Admin registration complete for all models — CRM admin (Phase 7) has foundation

---
*Phase: 01-infrastructure-data-model*
*Completed: 2026-04-16*
