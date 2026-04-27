from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from unfold.admin import ModelAdmin, StackedInline, TabularInline
from unfold.decorators import action

from apps.reports.models import AuditReport
from apps.submissions.group_invites import (
    participant_summary,
    send_email_invitation,
)
from apps.submissions.models import (
    Answer,
    AuditGroup,
    AuditParticipant,
    Submission,
)


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


class AuditParticipantInline(TabularInline):
    model = AuditParticipant
    extra = 0
    readonly_fields = ("invite_token", "status", "invited_at", "completed_at", "invite_link")
    fields = ("name", "email", "phone_wa", "status", "invite_link", "invited_at", "completed_at")
    can_delete = False

    @admin.display(description="Ссылка")
    def invite_link(self, obj):
        if not obj.invite_token:
            return "—"
        from django.conf import settings
        base = getattr(settings, "SITE_URL", "https://baqsy.tnriazun.com").rstrip("/")
        url = f"{base}/invite/{obj.invite_token}"
        return format_html(
            '<a href="{}" target="_blank" rel="noopener" '
            'style="color:#d97706;font-weight:600;">📎 открыть</a>', url,
        )


@admin.register(AuditGroup)
class AuditGroupAdmin(ModelAdmin):
    list_display = (
        "id", "submission_link", "quorum_size",
        "completed_count_badge", "created_at",
    )
    list_filter = ("quorum_size",)
    search_fields = (
        "initiator_submission__client__name",
        "initiator_submission__client__company",
        "participants__email",
        "participants__name",
    )
    readonly_fields = ("initiator_submission", "created_at", "updated_at")
    inlines = [AuditParticipantInline]
    save_on_top = True

    @admin.display(description="Заявка инициатора")
    def submission_link(self, obj):
        url = reverse("admin:submissions_submission_change", args=[obj.initiator_submission_id])
        client = obj.initiator_submission.client
        label = f"{client.name} · {client.company}" if client else str(obj.initiator_submission_id)
        return format_html('<a href="{}">{}</a>', url, label)

    @admin.display(description="Кворум")
    def completed_count_badge(self, obj):
        done = obj.completed_count
        total = obj.quorum_size
        ok = done >= total
        bg, fg = ("#d1fae5", "#065f46") if ok else ("#fef3c7", "#78350f")
        return format_html(
            '<span style="display:inline-block;padding:2px 10px;border-radius:999px;'
            'background:{};color:{};font-size:12px;font-weight:600;">{}/{}{}</span>',
            bg, fg, done, total, " ✓" if ok else "",
        )


@admin.register(AuditParticipant)
class AuditParticipantAdmin(ModelAdmin):
    list_display = ("name", "email", "group", "status_badge", "invited_at", "completed_at", "resend_button")
    list_filter = ("status",)
    search_fields = ("name", "email", "phone_wa", "invite_token")
    readonly_fields = (
        "group", "invite_token", "invite_link",
        "status", "invited_at", "started_at", "completed_at",
        "last_email_sent_at",
    )
    actions_detail = ["resend_invitation"]

    @admin.display(description="Статус")
    def status_badge(self, obj):
        colors = {
            "invited": ("#dbeafe", "#1e40af"),
            "in_progress": ("#fef3c7", "#78350f"),
            "completed": ("#d1fae5", "#065f46"),
            "expired": ("#fee2e2", "#991b1b"),
        }
        bg, fg = colors.get(obj.status, ("#e2e8f0", "#0f172a"))
        return format_html(
            '<span style="background:{};color:{};padding:3px 10px;border-radius:999px;'
            'font-size:11px;font-weight:600;">{}</span>',
            bg, fg, obj.get_status_display(),
        )

    @admin.display(description="Ссылка")
    def invite_link(self, obj):
        s = participant_summary(obj)
        return format_html(
            '<a href="{}" target="_blank">📎 опросная ссылка</a><br>'
            '<a href="{}" target="_blank">💬 wa.me</a>' if s.get("wa_me_url") else
            '<a href="{}" target="_blank">📎 опросная ссылка</a>',
            s["invite_url"], s.get("wa_me_url") or "",
        )

    @admin.display(description="")
    def resend_button(self, obj):
        url = reverse("admin:submissions_auditparticipant_change", args=[obj.id])
        return format_html(
            '<a href="{}#resend" style="display:inline-block;padding:3px 8px;'
            'border-radius:6px;background:#f59e0b;color:#fff;font-size:11px;'
            'font-weight:600;text-decoration:none;">Открыть</a>', url,
        )

    @action(description=_("Перепослать приглашение по email"), url_path="resend-email")
    def resend_invitation(self, request, object_id):
        p = AuditParticipant.objects.get(pk=object_id)
        ok = send_email_invitation(p)
        if ok:
            messages.success(request, _("Приглашение отправлено на %(email)s.") % {"email": p.email})
        else:
            messages.error(
                request,
                _("Не удалось отправить email. Используйте wa.me-ссылку из карточки участника."),
            )
        return HttpResponseRedirect(
            reverse("admin:submissions_auditparticipant_change", args=(object_id,))
        )
