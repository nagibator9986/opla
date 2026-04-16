---
phase: 03-telegram-bot
plan: 02
type: execute
wave: 2
title: "Questionnaire flow + 24h reminders"
depends_on: [01]
requirements: [BOT-05, BOT-06, BOT-07, BOT-10, BOT-11]
autonomous: true
files_modified:
  - bot/handlers/questionnaire.py
  - backend/apps/submissions/tasks.py
  - backend/baqsy/celery.py
nyquist_compliant: true
---

# Plan 02: Questionnaire Flow + 24h Reminders

## Goal

Implement the questionnaire handler for answering questions one-by-one with field_type-aware keyboards, progress indicator, and FSM crash recovery. Add Celery beat periodic task for 24h incomplete submission reminders.

## must_haves

- Bot handles text/number/choice/multichoice question types correctly
- Each question shows "Вопрос N/M" progress indicator
- After all questions: auto-complete + thank-you message
- FSM crash recovery: /start resumes from last unanswered question
- Celery beat sends 24h reminders via Telegram Bot API (max 1 per 24h)

## Tasks

<task id="02-01">
<title>Create questionnaire handler with field-type-aware keyboards</title>
<read_first>
- bot/handlers/start.py (_send_next_question already sends first question)
- bot/states/questionnaire.py (QuestionnaireStates)
- bot/services/api_client.py (save_answer, get_next_question, complete_submission)
- .planning/phases/03-telegram-bot/03-CONTEXT.md (question presentation decisions)
- .planning/phases/03-telegram-bot/03-RESEARCH.md (multichoice toggle, callback_data limit)
</read_first>
<action>
Create `bot/handlers/questionnaire.py`:

```python
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from bot.services import api_client
from bot.states.questionnaire import QuestionnaireStates
from bot.handlers.start import _send_next_question

router = Router()


@router.message(QuestionnaireStates.answering)
async def process_text_answer(message: Message, state: FSMContext):
    """Handle free-text or number input for current question."""
    data = await state.get_data()
    submission_id = data["submission_id"]
    jwt_token = data["jwt_token"]
    question_id = data["current_question_id"]
    field_type = data["current_field_type"]

    text = message.text.strip()

    if field_type == "number":
        try:
            num = float(text) if "." in text else int(text)
            value = {"number": num}
        except ValueError:
            await message.answer("Пожалуйста, введите число:")
            return
    else:
        value = {"text": text}

    try:
        result = await api_client.save_answer(submission_id, question_id, value, jwt_token)
    except Exception as e:
        await message.answer("Ошибка при сохранении ответа. Попробуйте ещё раз.")
        return

    await _send_next_question(message, state)


@router.callback_query(QuestionnaireStates.answering, F.data.startswith("choice:"))
async def process_choice_answer(callback: CallbackQuery, state: FSMContext):
    """Handle single-choice inline button."""
    choice = callback.data.split(":", 1)[1]
    data = await state.get_data()

    try:
        await api_client.save_answer(
            data["submission_id"],
            data["current_question_id"],
            {"choice": choice},
            data["jwt_token"],
        )
    except Exception:
        await callback.answer("Ошибка, попробуйте ещё раз")
        return

    await callback.answer()
    await _send_next_question(callback.message, state)


@router.callback_query(QuestionnaireStates.multichoice_selecting, F.data.startswith("mc:"))
async def process_multichoice_toggle(callback: CallbackQuery, state: FSMContext):
    """Toggle multichoice selection or submit on 'done'."""
    value = callback.data.split(":", 1)[1]
    data = await state.get_data()

    if value == "done":
        selected = data.get("mc_selected", [])
        if not selected:
            await callback.answer("Выберите хотя бы один вариант")
            return

        try:
            await api_client.save_answer(
                data["submission_id"],
                data["current_question_id"],
                {"choices": selected},
                data["jwt_token"],
            )
        except Exception:
            await callback.answer("Ошибка, попробуйте ещё раз")
            return

        await callback.answer()
        await state.set_state(QuestionnaireStates.answering)
        await _send_next_question(callback.message, state)
        return

    # Toggle selection
    selected = data.get("mc_selected", [])
    if value in selected:
        selected.remove(value)
    else:
        selected.append(value)
    await state.update_data(mc_selected=selected)

    # Update keyboard to show selection state
    options = data.get("current_options", {}).get("choices", [])
    kb = InlineKeyboardMarkup(inline_keyboard=[
        *[[InlineKeyboardButton(
            text=f"{'✅' if c in selected else '☐'} {c}",
            callback_data=f"mc:{c}"
        )] for c in options],
        [InlineKeyboardButton(text=f"✅ Готово ({len(selected)})", callback_data="mc:done")],
    ])
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()
```
</action>
<acceptance_criteria>
- `bot/handlers/questionnaire.py` contains `async def process_text_answer(`
- `bot/handlers/questionnaire.py` contains `async def process_choice_answer(`
- `bot/handlers/questionnaire.py` contains `async def process_multichoice_toggle(`
- `bot/handlers/questionnaire.py` contains `"choice:"` callback filter
- `bot/handlers/questionnaire.py` contains `"mc:"` callback filter
- `bot/handlers/questionnaire.py` contains `mc_selected`
</acceptance_criteria>
</task>

