"""PDF generation service for Baqsy audit reports.

Provides two public functions:
  - render_pdf(report) -> bytes    : Jinja2 + WeasyPrint HTML-to-PDF
  - upload_pdf_to_minio(pdf_bytes, submission_id) -> str  : boto3 S3 upload + presigned URL
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.utils import timezone

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from apps.reports.models import AuditReport


def _format_answer_value(value_dict: dict) -> str:
    """Jinja2 filter: convert Answer.value JSON dict to human-readable string.

    Handles all typed formats:
      {"text": "foo"}            -> "foo"
      {"number": 42}             -> "42"
      {"choice": "option"}       -> "option"
      {"choices": ["a", "b"]}    -> "a, b"
    Falls back to str(value_dict) for unexpected formats.
    """
    if not isinstance(value_dict, dict):
        return str(value_dict)

    if "text" in value_dict:
        return str(value_dict["text"])
    if "number" in value_dict:
        return str(value_dict["number"])
    if "choice" in value_dict:
        return str(value_dict["choice"])
    if "choices" in value_dict:
        choices = value_dict["choices"]
        if isinstance(choices, list):
            return ", ".join(str(c) for c in choices)
        return str(choices)

    # Fallback: return first non-null value found
    for v in value_dict.values():
        if v is not None:
            return str(v)
    return ""


def approve_report(report: "AuditReport") -> tuple[bool, str | None]:
    """Утвердить отчёт: меняет статусы заявки и отчёта, ставит PDF в очередь.

    Возвращает ``(success: bool, error_message: str | None)``.

    Используется И из admin (response_change/actions), И из API (ApproveReportView):
    единая бизнес-логика без дублирования. См. CLAUDE.md §13.1 — не звать DRF
    views из admin, использовать helper.
    """
    has_text = bool((report.admin_text or "").strip())
    has_file = bool(report.uploaded_file)
    if not has_text and not has_file:
        return False, "Загрузите PDF/DOCX или заполните текст отчёта."

    sub = report.submission
    if sub.status == "completed":
        try:
            sub.start_audit()
            sub.save(update_fields=["status"])
            log.info("approve_report: sub=%s → under_audit", sub.id)
        except Exception as exc:
            log.warning(
                "approve_report: FSM failed sub=%s: %s", sub.id, exc
            )

    update_fields = []
    if report.status == "draft":
        report.status = "approved"
        update_fields.append("status")
    if not report.approved_at:
        report.approved_at = timezone.now()
        update_fields.append("approved_at")
    if update_fields:
        report.save(update_fields=update_fields)

    from apps.reports.tasks import generate_pdf
    generate_pdf.delay(str(report.id))

    log.info("approve_report: approved + queued report=%s", report.id)
    return True, None


def mark_report_delivered(report: "AuditReport") -> tuple[bool, str | None]:
    """Пометить отчёт доставленным клиенту: заявка → delivered, отчёт → sent.

    Возвращает ``(success: bool, error_message: str | None)``.
    """
    sub = report.submission
    if sub.status == "delivered":
        return True, "Уже доставлено."
    if sub.status != "under_audit":
        return False, (
            f"Нельзя пометить доставленным из «{sub.get_status_display()}». "
            "Сначала утвердите отчёт."
        )
    try:
        sub.mark_delivered()
        sub.save(update_fields=["status"])
        report.status = "sent"
        report.save(update_fields=["status"])
        log.info("mark_report_delivered: sub=%s done", sub.id)
        return True, None
    except Exception as exc:
        log.warning("mark_report_delivered: failed sub=%s: %s", sub.id, exc)
        return False, str(exc)


def _load_donation_context() -> dict:
    """Подтягивает донат-блок из ContentBlock'ов в PDF-контекст.

    Если в БД нет такого блока — используется fallback из правил seed_content.
    Так PDF всё равно отрендерится корректно даже если админ удалил блок.
    """
    from apps.content.models import ContentBlock

    keys = [
        "donation_title",
        "donation_message",
        "donation_card_number",
        "donation_card_holder",
        "donation_card_bank",
    ]
    blocks = {
        cb.key: cb.content
        for cb in ContentBlock.objects.filter(key__in=keys, is_active=True)
    }
    return {k: blocks.get(k, "") for k in keys}


def render_pdf(report: "AuditReport") -> bytes:
    """Render audit report as PDF bytes using Jinja2 + WeasyPrint.

    The Jinja2 environment points at backend/templates/pdf/ so styles.css
    is resolved via relative URL by WeasyPrint's base_url.
    """
    import jinja2
    from weasyprint import HTML

    templates_dir = str(settings.BASE_DIR / "templates" / "pdf")

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(templates_dir),
        autoescape=True,
    )
    env.filters["format_answer_value"] = _format_answer_value

    template = env.get_template("audit_report.html")

    submission = report.submission
    client = submission.client
    tariff = submission.tariff
    answers = submission.answers.select_related("question").order_by("question__order")
    generated_at = timezone.now()

    context = {
        "report": report,
        "submission": submission,
        "client": client,
        "tariff": tariff,
        "answers": list(answers),
        "generated_at": generated_at,
        **_load_donation_context(),
    }

    html_str = template.render(**context)

    pdf_bytes = HTML(
        string=html_str,
        base_url=templates_dir,
    ).write_pdf()

    log.info("render_pdf: rendered %d bytes for report=%s", len(pdf_bytes), report.pk)
    return pdf_bytes


def upload_pdf_to_minio(pdf_bytes: bytes, submission_id: str) -> str:
    """Upload PDF bytes to MinIO (S3-compatible) and return a presigned URL.

    boto3 client is created inside this function to avoid fork-safety issues
    with Celery prefork workers.
    """
    import boto3

    s3 = boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )

    key = f"pdfs/{submission_id}/{int(timezone.now().timestamp())}.pdf"

    s3.put_object(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=key,
        Body=pdf_bytes,
        ContentType="application/pdf",
    )

    presigned_url = s3.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
            "Key": key,
        },
        ExpiresIn=settings.AWS_QUERYSTRING_EXPIRE,
    )

    log.info("upload_pdf_to_minio: uploaded key=%s url_len=%d", key, len(presigned_url))
    return presigned_url
