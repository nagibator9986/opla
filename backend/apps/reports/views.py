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
    """GET /api/v1/submissions/{submission_id}/pdf/ — публичная отдача отчёта.

    Источник файла (в порядке приоритета):
      1. ``report.uploaded_file`` — если админ загрузил готовый PDF/DOCX,
         он отдаётся как есть (с правильным content-type по расширению).
      2. ``report.pdf_url`` — иначе стримим из MinIO PDF, собранный
         WeasyPrint'ом из ``admin_text``.

    Почему через Django proxy (а не прямую ссылку на MinIO):
      • MinIO живёт во внутренней Docker-сети (``http://minio:9000``) и
        наружу через nginx не проксируется.
      • Логика permissions может быть расширена без нарушения публичных URL.

    Public URL = ``{SITE_URL}/api/v1/submissions/{submission_id}/pdf/``.
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
        if not report or not report.has_deliverable:
            raise Http404("Отчёт ещё не готов.")

        client = submission.client
        company_slug = "report"
        if client and client.company:
            company_slug = re.sub(r"[^\w\-]+", "_", client.company)[:40] or "report"

        # 1) Приоритет — загруженный админом файл.
        if report.uploaded_file:
            return self._serve_uploaded(report, company_slug)

        # 2) Fallback — PDF из MinIO.
        return self._serve_minio_pdf(report, company_slug)

    # ── helpers ───────────────────────────────────────────────────────────

    def _serve_uploaded(self, report, company_slug):
        """Стримит загруженный админом файл (PDF / DOCX / другое).

        django-FileField сам открывает поток из дефолтного storage
        (FileSystemStorage в текущей конфигурации). При смене на S3
        Django откроет stream из S3 прозрачно.
        """
        f = report.uploaded_file
        ext = (f.name.rsplit(".", 1)[-1] or "pdf").lower()
        content_type = {
            "pdf":  "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "doc":  "application/msword",
        }.get(ext, "application/octet-stream")
        return FileResponse(
            f.open("rb"),
            content_type=content_type,
            as_attachment=False,
            filename=f"baqsy_{company_slug}.{ext}",
        )

    def _serve_minio_pdf(self, report, company_slug):
        object_key = _extract_object_key(report.pdf_url)
        if not object_key:
            log.error(
                "DownloadReportPdfView: cannot extract S3 key from %s",
                report.pdf_url,
            )
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

        return FileResponse(
            obj["Body"],
            content_type="application/pdf",
            as_attachment=False,
            filename=f"baqsy_{company_slug}.pdf",
        )


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

        # Должно быть либо загруженный файл, либо текст для AI-генерации.
        has_text = bool((report.admin_text or "").strip())
        has_file = bool(report.uploaded_file)
        if not has_text and not has_file:
            return Response(
                {"error": "перед утверждением загрузите PDF/DOCX или заполните текст отчёта"},
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
