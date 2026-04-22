"""Celery tasks that advance Submission FSM after payment + send reminders.

The Telegram-bot messaging code was removed — the product switched to an
AI-chat onboarding. After payment the Submission just transitions to
``in_progress_full``; the client is notified via the cabinet (frontend poll)
and a WhatsApp link the admin can trigger manually from the Reports admin.
"""
from __future__ import annotations

import logging
from datetime import timedelta

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
    """Advance the submission FSM to ``in_progress_full`` after payment.

    Previously also sent a Telegram message; that code was removed. The name
    is kept for backwards compatibility with scheduled tasks already queued
    in Redis. Consider renaming to ``advance_after_payment`` in a follow-up.
    """
    from apps.submissions.models import Submission

    try:
        sub = Submission.objects.get(id=submission_id)
    except Submission.DoesNotExist:
        log.error("advance_after_payment: submission %s not found", submission_id)
        return

    try:
        sub.start_questionnaire()
        sub.save()
        log.info("advance_after_payment: submission %s → in_progress_full", sub.id)
    except Exception as exc:
        log.warning(
            "advance_after_payment: FSM start_questionnaire failed for sub=%s: %s "
            "(may already be transitioned)",
            sub.id,
            exc,
        )


@shared_task(name="submissions.remind_incomplete")
def remind_incomplete_submissions():
    """Stub — previously sent Telegram reminders. AI-chat flow doesn't push
    outbound messages, so this is a no-op that just logs pending submissions.
    """
    from django.db.models import Q

    from apps.submissions.models import Submission

    cutoff = timezone.now() - timedelta(hours=24)
    pending = Submission.objects.filter(
        status__in=["in_progress_full", "paid"],
        updated_at__lt=cutoff,
    ).filter(
        Q(last_reminded_at__isnull=True) | Q(last_reminded_at__lt=cutoff)
    ).count()

    log.info("reminder scan: %d idle submissions (no outbound channel wired)", pending)
    return pending
