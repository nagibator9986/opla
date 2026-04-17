"""Celery tasks for delivery app.

deliver_telegram and deliver_whatsapp are stubs in Plan 01.
Full implementation will be provided in Phase 06, Plan 02.
"""
from __future__ import annotations

import logging

from celery import shared_task

log = logging.getLogger(__name__)


@shared_task(
    name="delivery.deliver_telegram",
    bind=True,
    max_retries=5,
    retry_backoff=True,
)
def deliver_telegram(self, report_id: str):
    """Stub: deliver audit PDF via Telegram (implemented in plan 02)."""
    log.info(
        "deliver_telegram stub: report=%s (will be implemented in plan 02)", report_id
    )


@shared_task(
    name="delivery.deliver_whatsapp",
    bind=True,
    max_retries=5,
    retry_backoff=True,
)
def deliver_whatsapp(self, report_id: str):
    """Stub: deliver audit PDF via WhatsApp (implemented in plan 02)."""
    log.info(
        "deliver_whatsapp stub: report=%s (will be implemented in plan 02)", report_id
    )
