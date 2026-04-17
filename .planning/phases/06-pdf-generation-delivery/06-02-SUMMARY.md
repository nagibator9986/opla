---
phase: 06-pdf-generation-delivery
plan: 02
subsystem: delivery
tags: [celery, telegram, whatsapp, wazzup24, django-fsm, requests, delivery-pipeline]

# Dependency graph
requires:
  - phase: 06-01
    provides: generate_pdf task, AuditReport.pdf_url, DeliveryLog model, delivery task stubs

provides:
  - WhatsAppProvider ABC (providers/base.py)
  - Wazzup24Provider implementation with phone normalization (providers/wazzup24.py)
  - deliver_telegram Celery task: sendMessage + sendDocument via Bot API with autoretry
  - deliver_whatsapp Celery task: Wazzup24Provider integration with no-phone-wa skip
  - _try_mark_delivered helper with select_for_update race condition guard
  - DeliveryLog tracking: queued → delivered for both channels
  - FSM transition UNDER_AUDIT → DELIVERED via mark_delivered()
  - 16 passing tests (5 providers + 11 tasks)

affects:
  - 07-admin-crm
  - 08-hardening-launch

# Tech tracking
tech-stack:
  added: []
  patterns:
    - WhatsAppProvider ABC for provider-agnostic WA delivery
    - get_or_create for idempotent DeliveryLog on Celery retries
    - select_for_update in transaction.atomic() for concurrent mark_delivered race condition
    - autoretry_for=(RequestException,) with retry_backoff for transient network failures
    - Lazy imports inside tasks (from apps.X.models import Y) for Celery compatibility

key-files:
  created:
    - backend/apps/delivery/providers/__init__.py
    - backend/apps/delivery/providers/base.py
    - backend/apps/delivery/providers/wazzup24.py
    - backend/apps/delivery/tests/test_providers.py
    - backend/apps/delivery/tests/test_tasks.py
  modified:
    - backend/apps/delivery/tasks.py

key-decisions:
  - "Wazzup24Provider normalizes phone by stripping leading '+' — chatId must be digits-only"
  - "get_or_create for DeliveryLog on both tasks ensures idempotency across Celery retries"
  - "select_for_update inside transaction.atomic() in _try_mark_delivered prevents double mark_delivered race condition"
  - "_try_mark_delivered checks has_wa flag: if phone_wa empty, only TELEGRAM channel required for mark_delivered"
  - "WA no-phone edge case creates FAILED DeliveryLog with error=no_phone_wa (trackable in CRM)"

patterns-established:
  - "Delivery task pattern: get_or_create log → skip if DELIVERED → call external API → update log → _try_mark_delivered"
  - "Provider abstraction: WhatsAppProvider ABC allows future swap to GreenAPI without changing tasks.py"
  - "Test AuditReportFactory defined inline in test files using SubmissionFactory (avoids import cycles)"

requirements-completed:
  - DLV-01
  - DLV-02
  - DLV-03
  - DLV-04
  - DLV-05
  - DLV-06

# Metrics
duration: 8min
completed: 2026-04-17
---

# Phase 06 Plan 02: Delivery Tasks Summary

**Celery delivery pipeline closing the PDF loop — deliver_telegram (Bot API sendDocument) + deliver_whatsapp (Wazzup24Provider) with DeliveryLog tracking, select_for_update race guard, and FSM UNDER_AUDIT→DELIVERED transition**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-04-17T09:35:00Z
- **Completed:** 2026-04-17T09:38:54Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- WhatsAppProvider ABC + Wazzup24Provider implementation with phone normalization and presigned URL support
- deliver_telegram task: sends companion text (sendMessage) then PDF file (sendDocument) via Bot API, autoretry on RequestException
- deliver_whatsapp task: delegates to Wazzup24Provider, skips gracefully when phone_wa is empty (logs FAILED DeliveryLog with error=no_phone_wa)
- _try_mark_delivered: checks all required channels delivered then atomically transitions Submission UNDER_AUDIT→DELIVERED via select_for_update
- 16 passing tests covering all delivery scenarios; 0 regressions (123 total pass)

## Task Commits

1. **Task 1: WhatsAppProvider ABC + Wazzup24Provider + tests** - `2cc65b1` (feat)
2. **Task 2: deliver_telegram + deliver_whatsapp + _try_mark_delivered + tests** - `c531efb` (feat)

## Files Created/Modified
- `backend/apps/delivery/providers/__init__.py` - Package exports for WhatsAppProvider and Wazzup24Provider
- `backend/apps/delivery/providers/base.py` - Abstract WhatsAppProvider with send_document ABC
- `backend/apps/delivery/providers/wazzup24.py` - Wazzup24Provider: POST /v3/message with Bearer auth and phone normalization
- `backend/apps/delivery/providers/__init__.py` - Re-exports both classes
- `backend/apps/delivery/tasks.py` - Full delivery tasks replacing Plan 01 stubs
- `backend/apps/delivery/tests/test_providers.py` - 5 tests: abstract guard, send_document success, phone normalization, HTTP error, auth header
- `backend/apps/delivery/tests/test_tasks.py` - 11 tests: telegram flow, whatsapp flow, no-phone edge case, _try_mark_delivered variants, autoretry attribute

## Decisions Made
- Wazzup24Provider strips leading '+' from phone — chatId must be digits-only per Wazzup24 API
- get_or_create for DeliveryLog in both tasks ensures Celery retry idempotency (DLV-04)
- select_for_update inside transaction.atomic() in _try_mark_delivered prevents concurrent mark_delivered race condition
- has_wa flag in _try_mark_delivered: when phone_wa is empty, WA channel is not required — Telegram alone is sufficient for delivered transition

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Docker containers not running; ran pytest directly with system Python (python3 -m pytest in backend/). All 16 tests passed, 123 total passing.

## User Setup Required
WAZZUP24_API_KEY and WAZZUP24_CHANNEL_ID env vars must be set for WhatsApp delivery in production. TELEGRAM_BOT_TOKEN already required from prior phases.

## Next Phase Readiness
- Full delivery pipeline complete: generate_pdf (Plan 01) → deliver_telegram + deliver_whatsapp (Plan 02)
- Submission FSM lifecycle complete: created → ... → under_audit → delivered
- CRM admin (Phase 07) can trigger generate_pdf + deliver tasks via ApproveReportView
- WhatsApp provider abstraction allows future switch from Wazzup24 to GreenAPI without changing tasks.py

---
*Phase: 06-pdf-generation-delivery*
*Completed: 2026-04-17*
