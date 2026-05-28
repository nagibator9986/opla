"""Админка AuditReport — переработана 2026-05-28 под удобный workflow.

Жалоба клиента: «в заявках "Анкета завершена", а в отчётах висит "Черновик /
PDF ещё не готов" — непонятно что делать дальше».

Решение:
  • В list_display — крупный прогресс-бейдж с явным следующим действием
    («Сгенерировать AI», «Утвердить + PDF», «Отправить клиенту»).
  • В list — bulk-actions: массово сгенерировать AI / утвердить / отметить.
  • В detail — большое поле admin_text сверху, workflow-карточка с кнопками,
    ссылка на Submission и прямой просмотр ответов клиента.
  • Заголовок страницы — «Отчёт для {имя} ({компания})», а не «AuditReport 1».

Все «магические» переходы по статусам — через те же FSM transitions и
ApproveReportView что и раньше, чтобы не дублировать бизнес-логику.
"""
from __future__ import annotations

from urllib.parse import quote_plus

from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from unfold.admin import ModelAdmin
from unfold.decorators import action

from apps.reports.models import AuditReport
from apps.submissions.models import Submission


@admin.register(AuditReport)
class AuditReportAdmin(ModelAdmin):
    """Workflow-friendly админка для отчётов."""

    list_display = (
        "report_title",
        "workflow_badge",
        "pdf_link",
        "whatsapp_button",
        "approved_at",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = (
        "submission__client__name",
        "submission__client__company",
        "submission__id",
    )
    readonly_fields = (
        "workflow_card",
        "submission_link",
        "client_info",
        "answers_link",
        "pdf_url",
        "status",
        "approved_at",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        ("Управление", {
            "fields": ("workflow_card",),
            "description": (
                "Workflow-шаги отчёта. Кнопки переключают шаги. "
                "Текст отчёта редактируется ниже в поле <b>«Содержимое»</b>."
            ),
        }),
        ("Содержимое отчёта", {
            "fields": ("admin_text",),
            "description": (
                "Это текст, который попадёт в PDF под заголовком «Анализ бизнеса». "
                "Можно отредактировать вручную или сгенерировать через AI-кнопку выше."
            ),
        }),
        ("Клиент и заявка", {
            "fields": ("submission_link", "client_info", "answers_link"),
        }),
        ("Системная информация", {
            "fields": ("status", "pdf_url", "approved_at", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
    actions_detail = ["generate_ai_draft", "approve_and_send", "mark_delivered"]
    actions = ["bulk_generate_ai_draft"]
    list_per_page = 30
    save_on_top = True

    # ── список ────────────────────────────────────────────────────────────

    @admin.display(description="Отчёт")
    def report_title(self, obj):
        client = getattr(obj.submission, "client", None)
        if client:
            primary = f"{client.name}"
            secondary = client.company or "—"
        else:
            primary = f"Заявка {str(obj.submission_id)[:8]}"
            secondary = ""
        sub_url = reverse(
            "admin:submissions_submission_change", args=[obj.submission_id]
        )
        return format_html(
            '<div style="line-height:1.3;">'
            '<div style="font-weight:600;color:#0f172a;">{}</div>'
            '<div style="font-size:11px;color:#64748b;">{}</div>'
            '<a href="{}" style="font-size:10px;color:#0ea5e9;text-decoration:none;">→ заявка</a>'
            '</div>',
            primary, secondary, sub_url,
        )

    @admin.display(description="Что делать сейчас")
    def workflow_badge(self, obj):
        """Цветной бейдж с подсказкой следующего шага."""
        sub_status = obj.submission.status
        has_text = bool((obj.admin_text or "").strip())
        is_approved = obj.status in (AuditReport.Status.APPROVED, AuditReport.Status.SENT)
        has_pdf = bool(obj.pdf_url)
        is_sent = obj.status == AuditReport.Status.SENT or sub_status == Submission.Status.DELIVERED

        if sub_status not in (
            Submission.Status.COMPLETED,
            Submission.Status.UNDER_AUDIT,
            Submission.Status.DELIVERED,
        ):
            label, bg, fg = "⏳ Ждём анкету", "#e2e8f0", "#475569"
        elif is_sent:
            label, bg, fg = "✓ Доставлено", "#d1fae5", "#065f46"
        elif has_pdf and is_approved:
            label, bg, fg = "💬 Отправить клиенту", "#fef3c7", "#92400e"
        elif has_text:
            label, bg, fg = "✓ Утвердить + создать PDF", "#dbeafe", "#1e40af"
        else:
            label, bg, fg = "🤖 Сгенерировать AI-черновик", "#fef3c7", "#92400e"

        return format_html(
            '<span style="display:inline-block;padding:4px 12px;border-radius:999px;'
            'background:{};color:{};font-size:12px;font-weight:600;'
            'white-space:nowrap;">{}</span>',
            bg, fg, label,
        )

    @admin.display(description="PDF")
    def pdf_link(self, obj):
        if not obj.pdf_url:
            return format_html('<span style="color:#94a3b8;font-size:11px;">не готов</span>')
        return format_html(
            '<a href="{}" target="_blank" rel="noopener" '
            'style="color:#d97706;font-weight:600;font-size:12px;">📄 Открыть</a>',
            obj.pdf_url,
        )

    @admin.display(description="WhatsApp")
    def whatsapp_button(self, obj):
        if not obj.pdf_url:
            return format_html('<span style="color:#94a3b8;font-size:11px;">—</span>')

        client = getattr(obj.submission, "client", None)
        if not client or not client.phone_wa:
            return format_html('<span style="color:#94a3b8;font-size:11px;">нет номера</span>')

        digits = "".join(ch for ch in client.phone_wa if ch.isdigit())
        if not digits:
            return format_html('<span style="color:#94a3b8;font-size:11px;">нет номера</span>')

        message = (
            f"Здравствуйте, {client.name}! Ваш бизнес-аудит Baqsy готов.\n"
            f"Отчёт по компании «{client.company}» можно скачать по ссылке:\n"
            f"{obj.pdf_url}\n\n"
            f"Если возникнут вопросы — напишите в этот чат, мы ответим."
        )
        wa_url = f"https://wa.me/{digits}?text={quote_plus(message)}"
        return format_html(
            '<a href="{}" target="_blank" rel="noopener" '
            'style="display:inline-block;padding:3px 10px;border-radius:6px;'
            'background:#25D366;color:#fff;font-size:11px;font-weight:600;'
            'text-decoration:none;white-space:nowrap;">💬 Отправить</a>',
            wa_url,
        )

    # ── detail page ───────────────────────────────────────────────────────

    @admin.display(description="Заявка клиента")
    def submission_link(self, obj):
        sub_url = reverse(
            "admin:submissions_submission_change", args=[obj.submission_id]
        )
        return format_html(
            '<a href="{}" style="color:#0ea5e9;font-weight:600;">'
            '→ открыть карточку заявки</a> &nbsp;<span style="color:#64748b;font-size:11px;">'
            'status: {}</span>',
            sub_url, escape(obj.submission.get_status_display()),
        )

    @admin.display(description="Клиент")
    def client_info(self, obj):
        client = getattr(obj.submission, "client", None)
        if not client:
            return "—"
        rows = [
            ("Имя", escape(client.name or "—")),
            ("Компания", escape(client.company or "—")),
            ("WhatsApp", escape(client.phone_wa or "не указан")),
        ]
        email = getattr(client, "email", None)
        if email:
            rows.append(("Email", escape(email)))
        body = "".join(
            f'<div style="display:flex;gap:14px;padding:4px 0;font-size:13px;">'
            f'<span style="color:#64748b;min-width:90px;">{k}:</span>'
            f'<span style="color:#0f172a;font-weight:500;">{v}</span></div>'
            for k, v in rows
        )
        return mark_safe(f'<div>{body}</div>')

    @admin.display(description="Ответы клиента")
    def answers_link(self, obj):
        sub_url = reverse(
            "admin:submissions_submission_change", args=[obj.submission_id]
        )
        answers_count = obj.submission.answers.count()
        return format_html(
            '<a href="{}#client-answers" style="color:#0ea5e9;font-weight:600;">'
            '→ читать все ответы ({})</a> &nbsp;'
            '<span style="color:#64748b;font-size:11px;">'
            'для контекста при редактировании отчёта</span>',
            sub_url, answers_count,
        )

    @admin.display(description="Workflow")
    def workflow_card(self, obj):
        """Большая визуальная карточка с прогрессом + основными кнопками."""
        if not obj or not obj.pk:
            return "—"

        sub = obj.submission
        sub_status = sub.status
        has_text = bool((obj.admin_text or "").strip())
        is_approved = obj.status in (AuditReport.Status.APPROVED, AuditReport.Status.SENT)
        has_pdf = bool(obj.pdf_url)
        is_sent = obj.status == AuditReport.Status.SENT or sub_status == Submission.Status.DELIVERED

        # Active step
        if sub_status not in (
            Submission.Status.COMPLETED,
            Submission.Status.UNDER_AUDIT,
            Submission.Status.DELIVERED,
        ):
            active = 1
        elif not has_text:
            active = 2
        elif not (is_approved and has_pdf):
            active = 3
        elif not is_sent:
            active = 4
        else:
            active = 5

        STEPS = [
            ("Анкета", "Клиент заполняет"),
            ("AI-черновик", "12 ассистентов"),
            ("Утверждение", "Проверка + PDF"),
            ("Отправка", "WhatsApp клиенту"),
        ]

        parts: list[str] = []
        parts.append(
            '<div style="font-family:system-ui,-apple-system,sans-serif;'
            'border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;background:#fff;">'
        )

        # progress strip
        parts.append(
            '<div style="display:flex;background:linear-gradient'
            '(135deg,#fef3c7 0%,#fffbeb 100%);border-bottom:1px solid #fde68a;">'
        )
        for idx, (name, hint) in enumerate(STEPS, 1):
            if idx < active or active == 5:
                bg, fg, icon = "#10b981", "#fff", "✓"
            elif idx == active:
                bg, fg, icon = "#f59e0b", "#fff", str(idx)
            else:
                bg, fg, icon = "#e2e8f0", "#94a3b8", str(idx)
            parts.append(
                f'<div style="flex:1;padding:14px 12px;text-align:center;'
                f'border-right:1px solid #fde68a;">'
                f'<div style="display:inline-flex;align-items:center;justify-content:center;'
                f'width:28px;height:28px;border-radius:50%;background:{bg};color:{fg};'
                f'font-weight:700;font-size:13px;margin-bottom:6px;">{icon}</div>'
                f'<div style="font-size:12px;font-weight:600;color:#0f172a;">{escape(name)}</div>'
                f'<div style="font-size:10px;color:#64748b;margin-top:2px;">{escape(hint)}</div>'
                f'</div>'
            )
        parts.append('</div>')

        # buttons
        parts.append('<div style="padding:16px;">')

        if active == 1:
            parts.append(
                '<div style="padding:12px;background:#fef3c7;border-radius:8px;color:#78350f;'
                'font-size:13px;">Клиент пока не завершил анкету.</div>'
            )

        elif active == 2:
            ai_url = reverse(
                "admin:reports_auditreport_generate_ai_draft", args=[obj.pk]
            )
            parts.append(
                f'<a href="{escape(ai_url)}" '
                f'style="display:inline-flex;align-items:center;gap:8px;'
                f'background:#0ea5e9;color:#fff;padding:10px 18px;border-radius:8px;'
                f'text-decoration:none;font-weight:600;font-size:14px;">'
                f'🤖 Сгенерировать AI-черновик (12 ассистентов)</a>'
                f'<div style="margin-top:8px;font-size:12px;color:#64748b;">'
                f'Запустит 12 параллельных вызовов OpenAI, соберёт черновик в поле '
                f'<b>«Содержимое отчёта»</b> ниже. Длительность: ~30 секунд.</div>'
            )

        elif active == 3:
            approve_url = reverse(
                "admin:reports_auditreport_approve_and_send", args=[obj.pk]
            )
            ai_url = reverse(
                "admin:reports_auditreport_generate_ai_draft", args=[obj.pk]
            )
            parts.append(
                f'<div style="display:flex;gap:10px;flex-wrap:wrap;">'
                f'<a href="{escape(approve_url)}" '
                f'style="display:inline-flex;align-items:center;gap:8px;'
                f'background:#10b981;color:#fff;padding:10px 18px;border-radius:8px;'
                f'text-decoration:none;font-weight:600;font-size:14px;">'
                f'✓ Утвердить и создать PDF</a>'
                f'<a href="{escape(ai_url)}" '
                f'style="display:inline-flex;align-items:center;gap:6px;'
                f'background:#fff;color:#0ea5e9;border:1px solid #0ea5e9;'
                f'padding:9px 14px;border-radius:8px;text-decoration:none;'
                f'font-weight:600;font-size:13px;">🤖 Догенерировать AI</a>'
                f'</div>'
                f'<div style="margin-top:8px;font-size:12px;color:#64748b;">'
                f'Текст уже есть. Сначала проверьте/отредактируйте поле '
                f'<b>«Содержимое отчёта»</b>, потом нажмите «Утвердить».</div>'
            )

        elif active == 4:
            client = getattr(sub, "client", None)
            wa_html = ""
            if obj.pdf_url and client and client.phone_wa:
                digits = "".join(ch for ch in client.phone_wa if ch.isdigit())
                if digits:
                    message = (
                        f"Здравствуйте, {client.name}! Ваш бизнес-аудит Baqsy готов.\n"
                        f"Отчёт по компании «{client.company}» можно скачать по ссылке:\n"
                        f"{obj.pdf_url}\n\nЕсли возникнут вопросы — напишите."
                    )
                    wa_url = f"https://wa.me/{digits}?text={quote_plus(message)}"
                    wa_html = (
                        f'<a href="{escape(wa_url)}" target="_blank" rel="noopener" '
                        f'style="display:inline-flex;align-items:center;gap:8px;'
                        f'background:#25D366;color:#fff;padding:10px 18px;border-radius:8px;'
                        f'text-decoration:none;font-weight:600;font-size:14px;">'
                        f'💬 Отправить клиенту в WhatsApp</a>'
                    )
                else:
                    wa_html = '<span style="color:#94a3b8;font-size:13px;">Нет валидного номера.</span>'
            else:
                wa_html = '<span style="color:#f59e0b;font-size:13px;">PDF ещё генерируется — обновите страницу.</span>'

            delivered_url = reverse(
                "admin:reports_auditreport_mark_delivered", args=[obj.pk]
            )
            pdf_link = ""
            if obj.pdf_url:
                pdf_link = (
                    f'<a href="{escape(obj.pdf_url)}" target="_blank" rel="noopener" '
                    f'style="display:inline-flex;align-items:center;gap:6px;'
                    f'background:#fff;color:#d97706;border:1px solid #d97706;'
                    f'padding:9px 14px;border-radius:8px;text-decoration:none;'
                    f'font-weight:600;font-size:13px;">📄 Скачать PDF</a>'
                )

            parts.append(
                f'<div style="display:flex;gap:10px;flex-wrap:wrap;">'
                f'{wa_html}{pdf_link}'
                f'<a href="{escape(delivered_url)}" '
                f'style="display:inline-flex;align-items:center;gap:6px;'
                f'background:#fff;color:#10b981;border:1px solid #10b981;'
                f'padding:9px 14px;border-radius:8px;text-decoration:none;'
                f'font-weight:600;font-size:13px;">📦 Отметить доставленным</a>'
                f'</div>'
                f'<div style="margin-top:8px;font-size:12px;color:#64748b;">'
                f'<b>1.</b> Нажмите «Отправить клиенту» — откроется WhatsApp Web. '
                f'<b>2.</b> Проверьте текст и пошлите. '
                f'<b>3.</b> Вернитесь и нажмите «Отметить доставленным».</div>'
            )

        else:  # active == 5
            parts.append(
                '<div style="padding:14px;background:#d1fae5;border-radius:8px;'
                'color:#065f46;font-size:14px;font-weight:600;">'
                '✓ Отчёт сформирован, PDF создан, отправлен клиенту и помечен доставленным.'
                '</div>'
            )

        # footer meta
        meta_parts = []
        if obj.approved_at:
            meta_parts.append(f"утверждено: {obj.approved_at.strftime('%Y-%m-%d %H:%M')}")
        if obj.pdf_url:
            meta_parts.append("PDF: готов")
        if meta_parts:
            parts.append(
                f'<div style="margin-top:14px;padding-top:12px;border-top:1px solid #e2e8f0;'
                f'font-size:11px;color:#64748b;">{" · ".join(meta_parts)}</div>'
            )

        parts.append('</div></div>')
        return mark_safe("".join(parts))

    # ── detail actions ────────────────────────────────────────────────────

    @action(
        description=_("🤖 Сгенерировать AI-черновик (12 ассистентов)"),
        url_path="generate-ai-draft",
    )
    def generate_ai_draft(self, request, object_id):
        from apps.ai.parameter_analyzer import assemble_full_report

        report = AuditReport.objects.select_related(
            "submission", "submission__client"
        ).get(pk=object_id)
        try:
            text = assemble_full_report(report.submission)
        except Exception as exc:
            messages.error(request, f"Ошибка генерации: {exc}")
            return HttpResponseRedirect(
                reverse("admin:reports_auditreport_change", args=(object_id,))
            )

        existing = (report.admin_text or "").strip()
        report.admin_text = f"{existing}\n\n---\n\n{text}" if existing else text
        report.save(update_fields=["admin_text", "updated_at"])
        messages.success(
            request,
            _("Черновик сгенерирован — проверьте и отредактируйте ниже."),
        )
        return HttpResponseRedirect(
            reverse("admin:reports_auditreport_change", args=(object_id,))
        )

    @action(
        description=_("✓ Утвердить и создать PDF"),
        url_path="approve-send",
    )
    def approve_and_send(self, request, object_id):
        report = AuditReport.objects.get(pk=object_id)
        admin_text = request.POST.get("admin_text")
        if admin_text is not None:
            report.admin_text = admin_text
            report.save(update_fields=["admin_text"])

        if not (report.admin_text or "").strip():
            messages.error(
                request,
                _("Заполните содержимое отчёта перед утверждением."),
            )
            return HttpResponseRedirect(
                reverse("admin:reports_auditreport_change", args=(object_id,))
            )

        from apps.reports.views import ApproveReportView
        approve_view = ApproveReportView.as_view()
        response = approve_view(request, report_id=str(object_id))
        if hasattr(response, "status_code") and response.status_code == 200:
            messages.success(
                request,
                _("Отчёт утверждён. PDF готовится — обновите страницу через 5–10 секунд."),
            )
        else:
            data = getattr(response, "data", {})
            err = data.get("error", data.get("detail", "неизвестная ошибка"))
            messages.error(request, f"Ошибка: {err}")
        return HttpResponseRedirect(
            reverse("admin:reports_auditreport_change", args=(object_id,))
        )

    @action(
        description=_("📦 Отметить доставленным"),
        url_path="mark-delivered",
    )
    def mark_delivered(self, request, object_id):
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
        elif sub.status == Submission.Status.DELIVERED:
            messages.info(request, _("Уже доставлено."))
        else:
            messages.warning(
                request,
                f"Нельзя пометить доставленным из «{sub.get_status_display()}».",
            )
        return HttpResponseRedirect(
            reverse("admin:reports_auditreport_change", args=(object_id,))
        )

    # ── bulk action: запустить AI для группы отчётов ──────────────────────

    @admin.action(description="🤖 Сгенерировать AI-черновик для выбранных")
    def bulk_generate_ai_draft(self, request, queryset):
        from apps.ai.parameter_analyzer import assemble_full_report

        ok = 0
        failed = 0
        for report in queryset.select_related("submission"):
            if (report.admin_text or "").strip():
                continue  # пропускаем, у кого уже есть текст
            try:
                report.admin_text = assemble_full_report(report.submission)
                report.save(update_fields=["admin_text", "updated_at"])
                ok += 1
            except Exception as exc:
                failed += 1
                self.message_user(
                    request,
                    f"Заявка {report.submission_id}: ошибка — {exc}",
                    level=messages.WARNING,
                )

        self.message_user(
            request,
            f"AI-черновик сгенерирован для {ok} отчётов" + (f", ошибок: {failed}" if failed else ""),
            level=messages.SUCCESS if ok else messages.WARNING,
        )
