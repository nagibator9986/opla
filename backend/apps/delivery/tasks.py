"""Delivery tasks.

The Telegram auto-delivery was removed with the bot. WhatsApp auto-delivery
via Wazzup24 is still wired for future use (once a real channel is configured),
but the current production flow relies on the admin manually clicking the
«💬 Отправить клиенту» WhatsApp-button in the AuditReport admin list — which
opens ``https://wa.me/<digits>?text=<encoded message + PDF URL>``.
"""
from __future__ import annotations

import logging
import os

from celery import shared_task
from django.db import transaction
from requests.exceptions import RequestException

log = logging.getLogger(__name__)


def _try_mark_delivered(report):
    """Advance the submission FSM to ``delivered`` once the PDF is out.

    In the current flow we only require the WhatsApp channel if the client
    provided a WA number. If they didn't, the submission is marked delivered
    as soon as the PDF is ready.
    """
    from apps.delivery.models import DeliveryLog
    from apps.submissions.models import Submission

    delivered = set(
        DeliveryLog.objects.filter(
            report=report, status=DeliveryLog.Status.DELIVERED,
        ).values_list("channel", flat=True)
    )
    has_wa = bool(report.submission.client and report.submission.client.phone_wa)
    required = {DeliveryLog.Channel.WHATSAPP} if has_wa else set()
    if required and not required.issubset(delivered):
        return

    with transaction.atomic():
        sub = Submission.objects.select_for_update().get(pk=report.submission_id)
        if sub.status == Submission.Status.UNDER_AUDIT:
            sub.mark_delivered()
            sub.save(update_fields=["status"])
            log.info("mark_delivered: submission=%s → delivered", sub.id)


@shared_task(name="delivery.deliver_telegram")
def deliver_telegram(report_id: str):
    """DEPRECATED — Telegram bot was removed. Kept as a no-op so legacy queued
    tasks or external callers don't crash. Always logs a warning."""
    log.warning(
        "deliver_telegram called for report=%s — Telegram delivery is deprecated, skipping",
        report_id,
    )
    return


@shared_task(
    name="delivery.deliver_whatsapp",
    bind=True,
    autoretry_for=(RequestException,),
    max_retries=5,
    retry_backoff=True,
    retry_backoff_max=300,
)
def deliver_whatsapp(self, report_id: str):
    """Deliver PDF via WhatsApp through Wazzup24 (optional, auto-mode).

    Silently skips if ``WAZZUP24_API_KEY`` / ``WAZZUP24_CHANNEL_ID`` are not
    configured — the admin should then use the manual wa.me button in the
    AuditReport admin list.
    """
    from apps.delivery.models import DeliveryLog
    from apps.reports.models import AuditReport

    report = AuditReport.objects.select_related("submission__client").get(id=report_id)
    client = report.submission.client
    api_key = os.environ.get("WAZZUP24_API_KEY", "")
    channel_id = os.environ.get("WAZZUP24_CHANNEL_ID", "")

    if not client or not client.phone_wa:
        DeliveryLog.objects.get_or_create(
            report=report,
            channel=DeliveryLog.Channel.WHATSAPP,
            defaults={"status": DeliveryLog.Status.FAILED, "error": "no_phone_wa"},
        )
        log.warning("deliver_whatsapp: no phone_wa for report=%s, skipping", report_id)
        _try_mark_delivered(report)
        return

    if not api_key or not channel_id:
        DeliveryLog.objects.get_or_create(
            report=report,
            channel=DeliveryLog.Channel.WHATSAPP,
            defaults={"status": DeliveryLog.Status.FAILED, "error": "wazzup_not_configured"},
        )
        log.info(
            "deliver_whatsapp: Wazzup24 not configured — admin should send manually "
            "via wa.me button in AuditReport admin (report=%s)",
            report_id,
        )
        return

    log_entry, _ = DeliveryLog.objects.get_or_create(
        report=report,
        channel=DeliveryLog.Channel.WHATSAPP,
        defaults={"status": DeliveryLog.Status.QUEUED},
    )
    if log_entry.status == DeliveryLog.Status.DELIVERED:
        log.info("deliver_whatsapp: already delivered for report=%s", report_id)
        return

    from apps.delivery.providers.wazzup24 import Wazzup24Provider

    provider = Wazzup24Provider(api_key=api_key, channel_id=channel_id)
    message_id = provider.send_document(
        phone=client.phone_wa,
        file_url=report.pdf_url,
        caption="Спасибо за обращение! Ваш аудит-отчёт готов.",
    )
    log_entry.status = DeliveryLog.Status.DELIVERED
    log_entry.external_id = message_id
    log_entry.save(update_fields=["status", "external_id"])
    log.info("deliver_whatsapp: done for report=%s, messageId=%s", report_id, message_id)
    _try_mark_delivered(report)
