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
