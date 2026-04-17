---
phase: 04-payments
plan: 02
subsystem: payments
tags: [celery, telegram, upsell, cloudpayments, fsm]
dependency_graph:
  requires: [04-01]
  provides: [PAY-06, PAY-07, PAY-08]
  affects: [submissions, payments, bot]
tech_stack:
  added: []
  patterns:
    - Celery bind=True with exponential backoff retry
    - FSM transition in Celery task before external API call
    - JWT-protected DRF view resolving client via synthetic email
    - Upsell tariff upgrade inside atomic Pay webhook block
key_files:
  created:
    - backend/apps/payments/tests/test_upsell.py
  modified:
    - backend/apps/submissions/tasks.py
    - backend/apps/payments/views.py
    - backend/apps/payments/urls.py
decisions:
  - Upsell tariff upgrade (sub.tariff = ashide_2) placed inside transaction.atomic() block in PayView to ensure atomicity with Payment creation
  - notify_bot_payment_success performs FSM start_questionnaire() with silent catch — task may retry and submission may already be transitioned
  - UpsellView reuses _get_client_profile() from submissions.views for consistent JWT identity resolution
  - Upsell status check uses Submission.Status enum constants, not raw strings
metrics:
  duration_seconds: 137
  completed_date: "2026-04-16"
  tasks_completed: 3
  files_changed: 4
---

# Phase 04 Plan 02: Bot Payment Notification + Upsell Summary

**One-liner:** Celery task notifying bot users of payment success (with FSM transition + Telegram deep-link) and JWT-protected upsell endpoint upgrading Ashide 1 → 2 via CloudPayments Widget.

## What Was Built

### Task 02-01: FSM transition in notify_bot_payment_success

Added `sub.start_questionnaire()` + `sub.save()` call to the existing `notify_bot_payment_success` Celery task. The FSM transition (`paid → in_progress_full`) now happens before the Telegram message is dispatched. Errors are caught and logged silently (idempotent — task may be retried and submission may already be transitioned).

**Files:** `backend/apps/submissions/tasks.py`
**Commit:** 5ebed11

### Task 02-02: UpsellView + Pay webhook upsell upgrade

Added `UpsellView` (JWT-protected) at `POST /api/v1/payments/upsell/`. Validates:
- `submission_id` present
- JWT user resolves to a `ClientProfile` (via `_get_client_profile`)
- Submission belongs to that client
- Current tariff is `ashide_1`
- Status is `completed`, `under_audit`, or `delivered`

Returns CloudPayments Widget config (publicId, amount=90000, currency=KZT, invoiceId, description, accountId, tariff_code).

Extended `CloudPaymentsPayView.post()` to detect `payment.tariff.code == "upsell"` and upgrade `sub.tariff` to `ashide_2` inside the `transaction.atomic()` block.

**Files:** `backend/apps/payments/views.py`, `backend/apps/payments/urls.py`
**Commit:** fdf177b

### Task 02-03: Tests

Created `backend/apps/payments/tests/test_upsell.py` with 10 tests:

**TestUpsellView (7 tests):**
- Happy path returns correct CP Widget payload
- Rejects non-ashide_1 tariff (400)
- Rejects incomplete submission (400)
- Requires authentication (401)
- Rejects wrong owner — no ClientProfile (403)
- Rejects missing submission_id (400)
- Rejects non-existent submission UUID (404)

**TestNotifyBotPayment (3 tests):**
- Sends POST to `api.telegram.org` with correct `chat_id`
- Skips without calling Telegram when submission not found
- Retries when Telegram API returns non-OK response

Full suite: 36 tests pass (payments + submissions).

**Commit:** e1bbfbb

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical Functionality] FSM transition was missing in existing task**

- **Found during:** Task 02-01
- **Issue:** `notify_bot_payment_success` task existed in tasks.py from Phase 3/4 work but was missing the required `sub.start_questionnaire()` FSM call specified in plan acceptance criteria and CONTEXT.md
- **Fix:** Added FSM transition block before Telegram message dispatch, with silent exception logging for idempotency on retries
- **Files modified:** `backend/apps/submissions/tasks.py`
- **Commit:** 5ebed11

**2. [Rule 1 - Bug] Test fixture needed proper FSM advancement for completed status**

- **Found during:** Task 02-03
- **Issue:** Plan's test fixture set `status="completed"` directly, but FSM field requires proper transitions (cannot set directly without bypassing django-fsm)
- **Fix:** Fixture advances submission through full FSM chain (`start_onboarding → mark_paid → start_questionnaire → complete_questionnaire`) then saves; notification test resets back to `paid` via `Submission.objects.filter().update()` (bypasses FSM as intended for test setup)
- **Files modified:** `backend/apps/payments/tests/test_upsell.py`
- **Commit:** e1bbfbb

## Self-Check: PASSED

All files present. All 3 commits found in git log.
