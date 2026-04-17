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
    """POST /api/v1/reports/{report_id}/approve/ — staff approves and queues delivery.

    Requires:
    - Staff user (IsAdminUser permission)
    - report.admin_text must be non-empty

    On success:
    - Transitions submission completed → under_audit (idempotent if already under_audit)
    - Sets report.approved_at if not already set
    - Enqueues Celery chain: generate_pdf | group(deliver_telegram, deliver_whatsapp)
    - Returns 200 {"status": "queued"}
    """

    permission_classes = [IsAdminUser]

    def post(self, request, report_id):
        try:
            report = AuditReport.objects.select_related("submission").get(id=report_id)
        except AuditReport.DoesNotExist:
            return Response({"detail": "Report not found."}, status=404)

        # Validate admin_text is present
        if not report.admin_text or not report.admin_text.strip():
            return Response(
                {"error": "admin_text is required before approval"},
                status=400,
            )

        sub = report.submission

        # FSM transition: completed → under_audit (idempotent for under_audit)
        if sub.status == Submission.Status.COMPLETED:
            try:
                sub.start_audit()
                sub.save(update_fields=["status"])
                log.info("ApproveReportView: sub=%s transitioned to under_audit", sub.id)
            except Exception as exc:
                log.warning(
                    "ApproveReportView: FSM transition failed for sub=%s: %s", sub.id, exc
                )
        elif sub.status == Submission.Status.UNDER_AUDIT:
            log.info(
                "ApproveReportView: sub=%s already under_audit, skipping FSM", sub.id
            )
        else:
            log.warning(
                "ApproveReportView: sub=%s in unexpected status=%s for approval",
                sub.id,
                sub.status,
            )

        # Set approved_at if not already set
        if not report.approved_at:
            report.approved_at = timezone.now()
            report.save(update_fields=["approved_at"])

        # Enqueue Celery chain: generate_pdf → group(deliver_telegram, deliver_whatsapp)
        from celery import chain, group

        from apps.delivery.tasks import deliver_telegram, deliver_whatsapp
        from apps.reports.tasks import generate_pdf

        workflow = chain(
            generate_pdf.s(str(report.id)),
            group(
                deliver_telegram.si(str(report.id)),
                deliver_whatsapp.si(str(report.id)),
            ),
        )
        workflow.delay()

        log.info("ApproveReportView: queued pipeline for report=%s", report.id)
        return Response({"status": "queued"}, status=200)
