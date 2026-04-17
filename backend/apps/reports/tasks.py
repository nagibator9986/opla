"""Celery tasks for PDF generation."""
from __future__ import annotations

import logging

from celery import shared_task

log = logging.getLogger(__name__)


@shared_task(
    name="reports.generate_pdf",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def generate_pdf(self, report_id: str):
    """Generate PDF for an AuditReport and upload to MinIO.

    Idempotent: if report.pdf_url is already set, returns immediately (PDF-07).
    On failure retries up to 3 times with 60s delay.
    """
    from apps.reports.models import AuditReport
    from apps.reports.services import render_pdf, upload_pdf_to_minio

    try:
        report = AuditReport.objects.select_related(
            "submission__client__industry",
            "submission__tariff",
        ).get(id=report_id)
    except AuditReport.DoesNotExist:
        log.error("generate_pdf: report %s not found", report_id)
        return

    # Idempotency check (PDF-07)
    if report.pdf_url:
        log.info("generate_pdf: already exists for report=%s", report_id)
        return

    try:
        pdf_bytes = render_pdf(report)
        presigned_url = upload_pdf_to_minio(pdf_bytes, str(report.submission_id))

        report.pdf_url = presigned_url
        report.save(update_fields=["pdf_url"])
        log.info("generate_pdf: done for report=%s url=%s...", report_id, presigned_url[:40])
    except Exception as exc:
        log.error("generate_pdf: failed for report=%s: %s", report_id, exc)
        raise self.retry(exc=exc)
