import csv
import io
from collections import OrderedDict
from urllib.parse import quote

from django.contrib import admin, messages
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe
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


# ─── helpers ─────────────────────────────────────────────────────────────


def _format_answer_value(value: dict) -> str:
    """Преобразует JSON ответа в человекочитаемый текст."""
    if not isinstance(value, dict):
        return str(value or "—")
    if "text" in value:
        return value["text"] or "—"
    if "number" in value:
        v = value["number"]
        return str(v) if v is not None else "—"
    if "choice" in value:
        return value["choice"] or "—"
    if "choices" in value:
        return ", ".join(value["choices"]) if value["choices"] else "—"
    if "url" in value:
        return value["url"] or "—"
    return str(value)


def _grouped_answers(submission: Submission) -> "OrderedDict[str, list]":
    """Группирует ответы по этапам (stage) с сохранением исходного порядка."""
    grouped: "OrderedDict[str, list]" = OrderedDict()
    answers = (
        submission.answers.select_related("question")
        .order_by("question__order")
    )
    for answer in answers:
        stage = answer.question.stage or "Без раздела"
        grouped.setdefault(stage, []).append(answer)
    return grouped


def _answers_as_plain_text(submission: Submission) -> str:
    """Все ответы клиента как обычный текст — для копирования в буфер."""
    lines: list[str] = []
    client = submission.client
    if client:
        lines.append(f"Клиент: {client.name} · {client.company}")
        if client.phone_wa:
            lines.append(f"Телефон/WA: {client.phone_wa}")
        if getattr(client, "email", None):
            lines.append(f"Email: {client.email}")
    lines.append(f"Заявка: {submission.id}")
    lines.append(f"Шаблон: {submission.template.name} v{submission.template.version}")
    if submission.tariff_id:
        lines.append(f"Тариф: {submission.tariff.title}")
    lines.append("")

    for stage, items in _grouped_answers(submission).items():
        lines.append(f"━━ {stage} ━━")
        for a in items:
            lines.append(f"\nВ: {a.question.text}")
            lines.append(f"О: {_format_answer_value(a.value)}")
        lines.append("")
    return "\n".join(lines)


# ─── inlines ─────────────────────────────────────────────────────────────


class AnswerInline(TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ("question_order", "question_text", "answer_pretty", "answered_at")
    fields = ("question_order", "question_text", "answer_pretty", "answered_at")
    can_delete = False
    classes = ("collapse",)
    verbose_name = "Ответ (таблица)"
    verbose_name_plural = "Ответы клиента (таблица — свернуть/развернуть)"

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description="№")
    def question_order(self, obj):
        return obj.question.order

    @admin.display(description="Вопрос")
    def question_text(self, obj):
        return obj.question.text

    @admin.display(description="Ответ")
    def answer_pretty(self, obj):
        return _format_answer_value(obj.value)


class AuditReportInline(StackedInline):
    model = AuditReport
    extra = 0
    fields = ("admin_text", "status", "pdf_url", "approved_at")
    readonly_fields = ("status", "pdf_url", "approved_at")
    can_delete = False


# ─── main admin ──────────────────────────────────────────────────────────


