from urllib.parse import quote_plus

from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from unfold.admin import ModelAdmin
from unfold.decorators import action

from apps.reports.models import AuditReport


@admin.register(AuditReport)
class AuditReportAdmin(ModelAdmin):
    list_display = (
        "submission",
        "client_name",
        "status",
        "pdf_link",
        "whatsapp_button",
        "approved_at",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("submission__client__name", "submission__client__company")
    readonly_fields = ("submission", "pdf_url", "status", "approved_at", "created_at", "updated_at")
    fields = ("submission", "admin_text", "status", "pdf_url", "approved_at", "created_at", "updated_at")
    actions_detail = ["approve_and_send"]

    @admin.display(description="Клиент")
    def client_name(self, obj):
        client = getattr(obj.submission, "client", None)
        if not client:
            return "—"
        return f"{client.name} ({client.company})"

    @admin.display(description="PDF")
    def pdf_link(self, obj):
        if not obj.pdf_url:
            return "—"
        return format_html(
            '<a href="{}" target="_blank" rel="noopener" '
            'style="color:#d97706;font-weight:600;">📄 Открыть</a>',
            obj.pdf_url,
        )

    @admin.display(description="WhatsApp")
    def whatsapp_button(self, obj):
        """Render a 'Send to client' button that pre-fills WhatsApp Web/desktop
        with the PDF link + a short message.

        Requires:
         - report.pdf_url populated (generated after status=approved)
         - client.phone_wa filled in
        """
        if not obj.pdf_url:
            return format_html('<span style="color:#94a3b8;">PDF ещё не готов</span>')

        client = getattr(obj.submission, "client", None)
        if not client or not client.phone_wa:
            return format_html('<span style="color:#94a3b8;">нет номера</span>')

        # Normalise phone to digits only — wa.me expects no + or spaces
        digits = "".join(ch for ch in client.phone_wa if ch.isdigit())
        if not digits:
            return format_html('<span style="color:#94a3b8;">нет номера</span>')

        message = (
            f"Здравствуйте, {client.name}! Ваш бизнес-аудит Baqsy готов.\n"
            f"Отчёт по компании «{client.company}» можно скачать по ссылке:\n"
            f"{obj.pdf_url}\n\n"
            f"Если возникнут вопросы — напишите в этот чат, мы ответим."
        )
        wa_url = f"https://wa.me/{digits}?text={quote_plus(message)}"
        return format_html(
            '<a href="{}" target="_blank" rel="noopener" '
            'style="display:inline-block;padding:4px 12px;border-radius:6px;'
            'background:#25D366;color:#fff;font-size:12px;font-weight:600;'
            'text-decoration:none;">💬 Отправить клиенту</a>',
            wa_url,
        )

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
