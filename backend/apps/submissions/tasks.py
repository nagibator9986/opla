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
