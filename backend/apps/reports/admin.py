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
    actions_detail = ["generate_ai_draft", "approve_and_send", "mark_delivered"]

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
        description=_("Сгенерировать черновик отчёта (12 ИИ-ассистентов)"),
        url_path="generate-ai-draft",
    )
    def generate_ai_draft(self, request, object_id):
        """Запустить 12 параметров через OpenAI и собрать markdown-черновик
        в поле admin_text. Оператор потом редактирует и отправляет PDF."""
        from apps.ai.parameter_analyzer import assemble_full_report

        report = AuditReport.objects.select_related("submission", "submission__client").get(pk=object_id)
        try:
            text = assemble_full_report(report.submission)
        except Exception as exc:
            messages.error(request, f"Ошибка генерации: {exc}")
            return HttpResponseRedirect(
                reverse("admin:reports_auditreport_change", args=(object_id,))
            )

        # Если в admin_text уже что-то есть — НЕ затираем, а добавляем вниз
        existing = (report.admin_text or "").strip()
        report.admin_text = (
            f"{existing}\n\n---\n\n{text}" if existing else text
        )
        report.save(update_fields=["admin_text", "updated_at"])
        messages.success(
            request,
            _("Черновик отчёта сгенерирован 12 ассистентами. Проверьте и отредактируйте текст ниже."),
        )
        return HttpResponseRedirect(
            reverse("admin:reports_auditreport_change", args=(object_id,))
        )

    @action(description=_("Отметить доставленным"), url_path="mark-delivered")
    def mark_delivered(self, request, object_id):
        """Admin confirmed they've sent the PDF via wa.me → move FSM to 'delivered'."""
        from apps.submissions.models import Submission

        report = AuditReport.objects.select_related("submission").get(pk=object_id)
        sub = report.submission
        if sub.status == Submission.Status.UNDER_AUDIT:
            try:
                sub.mark_delivered()
                sub.save(update_fields=["status"])
                report.status = AuditReport.Status.SENT
                report.save(update_fields=["status"])
                messages.success(request, _("Заявка помечена как доставленная."))
            except Exception as exc:
                messages.error(request, f"Ошибка FSM: {exc}")
        else:
            messages.warning(
                request,
                f"Нельзя перевести в 'delivered' из статуса '{sub.get_status_display()}'.",
            )
        return HttpResponseRedirect(
            reverse("admin:reports_auditreport_change", args=(object_id,))
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
