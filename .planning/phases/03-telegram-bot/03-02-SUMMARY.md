---
phase: 03-telegram-bot
plan: 02
subsystem: bot
tags: [aiogram, celery, celery-beat, telegram, fsm, questionnaire, reminders]

requires:
  - phase: 03-telegram-bot-01
    provides: questionnaire.py stub, _send_next_question in start.py, QuestionnaireStates FSM

provides:
  - Full questionnaire handler with text/number/choice/multichoice field types
  - Multichoice toggle with checkmark (checkmark/checkbox) visual state in inline keyboard
  - Celery shared task remind_incomplete_submissions for 24h idle reminders
  - Celery beat schedule firing every 6h to check for idle submissions

affects: [04-payment-integration, 05-pdf-generation, 06-whatsapp-delivery]

tech-stack:
  added: []
  patterns:
    - "value dict pattern: answer value always a dict {text:..}, {number:..}, {choice:..}, {choices:[..]}"
    - "Celery reminder: Q(last_reminded_at__isnull=True) | Q(last_reminded_at__lt=cutoff) for idempotent 24h gate"
    - "Multichoice toggle: state.update_data(mc_selected=[...]) + edit_reply_markup() for in-place keyboard update"

key-files:
  created:
    - bot/handlers/questionnaire.py
    - backend/apps/submissions/tasks.py
  modified:
    - backend/baqsy/celery.py

key-decisions:
  - "Answer value always a dict — {text:.., number:.., choice:.., choices:[..]} — consistent with Answer.value JSONField model"
  - "Bug in plan code fixed: removed duplicated/invalid models_Q_last_reminded filter; kept only correct Q() ORM filter"
  - "Multichoice done button shows selected count: '✅ Готово (N)' for better UX clarity"

patterns-established:
  - "value dict: always wrap answers in typed dict before save_answer call"
  - "try/except on every api_client call in bot handlers — graceful error message, no crash"

requirements-completed: [BOT-05, BOT-06, BOT-07, BOT-10, BOT-11]

duration: 5min
completed: 2026-04-16
---

# Phase 03 Plan 02: Questionnaire Flow + 24h Reminders Summary

**Full questionnaire FSM handler with field-type-aware keyboards (text/number/choice/multichoice) and Celery beat 24h reminder task using idempotent Q() filter**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-04-16T10:37:57Z
- **Completed:** 2026-04-16T10:42:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Replaced questionnaire.py stub with production handler: text/number validation, typed value dicts, error handling per handler
- Multichoice toggle pattern: in-place keyboard edit with checkmark/checkbox visual indicators and "Gotovo (N)" count on done button
- remind_incomplete_submissions Celery task with proper Q() ORM filter for idempotent 24h gate + Telegram Bot API direct call
- Beat schedule appended to celery.py: every 6 hours via crontab(hour="*/6")

## Task Commits

1. **Task 02-01: Full questionnaire handler** - `1c13ba4` (feat)
2. **Task 02-02: Celery reminder task + beat schedule** - `50112f9` (feat)

## Files Created/Modified

- `bot/handlers/questionnaire.py` - Replaced stub: process_text_answer, process_choice_answer, process_multichoice_toggle with typed value dicts and error handling
- `backend/apps/submissions/tasks.py` - Created: remind_incomplete_submissions shared task, Telegram Bot API POST, last_reminded_at update
- `backend/baqsy/celery.py` - Appended beat_schedule with crontab(hour="*/6") for 6h reminder checks

## Decisions Made

- Answer value always a dict: `{"text": ..}`, `{"number": ..}`, `{"choice": ..}`, `{"choices": [...]}` — consistent with `Answer.value` JSONField contract in the model
- Bug in plan code fixed: plan contained duplicate query with invalid `models_Q_last_reminded=True` filter; removed the first (broken) query, kept only the correct Q() filter version
- Multichoice done button shows live count (`Gotovo (N)`) — minor UX improvement over plain "Gotovo"

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed broken duplicate query in reminder task**
- **Found during:** Task 02-02 (Celery reminder task)
- **Issue:** Plan code had a first `.filter(models_Q_last_reminded=True)` query that referenced a nonexistent attribute, followed by a second correct query reassigning the same variable. The first query would raise AttributeError.
- **Fix:** Removed the broken first query entirely; kept only the correct Q()-based filter. Single query with correct ORM semantics.
- **Files modified:** backend/apps/submissions/tasks.py
- **Verification:** All 15 acceptance criteria pass in file content check
- **Committed in:** `50112f9` (Task 02-02 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** Essential correctness fix. No scope change.

## Issues Encountered

None beyond the plan bug fixed above.

## User Setup Required

None - no external service configuration required for this plan. TELEGRAM_BOT_TOKEN and TELEGRAM_BOT_USERNAME env vars are already in .env.example from Plan 01.

## Next Phase Readiness

- Questionnaire flow fully functional end-to-end (bot side)
- 24h reminders operational via Celery beat
- Ready for Phase 04 (payment integration): CloudPayments webhook triggers Submission.mark_paid() and bot notification

---
*Phase: 03-telegram-bot*
*Completed: 2026-04-16*
