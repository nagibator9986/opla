from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from unfold.admin import ModelAdmin, StackedInline, TabularInline
from unfold.decorators import action

from apps.reports.models import AuditReport
from apps.submissions.models import Answer, Submission


class AnswerInline(TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ("question", "value", "answered_at")
    can_delete = False


class AuditReportInline(StackedInline):
    model = AuditReport
    extra = 0
    fields = ("admin_text", "status", "pdf_url", "approved_at")
    readonly_fields = ("status", "pdf_url", "approved_at")
    can_delete = False


@admin.register(Submission)
class SubmissionAdmin(ModelAdmin):
    list_display = ("id", "client", "template", "tariff", "status", "created_at")
    list_filter = ("status", "tariff", "template__industry")
    search_fields = ("client__name", "client__company", "id")
    readonly_fields = ("id", "client", "template", "tariff", "created_at", "completed_at", "status")
    inlines = [AnswerInline, AuditReportInline]
    list_per_page = 25
    actions_detail = ["approve_and_send"]

    @action(
        description=_("Подтвердить и отправить PDF"),
        url_path="approve-send",
    )
    def approve_and_send(self, request, object_id):
        """Approve report from Submission change page. Resolves submission.report and calls ApproveReportView."""
        submission = Submission.objects.select_related("report").get(pk=object_id)
        if not hasattr(submission, "report"):
            messages.error(request, _("У заявки нет отчёта. Сначала создайте AuditReport."))
            return HttpResponseRedirect(
                reverse("admin:submissions_submission_change", args=(object_id,))
            )

        report = submission.report
        # Save admin_text from POST data if present
        admin_text = request.POST.get("admin_text")
        if admin_text is not None:
            report.admin_text = admin_text
            report.save(update_fields=["admin_text"])

        from apps.reports.views import ApproveReportView
        # Use as_view() to properly wrap Django request into DRF Request
        # (fixes DRF permission check -- IsAdminUser needs DRF's initialize_request)
        approve_view = ApproveReportView.as_view()
        response = approve_view(request, report_id=str(report.pk))
        if hasattr(response, "status_code") and response.status_code == 200:
            messages.success(request, _("Отчёт поставлен в очередь на генерацию и доставку."))
        else:
            data = getattr(response, "data", {})
            err = data.get("error", data.get("detail", "неизвестная ошибка"))
            messages.error(request, f"Ошибка: {err}")
        return HttpResponseRedirect(
            reverse("admin:submissions_submission_change", args=(object_id,))
        )