<task id="02-02">
<title>Create Celery task for 24h reminders</title>
<read_first>
- backend/apps/submissions/models.py (Submission, last_reminded_at)
- backend/baqsy/celery.py
- .planning/phases/03-telegram-bot/03-RESEARCH.md (Celery reminder pattern)
</read_first>
<action>
Create `backend/apps/submissions/tasks.py`:

```python
import logging
import os
from datetime import timedelta

import requests
from celery import shared_task
from django.utils import timezone

log = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
BOT_NAME = os.environ.get("TELEGRAM_BOT_USERNAME", "BaqsyBot")


@shared_task(name="submissions.remind_incomplete")
def remind_incomplete_submissions():
    """Find submissions idle for 24h+ and send Telegram reminders."""
    from apps.submissions.models import Submission
    from apps.accounts.models import ClientProfile

    cutoff = timezone.now() - timedelta(hours=24)
    reminder_cutoff = timezone.now() - timedelta(hours=24)

    submissions = Submission.objects.filter(
        status__in=["in_progress_full", "paid"],
        updated_at__lt=cutoff,
    ).filter(
        # Not reminded in last 24h
        models_Q_last_reminded=True,
    ).select_related("client")

    # Manual filter: last_reminded_at is None or < 24h ago
    from django.db.models import Q
    submissions = Submission.objects.filter(
        status__in=["in_progress_full", "paid"],
        updated_at__lt=cutoff,
    ).filter(
        Q(last_reminded_at__isnull=True) | Q(last_reminded_at__lt=reminder_cutoff)
    ).select_related("client")

    count = 0
    for sub in submissions:
        telegram_id = sub.client.telegram_id
        deeplink = f"https://t.me/{BOT_NAME}?start=questionnaire_{sub.id}"
        text = (
            "У вас есть незавершённая анкета для бизнес-аудита! 📋\n\n"
            "Продолжите заполнение, чтобы получить персональный отчёт."
        )

        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": telegram_id,
                    "text": text,
                    "reply_markup": {
                        "inline_keyboard": [[{
                            "text": "Продолжить анкету",
                            "url": deeplink,
                        }]]
                    },
                },
                timeout=10,
            )
            if resp.ok:
                sub.last_reminded_at = timezone.now()
                sub.save(update_fields=["last_reminded_at"])
                count += 1
                log.info("Reminder sent to tg_id=%s sub=%s", telegram_id, sub.id)
            else:
                log.warning("Telegram API error for tg_id=%s: %s", telegram_id, resp.text)
        except Exception as e:
            log.error("Failed to send reminder to tg_id=%s: %s", telegram_id, e)

    log.info("Reminders sent: %d", count)
    return count
```

Update `backend/baqsy/celery.py` to add beat schedule:

Add to the existing celery.py after `app.autodiscover_tasks()`:
```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    "remind-incomplete-submissions": {
        "task": "submissions.remind_incomplete",
        "schedule": crontab(hour="*/6"),  # every 6 hours
    },
}
```
</action>
<acceptance_criteria>
- `backend/apps/submissions/tasks.py` contains `def remind_incomplete_submissions():`
- `backend/apps/submissions/tasks.py` contains `api.telegram.org/bot`
- `backend/apps/submissions/tasks.py` contains `last_reminded_at`
- `backend/baqsy/celery.py` contains `remind-incomplete-submissions`
- `backend/baqsy/celery.py` contains `crontab(hour="*/6")`
</acceptance_criteria>
</task>

## Verification

```bash
python -c "from bot.handlers.questionnaire import router"  # import succeeds
python -c "from apps.submissions.tasks import remind_incomplete_submissions"  # import succeeds
```
