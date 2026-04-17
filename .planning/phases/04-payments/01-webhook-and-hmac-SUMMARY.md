---
phase: 04-payments
plan: 01
subsystem: payments
tags: [cloudpayments, webhook, hmac, fsm, celery]
dependency_graph:
  requires: [apps.submissions.models.Submission, apps.payments.models.Payment, apps.payments.models.Tariff]
  provides: [CloudPaymentsCheckView, CloudPaymentsPayView, TariffListView, validate_hmac, notify_bot_payment_success]
  affects: [apps.core.api_urls, apps.submissions.tasks, baqsy.settings.base]
tech_stack:
  added: []
  patterns: [HMAC-SHA256 constant-time verification, get_or_create idempotency, select_for_update FSM transition, Celery retry with exponential backoff]
key_files:
  created:
    - backend/apps/payments/services.py
    - backend/apps/payments/views.py
    - backend/apps/payments/serializers.py
    - backend/apps/payments/urls.py
    - backend/apps/payments/tests/test_webhook.py
  modified:
    - backend/baqsy/settings/base.py
    - backend/apps/core/api_urls.py
    - backend/apps/submissions/tasks.py
decisions:
  - Payment FK requires submission before get_or_create — restructured Pay view to find submission first, then use it in defaults
  - mark_paid() requires in_progress_basic — view auto-advances created→in_progress_basic for payments that arrive before onboarding
  - override_settings must decorate individual methods in pytest class (not the class itself)
metrics:
  duration_seconds: 167
  completed_date: "2026-04-17"
  tasks_completed: 3
  files_changed: 8
---

# Phase 4 Plan 01: CloudPayments Webhook + HMAC Summary

**One-liner:** CloudPayments HMAC-SHA256 webhook endpoints (Check + Pay) with idempotent Payment creation, FSM Submission transition to `paid`, Celery bot-notify task, and public tariff list API.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 01-01 | Create HMAC validation service | 31302e6 | services.py, settings/base.py |
| 01-02 | Create webhook views + tariff list | 632a0c2 | views.py, serializers.py, urls.py, api_urls.py, submissions/tasks.py |
| 01-03 | Write webhook tests | 417f247 | tests/test_webhook.py, views.py (FSM fix) |

## What Was Built

### HMAC Validation Service (`apps/payments/services.py`)
- `validate_hmac(body: bytes, received_hmac: str) -> bool`
- `hmac.compare_digest` for constant-time comparison (timing-attack safe)
- Reads `CLOUDPAYMENTS_API_SECRET` from Django settings

### Webhook Views (`apps/payments/views.py`)
- **`CloudPaymentsCheckView`** — Pre-authorisation check: validates HMAC, verifies submission existence, checks status in `{created, in_progress_basic}`, validates amount vs tariff price
- **`CloudPaymentsPayView`** — Payment confirmation: validates HMAC, finds submission with `select_for_update()`, creates Payment via `get_or_create(transaction_id=...)`, advances FSM to `paid`, enqueues `notify_bot_payment_success` Celery task
- Both views: `AllowAny`, `authentication_classes=[]`, `@csrf_exempt`
- **`TariffListView`** — Public `GET /api/v1/payments/tariffs/` returning active tariffs

### Bot Notification Task (`apps/submissions/tasks.py`)
- `notify_bot_payment_success(submission_id)` — sends Telegram message with deep-link to questionnaire
- `max_retries=3` with exponential backoff (`2^n * 5s`)

### URL Wiring
- `apps/payments/urls.py` — 3 paths: `tariffs/`, `cloudpayments/check/`, `cloudpayments/pay/`
- `apps/core/api_urls.py` — includes `payments/`

### Tests (8 total, 5 new)
- `test_check_valid_returns_code_0` — valid HMAC + matching amount → 200 + `{"code": 0}`
- `test_check_invalid_hmac_returns_400` — bad HMAC → 400
- `test_pay_creates_payment_and_marks_paid` — creates Payment, transitions Submission to paid, calls notify task
- `test_pay_idempotent_duplicate` — second call with same TransactionId → `{"code": 0}`, no duplicate Payment
- `test_tariffs_list` — returns only active tariffs

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Payment FK requires non-null submission before get_or_create**
- **Found during:** Task 02
- **Issue:** Plan's code does `Payment.objects.get_or_create(transaction_id=..., defaults={amount, currency, status, raw_webhook})` then assigns `payment.submission = sub` after. But `Payment.submission` is a required FK (non-null) — Django would raise IntegrityError on the INSERT.
- **Fix:** Restructured CloudPaymentsPayView to look up Submission first (with `select_for_update()`), then pass it in `get_or_create` defaults. Maintains full idempotency — duplicate TransactionId still returns `{"code": 0}` without side effects.
- **Files modified:** `backend/apps/payments/views.py`
- **Commit:** 632a0c2

**2. [Rule 1 - Bug] mark_paid() requires in_progress_basic status, not created**
- **Found during:** Task 03 (test failure analysis)
- **Issue:** Plan fixture creates Submission at default `created` status. The `mark_paid()` FSM transition only allows source `in_progress_basic`. Calling it on a `created` submission raises TransitionNotAllowed.
- **Fix:** View now auto-advances `created→in_progress_basic` via `start_onboarding()` before calling `mark_paid()` (payment can legitimately arrive before onboarding completes). Test fixture also explicitly advances submission to `in_progress_basic` for realistic test setup.
- **Files modified:** `backend/apps/payments/views.py`, `backend/apps/payments/tests/test_webhook.py`
- **Commit:** 417f247

**3. [Rule 1 - Bug] @override_settings cannot decorate plain pytest class**
- **Found during:** Task 03 (collection error)
- **Issue:** Django's `@override_settings` raises `ValueError: Only subclasses of Django SimpleTestCase can be decorated with override_settings` when applied to a plain class.
- **Fix:** Moved `@override_settings(CLOUDPAYMENTS_API_SECRET=TEST_SECRET)` from class level to individual test methods.
- **Files modified:** `backend/apps/payments/tests/test_webhook.py`
- **Commit:** 417f247

## Self-Check: PASSED

All 5 created/modified key files verified present on disk. All 3 task commits verified in git log.
