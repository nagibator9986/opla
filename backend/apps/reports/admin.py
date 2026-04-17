from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from unfold.admin import ModelAdmin
from unfold.decorators import action

from apps.reports.models import AuditReport


@admin.register(AuditReport)
class AuditReportAdmin(ModelAdmin):
    list_display = ("submission", "status", "approved_at", "created_at")
    list_filter = ("status",)
    search_fields = ("submission__client__name", "submission__client__company")
    readonly_fields = ("submission", "pdf_url", "status", "approved_at", "created_at", "updated_at")
    fields = ("submission", "admin_text", "status", "pdf_url", "approved_at", "created_at", "updated_at")
    actions_detail = ["approve_and_send"]

    @action(
        description=_("Подтвердить и отправить PDF"),
        url_path="approve-send",
    )
    def approve_and_send(self, request, object_id):
        report = AuditReport.objects.get(pk=object_id)
        # Save admin_text from POST data if present
        admin_text = request.POST.get("admin_text")
        if admin_text is not None:
            report.admin_text = admin_text
            report.save(update_fields=["admin_text"])

        from apps.reports.views import ApproveReportView
        # Use as_view() to properly wrap Django request into DRF Request.
        # This ensures DRF's initialize_request is called, which wraps the
        # raw Django HttpRequest into a DRF Request object. Without this,
        # IsAdminUser permission check would fail because it expects
        # request.user from DRF's Request, not raw Django request.
        approve_view = ApproveReportView.as_view()
        response = approve_view(request, report_id=str(object_id))
        if hasattr(response, "status_code") and response.status_code == 200:
            messages.success(request, _("Отчёт поставлен в очередь на генерацию и доставку."))
        else:
            data = getattr(response, "data", {})
            err = data.get("error", data.get("detail", "неизвестная ошибка"))
            messages.error(request, f"Ошибка: {err}")
        return HttpResponseRedirect(
            reverse("admin:reports_auditreport_change", args=(object_id,))
        )
