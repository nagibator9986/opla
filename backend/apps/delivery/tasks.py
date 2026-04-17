"""Celery tasks for PDF delivery via Telegram and WhatsApp."""
from __future__ import annotations

import logging
import os

import requests
from celery import shared_task
from django.db import transaction
from requests.exceptions import RequestException

log = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")


def _try_mark_delivered(report):
    """Check if both channels delivered; if so, transition FSM to delivered.

    Uses select_for_update to prevent race condition between
    deliver_telegram and deliver_whatsapp completing simultaneously.
    """
    from apps.delivery.models import DeliveryLog
    from apps.submissions.models import Submission

    delivered_channels = set(
        DeliveryLog.objects.filter(
            report=report,
            status=DeliveryLog.Status.DELIVERED,
        ).values_list("channel", flat=True)
    )

    # Если у клиента нет WA-номера, достаточно только Telegram
    has_wa = bool(report.submission.client.phone_wa)
    required = {DeliveryLog.Channel.TELEGRAM}
    if has_wa:
        required.add(DeliveryLog.Channel.WHATSAPP)

    if not required.issubset(delivered_channels):
        return

    with transaction.atomic():
        sub = Submission.objects.select_for_update().get(pk=report.submission_id)
        if sub.status == Submission.Status.UNDER_AUDIT:
            sub.mark_delivered()
            sub.save(update_fields=["status"])
            log.info("mark_delivered: submission=%s → delivered", sub.id)


@shared_task(
    name="delivery.deliver_telegram",
    bind=True,
    autoretry_for=(RequestException,),
    max_retries=5,
    retry_backoff=True,
    retry_backoff_max=300,
)
def deliver_telegram(self, report_id: str):
    """Deliver PDF to client via Telegram Bot API sendDocument (DLV-01)."""
    from apps.delivery.models import DeliveryLog
    from apps.reports.models import AuditReport

    report = AuditReport.objects.select_related("submission__client").get(id=report_id)

    # Idempotent: get_or_create prevents duplicates on retry (DLV-04)
    log_entry, _ = DeliveryLog.objects.get_or_create(
        report=report,
        channel=DeliveryLog.Channel.TELEGRAM,
        defaults={"status": DeliveryLog.Status.QUEUED},
    )

    # Skip if already delivered
    if log_entry.status == DeliveryLog.Status.DELIVERED:
        log.info("deliver_telegram: already delivered for report=%s", report_id)
        return

    telegram_id = report.submission.client.telegram_id

    # 1. Сопроводительный текст (DLV-06)
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": telegram_id,
            "text": "Спасибо за обращение! Ваш аудит-отчёт готов. 📄",
        },
        timeout=10,
    ).raise_for_status()

    # 2. Скачать PDF и отправить как файл (DLV-01)
    pdf_resp = requests.get(report.pdf_url, timeout=30)
    pdf_resp.raise_for_status()
    pdf_bytes = pdf_resp.content

    doc_resp = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
        data={"chat_id": telegram_id},
        files={"document": ("audit_report.pdf", pdf_bytes, "application/pdf")},
        timeout=30,
    )
    doc_resp.raise_for_status()
    message_id = doc_resp.json()["result"]["message_id"]

    # Update DeliveryLog (DLV-04)
    log_entry.status = DeliveryLog.Status.DELIVERED
    log_entry.external_id = str(message_id)
    log_entry.save(update_fields=["status", "external_id"])

    log.info("deliver_telegram: done for report=%s, message_id=%s", report_id, message_id)
    _try_mark_delivered(report)


@shared_task(
    name="delivery.deliver_whatsapp",
    bind=True,
    autoretry_for=(RequestException,),
    max_retries=5,
    retry_backoff=True,
    retry_backoff_max=300,
)
def deliver_whatsapp(self, report_id: str):
    """Deliver PDF to client via WhatsApp through Wazzup24 (DLV-02)."""
    from apps.delivery.models import DeliveryLog
    from apps.reports.models import AuditReport

    report = AuditReport.objects.select_related("submission__client").get(id=report_id)
    client = report.submission.client

    # Edge case: клиент без WhatsApp-номера — skip delivery
    if not client.phone_wa:
        log_entry, _ = DeliveryLog.objects.get_or_create(
            report=report,
            channel=DeliveryLog.Channel.WHATSAPP,
            defaults={
                "status": DeliveryLog.Status.FAILED,
                "error": "no_phone_wa",
            },
        )
        log.warning("deliver_whatsapp: no phone_wa for report=%s, skipping", report_id)
        _try_mark_delivered(report)
        return

    # Idempotent: get_or_create (DLV-04)
    log_entry, _ = DeliveryLog.objects.get_or_create(
        report=report,
        channel=DeliveryLog.Channel.WHATSAPP,
        defaults={"status": DeliveryLog.Status.QUEUED},
    )

    if log_entry.status == DeliveryLog.Status.DELIVERED:
        log.info("deliver_whatsapp: already delivered for report=%s", report_id)
        return

    # Send via Wazzup24Provider (DLV-02, DLV-03)
    from apps.delivery.providers.wazzup24 import Wazzup24Provider

    provider = Wazzup24Provider(
        api_key=os.environ.get("WAZZUP24_API_KEY", ""),
        channel_id=os.environ.get("WAZZUP24_CHANNEL_ID", ""),
    )
    caption = "Спасибо за обращение! Ваш аудит-отчёт готов."
    message_id = provider.send_document(
        phone=client.phone_wa,
        file_url=report.pdf_url,
        caption=caption,
    )

    # Update DeliveryLog (DLV-04)
    log_entry.status = DeliveryLog.Status.DELIVERED
    log_entry.external_id = message_id
    log_entry.save(update_fields=["status", "external_id"])

    log.info("deliver_whatsapp: done for report=%s, messageId=%s", report_id, message_id)
    _try_mark_delivered(report)
