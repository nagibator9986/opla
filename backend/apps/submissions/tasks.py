import logging
import os
from datetime import timedelta

import requests
from celery import shared_task
from django.utils import timezone

log = logging.getLogger(__name__)


@shared_task(
    name="submissions.notify_bot_payment_success",
    bind=True,
    max_retries=3,
    default_retry_delay=5,
)
def notify_bot_payment_success(self, submission_id: str):
    """Notify the Telegram bot that a submission has been paid.

    Sends a Telegram message with a deep-link to start the questionnaire.
    Retries up to 3 times with exponential back-off on Telegram API errors.
    """
    from apps.submissions.models import Submission

    try:
        sub = Submission.objects.select_related("client").get(id=submission_id)
    except Submission.DoesNotExist:
        log.error("notify_bot_payment_success: submission %s not found", submission_id)
        return

    telegram_id = sub.client.telegram_id
    deeplink = f"https://t.me/{BOT_NAME}?start=questionnaire_{sub.id}"
    text = (
        "Оплата прошла успешно! \U0001f389\n\n"
        "Теперь вы можете начать заполнение анкеты для бизнес-аудита. "
        "Нажмите кнопку ниже, чтобы продолжить."
    )

    # FSM: paid → in_progress_full
    try:
        sub.start_questionnaire()
        sub.save()
    except Exception as fsm_exc:
        log.warning(
            "notify_bot_payment_success: FSM start_questionnaire failed for sub=%s: %s "
            "(may already be transitioned)",
            sub.id,
            fsm_exc,
        )

    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": telegram_id,
                "text": text,
                "reply_markup": {
                    "inline_keyboard": [[
                        {
                            "text": "Начать анкету",
                            "url": deeplink,
                        }
                    ]]
                },
            },
            timeout=10,
        )
        if resp.ok:
            log.info(
                "notify_bot_payment_success: notified tg_id=%s for sub=%s",
                telegram_id,
                submission_id,
            )
        else:
            log.warning(
                "notify_bot_payment_success: Telegram API error for tg_id=%s: %s",
                telegram_id,
                resp.text,
            )
            raise self.retry(countdown=2 ** self.request.retries * 5)
    except requests.RequestException as exc:
        log.error(
            "notify_bot_payment_success: network error for tg_id=%s: %s",
            telegram_id,
            exc,
        )
        raise self.retry(exc=exc, countdown=2 ** self.request.retries * 5)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
BOT_NAME = os.environ.get("TELEGRAM_BOT_USERNAME", "BaqsyBot")


@shared_task(name="submissions.remind_incomplete")
def remind_incomplete_submissions():
    """Find submissions idle for 24h+ and send Telegram reminders (max 1 per 24h)."""
    from django.db.models import Q

    from apps.submissions.models import Submission

    cutoff = timezone.now() - timedelta(hours=24)
    reminder_cutoff = timezone.now() - timedelta(hours=24)

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
            "У вас есть незавершённая анкета для бизнес-аудита! \U0001f4cb\n\n"
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
