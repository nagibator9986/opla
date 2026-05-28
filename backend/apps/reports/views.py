"""Views for the reports app."""
from __future__ import annotations

import logging
import re

from django.conf import settings
from django.http import FileResponse, Http404
from django.utils import timezone
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reports.models import AuditReport
from apps.submissions.models import Submission

log = logging.getLogger(__name__)


# Извлекает S3 object key из MinIO presigned URL.
# Пример: http://minio:9000/baqsy/pdfs/uuid/123.pdf?... → pdfs/uuid/123.pdf
_PDF_KEY_RE = re.compile(r"^https?://[^/]+/[^/]+/(pdfs/[^?]+)")


def _extract_object_key(pdf_url: str) -> str | None:
    m = _PDF_KEY_RE.match(pdf_url or "")
    return m.group(1) if m else None


class DownloadReportPdfView(APIView):
    """GET /api/v1/submissions/{submission_id}/pdf/ — публичная отдача PDF.

    Зачем view (а не прямая ссылка на MinIO):
      • MinIO живёт во внутренней Docker-сети (`http://minio:9000`) и не
        проксируется наружу через nginx — публичная ссылка работать не
        будет.
      • Django стримит файл из MinIO клиенту, скрывая внутренний endpoint.
      • Логика permissions может быть расширена (например, требовать токен
        в URL — сейчас полагаемся на UUID submission как на «секрет»).

    Url namespace: settings.SITE_URL/api/v1/submissions/{id}/pdf/.
    """

    permission_classes = [AllowAny]

    def get(self, request, submission_id):
        try:
            submission = Submission.objects.select_related("report", "client").get(
                id=submission_id
            )
        except Submission.DoesNotExist:
            raise Http404("Заявка не найдена.")

        report = getattr(submission, "report", None)
        if not report or not report.pdf_url:
            raise Http404("PDF ещё не готов.")

        object_key = _extract_object_key(report.pdf_url)
        if not object_key:
            log.error("DownloadReportPdfView: cannot extract S3 key from %s", report.pdf_url)
            return Response({"detail": "internal error"}, status=500)

        import boto3
        from botocore.exceptions import ClientError

        s3 = boto3.client(
            "s3",
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

        try:
            obj = s3.get_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=object_key,
            )
        except ClientError as exc:
            log.warning(
                "DownloadReportPdfView: S3 get_object failed for key=%s: %s",
                object_key, exc,
            )
            raise Http404("PDF не найден в хранилище.")

        client = submission.client
        filename_safe = "audit_report"
        if client and client.company:
            slug = re.sub(r"[^\w\-]+", "_", client.company)[:40]
            filename_safe = f"baqsy_{slug}"

        response = FileResponse(
            obj["Body"],
            content_type="application/pdf",
            as_attachment=False,
            filename=f"{filename_safe}.pdf",
        )
        return response


class ApproveReportView(APIView):
    """POST /api/v1/reports/{report_id}/approve/ — staff approves + generates PDF.

    Flow:
    - Staff user writes `admin_text` in admin → clicks «Подтвердить и отправить PDF»
    - This view transitions the submission FSM to `under_audit`, sets `approved_at`,
      and queues ``generate_pdf`` — which renders the WeasyPrint template, uploads
      to MinIO, and stores the presigned URL on ``report.pdf_url``.
    - Once PDF is ready the admin sees the green «💬 Отправить клиенту» button in
      the reports list and clicks it — opens WhatsApp with a pre-filled message
      containing the client's name, company, and PDF link.

    The legacy Telegram/WhatsApp auto-delivery chain (``deliver_telegram``,
    ``deliver_whatsapp``) was removed along with the bot — manual WA send
    is now the single delivery path.
    """

    permission_classes = [IsAdminUser]

    def post(self, request, report_id):
        try:
            report = AuditReport.objects.select_related("submission").get(id=report_id)
        except AuditReport.DoesNotExist:
            return Response({"detail": "Report not found."}, status=404)

        if not report.admin_text or not report.admin_text.strip():
            return Response(
                {"error": "admin_text is required before approval"},
                status=400,
            )

        sub = report.submission

        # FSM: completed → under_audit (idempotent when already under_audit)
        if sub.status == Submission.Status.COMPLETED:
            try:
                sub.start_audit()
                sub.save(update_fields=["status"])
                log.info("ApproveReportView: sub=%s → under_audit", sub.id)
            except Exception as exc:
                log.warning(
                    "ApproveReportView: FSM transition failed for sub=%s: %s", sub.id, exc
                )
        elif sub.status == Submission.Status.UNDER_AUDIT:
            log.info("ApproveReportView: sub=%s already under_audit", sub.id)
        else:
            log.warning(
                "ApproveReportView: sub=%s in unexpected status=%s for approval",
                sub.id,
                sub.status,
            )

        if not report.approved_at:
            report.approved_at = timezone.now()
            report.save(update_fields=["approved_at"])

        # Generate PDF. Delivery is initiated manually by the admin from the
        # AuditReport admin list (WhatsApp button).
        from apps.reports.tasks import generate_pdf

        generate_pdf.delay(str(report.id))

        log.info("ApproveReportView: queued PDF generation for report=%s", report.id)
        return Response({"status": "queued"}, status=200)
