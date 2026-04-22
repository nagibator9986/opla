"""Views for the reports app."""
from __future__ import annotations

import logging

from django.utils import timezone
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reports.models import AuditReport
from apps.submissions.models import Submission

log = logging.getLogger(__name__)


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