@admin.register(Submission)
class SubmissionAdmin(ModelAdmin):
    list_display = ("id_short", "client_label", "template", "tariff", "status_badge", "answered_progress", "created_at")
    list_filter = ("status", "tariff", "template__industry")
    search_fields = ("client__name", "client__company", "id")
    readonly_fields = (
        "id", "client", "template", "tariff",
        "created_at", "completed_at", "status",
        "client_answers_card",
    )
    fieldsets = (
        (None, {
            "fields": ("id", "client", "template", "tariff", "status",
                       "created_at", "completed_at"),
        }),
        ("Ответы клиента", {
            "fields": ("client_answers_card",),
            "description": (
                "Все ответы клиента сгруппированы по этапам. "
                "Используйте кнопки выше — «Копировать в буфер», «Скачать CSV» — "
                "для удобной обработки."
            ),
        }),
    )
    inlines = [AnswerInline, AuditReportInline]
    list_per_page = 25
    actions_detail = ["approve_and_send"]

    # ── list_display helpers ──────────────────────────────────────────────

    @admin.display(description="ID", ordering="id")
    def id_short(self, obj):
        return str(obj.id)[:8]

    @admin.display(description="Клиент", ordering="client__name")
    def client_label(self, obj):
        c = obj.client
        if not c:
            return "—"
        return f"{c.name} · {c.company}"

    @admin.display(description="Статус")
    def status_badge(self, obj):
        colors = {
            "created": ("#e2e8f0", "#0f172a"),
            "in_progress_basic": ("#fef3c7", "#78350f"),
            "paid": ("#dbeafe", "#1e40af"),
            "in_progress_full": ("#fef3c7", "#78350f"),
            "completed": ("#d1fae5", "#065f46"),
            "under_audit": ("#fde68a", "#92400e"),
            "delivered": ("#bbf7d0", "#065f46"),
        }
        bg, fg = colors.get(obj.status, ("#e2e8f0", "#0f172a"))
        return format_html(
            '<span style="background:{};color:{};padding:3px 10px;border-radius:999px;'
            'font-size:11px;font-weight:600;">{}</span>',
            bg, fg, obj.get_status_display(),
        )

    @admin.display(description="Ответы")
    def answered_progress(self, obj):
        answered = obj.answers.count()
        total = obj.template.questions.filter(required=True).count() if obj.template_id else 0
        return f"{answered}/{total}"

    # ── главный read-only блок с ответами + кнопками ──────────────────────

    @admin.display(description="Ответы клиента (по этапам)")
    def client_answers_card(self, obj):
        """Карточка со всеми ответами клиента: группировка по этапам +
        кнопки «Копировать в буфер», «Скачать CSV», «Распечатать»."""
        if not obj or not obj.pk:
            return "—"

        grouped = _grouped_answers(obj)
        total = sum(len(v) for v in grouped.values())
        if total == 0:
            return mark_safe(
                '<div style="padding:24px;background:#fef3c7;border-radius:8px;color:#78350f;">'
                'Клиент ещё не дал ни одного ответа.</div>'
            )

        csv_url = reverse("admin:submissions_submission_answers_csv", args=[obj.pk])
        plain_text = _answers_as_plain_text(obj)

        # Сборка HTML
        parts: list[str] = []
        parts.append('<div style="font-family:system-ui,-apple-system,sans-serif;">')

        # Кнопки действий
        parts.append('<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px;">')
        parts.append(
            '<button type="button" id="copy-answers-btn" '
            'style="background:#0ea5e9;color:#fff;border:none;padding:8px 14px;'
            'border-radius:6px;cursor:pointer;font-weight:600;font-size:13px;">'
            '📋 Скопировать все ответы</button>'
        )
        parts.append(
            f'<a href="{escape(csv_url)}" '
            'style="background:#10b981;color:#fff;text-decoration:none;padding:8px 14px;'
            'border-radius:6px;font-weight:600;font-size:13px;">📊 Скачать CSV</a>'
        )
        parts.append(
            '<button type="button" onclick="window.print()" '
            'style="background:#6366f1;color:#fff;border:none;padding:8px 14px;'
            'border-radius:6px;cursor:pointer;font-weight:600;font-size:13px;">'
            '🖨️ Распечатать</button>'
        )
        parts.append(
            f'<span style="margin-left:auto;color:#475569;font-size:12px;align-self:center;">'
            f'Ответов: <b>{total}</b></span>'
        )
        parts.append('</div>')

        # Скрытый текст для копирования
        parts.append(
            f'<textarea id="answers-plain-text" '
            f'style="position:absolute;left:-9999px;top:-9999px;" '
            f'readonly>{escape(plain_text)}</textarea>'
        )

        # Группы ответов
        for stage, items in grouped.items():
            parts.append(
                '<div style="margin-bottom:18px;border:1px solid #e2e8f0;'
                'border-radius:10px;overflow:hidden;background:#fff;">'
            )
            parts.append(
                f'<div style="background:#0f172a;color:#fff;padding:10px 14px;'
                f'font-weight:600;font-size:13px;letter-spacing:0.02em;">'
                f'{escape(stage)} · {len(items)} ответ(а/ов)</div>'
            )
            parts.append('<div style="padding:6px 14px;">')
            for a in items:
                q_text = escape(a.question.text)
                a_text = escape(_format_answer_value(a.value))
                parts.append(
                    f'<div style="padding:10px 0;border-bottom:1px dashed #e2e8f0;">'
                    f'<div style="color:#64748b;font-size:11px;text-transform:uppercase;'
                    f'letter-spacing:0.05em;margin-bottom:4px;">Вопрос {a.question.order}</div>'
                    f'<div style="color:#0f172a;font-weight:500;margin-bottom:6px;">{q_text}</div>'
                    f'<div style="background:#f1f5f9;padding:8px 12px;border-radius:6px;'
                    f'color:#0f172a;font-size:14px;white-space:pre-wrap;line-height:1.5;">'
                    f'{a_text}</div>'
                    f'</div>'
                )
            parts.append('</div></div>')

        parts.append('</div>')

        # JS для копирования
        parts.append("""
        <script>
        (function() {
          var btn = document.getElementById('copy-answers-btn');
          var ta  = document.getElementById('answers-plain-text');
          if (!btn || !ta) return;
          btn.addEventListener('click', function() {
            ta.style.left = '0';
            ta.style.top = '0';
            ta.select();
            try {
              document.execCommand('copy');
              btn.innerText = '✓ Скопировано!';
              btn.style.background = '#10b981';
              setTimeout(function() {
                btn.innerText = '📋 Скопировать все ответы';
                btn.style.background = '#0ea5e9';
              }, 1800);
            } catch (e) {
              if (navigator.clipboard) {
                navigator.clipboard.writeText(ta.value).then(function() {
                  btn.innerText = '✓ Скопировано!';
                  setTimeout(function() {
                    btn.innerText = '📋 Скопировать все ответы';
                  }, 1800);
                });
              }
            }
            ta.style.left = '-9999px';
            ta.style.top = '-9999px';
          });
        })();
        </script>
        """)

        return mark_safe("".join(parts))

    # ── custom admin URLs ─────────────────────────────────────────────────

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<path:object_id>/answers.csv",
                self.admin_site.admin_view(self.answers_csv_view),
                name="submissions_submission_answers_csv",
            ),
        ]
        return custom + urls

    def answers_csv_view(self, request, object_id):
        """Экспорт всех ответов клиента в CSV (UTF-8 with BOM для Excel)."""
        submission = Submission.objects.select_related(
            "client", "template", "template__industry", "tariff"
        ).get(pk=object_id)

        buf = io.StringIO()
        buf.write("﻿")  # BOM — Excel поймёт UTF-8
        writer = csv.writer(buf, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["Этап", "№", "Вопрос", "Тип", "Ответ", "Дата ответа"])
        for stage, items in _grouped_answers(submission).items():
            for a in items:
                writer.writerow([
                    stage,
                    a.question.order,
                    a.question.text,
                    a.question.get_field_type_display(),
                    _format_answer_value(a.value),
                    a.answered_at.strftime("%Y-%m-%d %H:%M") if a.answered_at else "",
                ])

        client = submission.client
        client_slug = (
            f"{client.company}_{client.name}".replace(" ", "_")
            if client else f"submission_{submission.id}"
        )
        filename = f"baqsy_answers_{client_slug}.csv"

        response = HttpResponse(buf.getvalue(), content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = (
            f'attachment; filename*=UTF-8\'\'{quote(filename)}'
        )
        return response

    # ── existing approve_and_send action ──────────────────────────────────

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
        admin_text = request.POST.get("admin_text")
        if admin_text is not None:
            report.admin_text = admin_text
            report.save(update_fields=["admin_text"])

        from apps.reports.views import ApproveReportView
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


# ─── group/participant admins (без изменений) ───────────────────────────


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
