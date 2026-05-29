"""Админка заявок — единая страница с одной большой кнопкой действия.

После 2026-05-29 переработана под принцип «один экран — одно действие»
(см. CLAUDE.md §13.2). Старая логика с 4-шаговым прогрессом, 5 кнопками
и дублирующей админкой AuditReport показала себя как непонятная — теперь:

  • Только страница заявки (`/admin/submissions/submission/<id>/`) —
    AuditReport-админка скрыта из меню, но доступна по прямому URL.
  • Сверху: КЛИЕНТ, СТАТУС, ОДНА большая цветная кнопка с подсказкой
    что сейчас делать.
  • Ниже: одно поле для загрузки готового PDF/DOCX ИЛИ текст отчёта.
  • Ниже: свёрнутые ответы клиента (кнопки «Скопировать / CSV / Печать»).

Бизнес-логика workflow — в `apps.reports.services.approve_report()` и
`mark_report_delivered()`, чтобы не дублировать между DRF view и admin.
"""
from __future__ import annotations

import csv
import io
from collections import OrderedDict
from urllib.parse import quote, quote_plus

from django.conf import settings
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


def _public_pdf_url(submission) -> str:
    """Публичный URL отчёта (через Django proxy, MinIO внутри сети).

    См. CLAUDE.md §13.5 — MinIO не торчит наружу, поэтому используем proxy.
    """
    base = getattr(settings, "SITE_URL", "https://baqsy.tnriazun.com").rstrip("/")
    return f"{base}/api/v1/submissions/{submission.id}/pdf/"


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
    grouped: "OrderedDict[str, list]" = OrderedDict()
    for answer in submission.answers.select_related("question").order_by("question__order"):
        stage = answer.question.stage or "Без раздела"
        grouped.setdefault(stage, []).append(answer)
    return grouped


def _answers_as_plain_text(submission: Submission) -> str:
    lines: list[str] = []
    client = submission.client
    if client:
        lines.append(f"Клиент: {client.name} · {client.company}")
        if client.phone_wa:
            lines.append(f"Телефон/WA: {client.phone_wa}")
    lines.append(f"Заявка: {submission.id}")
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


# ─── inline для отчёта ───────────────────────────────────────────────────


class AuditReportInline(StackedInline):
    """Одна форма для контента отчёта: либо файл, либо текст."""

    model = AuditReport
    extra = 0
    max_num = 1
    fields = ("uploaded_file", "admin_text")
    can_delete = False
    verbose_name = "Контент отчёта"
    verbose_name_plural = "Контент отчёта"


# ─── main admin ──────────────────────────────────────────────────────────


@admin.register(Submission)
class SubmissionAdmin(ModelAdmin):
    """Единая страница заявки.

    Один путь обработки:
      1. Клиент сдаёт анкету → автоматически создаётся AuditReport draft.
      2. Админ загружает PDF/DOCX ИЛИ пишет текст в admin_text → нажимает «Сохранить».
      3. Подсказка «Готово — нажмите ОТПРАВИТЬ КЛИЕНТУ» → одна большая кнопка вверху.
      4. После клика: всё одной транзакцией — approve, generate PDF, открывается
         кабинет/WhatsApp.
      5. После отправки сообщения админом — кнопка «Отметить доставленным».
    """

    list_display = (
        "id_short", "client_label", "tariff",
        "status_badge", "answered_progress",
        "report_progress_badge", "created_at",
    )
    list_filter = ("status", "tariff", "template__industry")
    search_fields = ("client__name", "client__company", "id")
    readonly_fields = (
        "id", "client", "template", "tariff",
        "created_at", "completed_at", "status",
        "action_card", "client_answers_card",
    )
    fieldsets = (
        (None, {
            "fields": ("action_card",),
        }),
        ("Ответы клиента", {
            "fields": ("client_answers_card",),
            "classes": ("collapse",),
        }),
        ("Метаданные заявки", {
            "fields": ("id", "client", "template", "tariff", "status",
                       "created_at", "completed_at"),
            "classes": ("collapse",),
        }),
    )
    inlines = [AuditReportInline]
    list_per_page = 25
    actions_detail = ["send_to_client", "mark_delivered"]

    # ── list display ──────────────────────────────────────────────────────

    @admin.display(description="ID")
    def id_short(self, obj):
        return str(obj.id)[:8]

    @admin.display(description="Клиент")
    def client_label(self, obj):
        c = obj.client
        return f"{c.name} · {c.company}" if c else "—"

    @admin.display(description="Статус")
    def status_badge(self, obj):
        colors = {
            "created":           ("#e2e8f0", "#0f172a"),
            "in_progress_basic": ("#fef3c7", "#78350f"),
            "paid":              ("#dbeafe", "#1e40af"),
            "in_progress_full":  ("#fef3c7", "#78350f"),
            "completed":         ("#d1fae5", "#065f46"),
            "under_audit":       ("#fde68a", "#92400e"),
            "delivered":         ("#bbf7d0", "#065f46"),
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

    @admin.display(description="Отчёт")
    def report_progress_badge(self, obj):
        if obj.status in ("created", "in_progress_basic", "paid", "in_progress_full"):
            return format_html('<span style="color:#94a3b8;font-size:11px;">— анкета не сдана —</span>')
        report = getattr(obj, "report", None)
        has_content = bool(report and (report.uploaded_file or (report.admin_text or "").strip()))
        is_approved = report and report.status in ("approved", "sent")
        is_sent = obj.status == "delivered" or (report and report.status == "sent")
        if is_sent:
            return format_html(
                '<span style="background:#d1fae5;color:#065f46;padding:3px 10px;border-radius:999px;'
                'font-size:11px;font-weight:600;">✓ Доставлено</span>'
            )
        if is_approved:
            return format_html(
                '<span style="background:#fde68a;color:#92400e;padding:3px 10px;border-radius:999px;'
                'font-size:11px;font-weight:600;">Готов · Отправить</span>'
            )
        if has_content:
            return format_html(
                '<span style="background:#dbeafe;color:#1e40af;padding:3px 10px;border-radius:999px;'
                'font-size:11px;font-weight:600;">Готов · Утвердить</span>'
            )
        return format_html(
            '<span style="background:#fef3c7;color:#78350f;padding:3px 10px;border-radius:999px;'
            'font-size:11px;font-weight:600;">Загрузите файл или AI</span>'
        )

    # ── главный action-card ───────────────────────────────────────────────

    @admin.display(description="Что делать сейчас")
    def action_card(self, obj):
        """Большая карточка с одной кнопкой действия для текущего шага.

        Шаги:
          • анкета не сдана → сообщение «ждём клиента», без кнопок
          • анкета сдана, контента нет → нужно загрузить файл / написать текст / нажать AI
          • контент есть, не утверждено → одна кнопка «📨 Отправить клиенту»
          • утверждено, не доставлено → две кнопки: WhatsApp + «Отметить доставленным»
          • доставлено → ✓ Готово
        """
        if not obj or not obj.pk:
            return mark_safe(
                '<div style="padding:14px;background:#f1f5f9;border-radius:8px;color:#475569;">'
                'Сохраните заявку, чтобы увидеть действия.</div>'
            )

        client = obj.client
        client_line = f"{client.name} · {client.company}" if client else "Клиент не задан"
        status_text = obj.get_status_display()

        report = getattr(obj, "report", None)
        has_text = bool(report and (report.admin_text or "").strip())
        has_file = bool(report and report.uploaded_file)
        has_content = has_text or has_file
        is_approved = report and report.status in ("approved", "sent")
        deliverable_ready = report and (report.pdf_url or report.uploaded_file)
        is_sent = obj.status == "delivered" or (report and report.status == "sent")

        # Шапка карточки — всегда одинаковая
        parts: list[str] = []
        parts.append(
            '<div style="font-family:system-ui,-apple-system,sans-serif;'
            'border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;background:#fff;">'
        )
        parts.append(
            f'<div style="padding:16px 20px;background:linear-gradient'
            f'(135deg,#fef3c7 0%,#fffbeb 100%);border-bottom:1px solid #fde68a;">'
            f'<div style="font-size:11px;color:#92400e;text-transform:uppercase;'
            f'letter-spacing:0.05em;font-weight:700;margin-bottom:4px;">Заявка клиента</div>'
            f'<div style="font-size:18px;font-weight:700;color:#0f172a;">{escape(client_line)}</div>'
            f'<div style="font-size:12px;color:#78350f;margin-top:4px;">'
            f'Статус: <b>{escape(status_text)}</b></div>'
            f'</div>'
        )

        # Тело — действие зависит от шага
        parts.append('<div style="padding:20px;">')

        if obj.status in ("created", "in_progress_basic", "paid", "in_progress_full"):
            parts.append(
                '<div style="padding:16px;background:#fef3c7;border-radius:10px;'
                'color:#78350f;font-size:14px;text-align:center;">'
                '⏳ <b>Ждём, пока клиент закончит анкету.</b><br/>'
                '<span style="font-size:12px;">Действия станут доступны после завершения.</span>'
                '</div>'
            )

        elif is_sent:
            parts.append(
                '<div style="padding:16px;background:#d1fae5;border-radius:10px;'
                'color:#065f46;font-size:14px;text-align:center;font-weight:600;">'
                '✓ Отчёт отправлен клиенту и помечен доставленным.'
                '</div>'
            )

        elif not has_content:
            # Нужно выбрать: загрузить файл, написать текст или сгенерировать AI
            ai_url = reverse("admin:submissions_submission_generate_ai_draft", args=[obj.pk])
            parts.append(
                '<div style="font-size:14px;color:#0f172a;margin-bottom:12px;font-weight:600;">'
                'Выберите способ подготовки отчёта:</div>'
            )
            parts.append(
                f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px;">'
                # ── Вариант A: AI ──
                f'<div style="padding:14px;background:#f0f9ff;border:1px solid #bae6fd;border-radius:10px;">'
                f'<div style="font-weight:700;color:#0c4a6e;font-size:13px;margin-bottom:4px;">'
                f'A. Через AI</div>'
                f'<div style="font-size:11px;color:#475569;margin-bottom:10px;line-height:1.5;">'
                f'12 ассистентов соберут текст за ~30 сек. Потом можно отредактировать.</div>'
                f'<a href="{escape(ai_url)}" '
                f'style="display:inline-flex;align-items:center;gap:6px;background:#0ea5e9;'
                f'color:#fff;padding:8px 14px;border-radius:6px;text-decoration:none;'
                f'font-weight:600;font-size:13px;">🤖 Сгенерировать</a>'
                f'</div>'
                # ── Вариант B: Upload ──
                f'<div style="padding:14px;background:#fff7ed;border:1px solid #fed7aa;border-radius:10px;">'
                f'<div style="font-weight:700;color:#7c2d12;font-size:13px;margin-bottom:4px;">'
                f'B. Загрузить готовый</div>'
                f'<div style="font-size:11px;color:#475569;margin-bottom:10px;line-height:1.5;">'
                f'PDF или DOCX от эксперта. Отправится клиенту как есть.</div>'
                f'<a href="#contentotchta-group" '
                f'style="display:inline-flex;align-items:center;gap:6px;background:#f97316;'
                f'color:#fff;padding:8px 14px;border-radius:6px;text-decoration:none;'
                f'font-weight:600;font-size:13px;">📎 К полю загрузки</a>'
                f'</div>'
                f'</div>'
                '<div style="padding:10px;background:#f1f5f9;border-radius:8px;font-size:11px;'
                'color:#475569;line-height:1.5;">'
                '💡 Найдите ниже секцию <b>«Контент отчёта»</b>, загрузите файл '
                'или впишите текст — потом нажмите <b>«Сохранить и продолжить редактирование»</b> '
                'внизу страницы. После сохранения здесь появится кнопка отправки.'
                '</div>'
            )

        elif not is_approved:
            # Контент есть → большая кнопка «Отправить клиенту»
            send_url = reverse("admin:submissions_submission_send_to_client", args=[obj.pk])
            content_label = "файл загружен" if has_file else f"текст ({len(report.admin_text)} символов)"
            parts.append(
                f'<div style="margin-bottom:12px;padding:10px 14px;background:#dbeafe;'
                f'border-radius:8px;color:#1e40af;font-size:13px;">'
                f'✓ Контент готов ({content_label}).'
                f'</div>'
                f'<a href="{escape(send_url)}" '
                f'style="display:block;width:100%;box-sizing:border-box;text-align:center;'
                f'background:#10b981;color:#fff;padding:16px 24px;border-radius:10px;'
                f'text-decoration:none;font-weight:700;font-size:16px;'
                f'box-shadow:0 4px 12px rgba(16,185,129,0.3);">'
                f'📨 Отправить клиенту</a>'
                f'<div style="margin-top:10px;font-size:11px;color:#64748b;text-align:center;">'
                f'Утвердит отчёт, соберёт PDF, активирует отправку через WhatsApp.</div>'
            )

        else:
            # Утверждён, не доставлен → WhatsApp + отметить доставленным
            wa_html = ""
            if deliverable_ready and client and client.phone_wa:
                digits = "".join(ch for ch in client.phone_wa if ch.isdigit())
                if digits:
                    pdf_url = _public_pdf_url(obj)
                    message = (
                        f"Здравствуйте, {client.name}! Ваш бизнес-аудит Baqsy готов.\n"
                        f"Отчёт по компании «{client.company}» можно скачать по ссылке:\n"
                        f"{pdf_url}\n\nЕсли возникнут вопросы — напишите."
                    )
                    wa_url = f"https://wa.me/{digits}?text={quote_plus(message)}"
                    wa_html = (
                        f'<a href="{escape(wa_url)}" target="_blank" rel="noopener" '
                        f'style="display:block;width:100%;box-sizing:border-box;text-align:center;'
                        f'background:#25D366;color:#fff;padding:16px 24px;border-radius:10px;'
                        f'text-decoration:none;font-weight:700;font-size:16px;margin-bottom:10px;'
                        f'box-shadow:0 4px 12px rgba(37,211,102,0.3);">'
                        f'💬 Открыть WhatsApp с сообщением</a>'
                    )

            deliver_url = reverse("admin:submissions_submission_mark_delivered", args=[obj.pk])
            pdf_url = _public_pdf_url(obj)
            parts.append(
                '<div style="margin-bottom:12px;padding:10px 14px;background:#fde68a;'
                'border-radius:8px;color:#92400e;font-size:13px;">'
                '✓ Отчёт утверждён. PDF готов к отправке.'
                '</div>'
            )
            parts.append(wa_html)
            parts.append(
                f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px;">'
                f'<a href="{escape(pdf_url)}" target="_blank" '
                f'style="display:block;text-align:center;background:#fff;color:#d97706;'
                f'border:1.5px solid #d97706;padding:10px;border-radius:8px;text-decoration:none;'
                f'font-weight:600;font-size:13px;">📄 Открыть PDF</a>'
                f'<a href="{escape(deliver_url)}" '
                f'style="display:block;text-align:center;background:#fff;color:#10b981;'
                f'border:1.5px solid #10b981;padding:10px;border-radius:8px;text-decoration:none;'
                f'font-weight:600;font-size:13px;">📦 Отметить доставленным</a>'
                f'</div>'
                f'<div style="margin-top:10px;font-size:11px;color:#64748b;text-align:center;">'
                f'1) Открыть WhatsApp · 2) Отправить сообщение · 3) Нажать «Отметить доставленным».'
                f'</div>'
            )

        parts.append('</div></div>')
        return mark_safe("".join(parts))

    # ── ответы клиента ────────────────────────────────────────────────────

    @admin.display(description="Ответы (по этапам)")
    def client_answers_card(self, obj):
        if not obj or not obj.pk:
            return "—"
        grouped = _grouped_answers(obj)
        total = sum(len(v) for v in grouped.values())
        if total == 0:
            return mark_safe(
                '<div style="padding:14px;background:#fef3c7;border-radius:8px;color:#78350f;">'
                'Клиент ещё не дал ни одного ответа.</div>'
            )

        csv_url = reverse("admin:submissions_submission_answers_csv", args=[obj.pk])
        plain_text = _answers_as_plain_text(obj)
        parts: list[str] = []
        parts.append('<div style="font-family:system-ui,-apple-system,sans-serif;">')
        parts.append(
            f'<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px;">'
            f'<button type="button" id="copy-answers-btn" '
            f'style="background:#0ea5e9;color:#fff;border:none;padding:8px 14px;'
            f'border-radius:6px;cursor:pointer;font-weight:600;font-size:12px;">'
            f'📋 Скопировать</button>'
            f'<a href="{escape(csv_url)}" '
            f'style="background:#10b981;color:#fff;text-decoration:none;padding:8px 14px;'
            f'border-radius:6px;font-weight:600;font-size:12px;">📊 CSV</a>'
            f'<button type="button" onclick="window.print()" '
            f'style="background:#6366f1;color:#fff;border:none;padding:8px 14px;'
            f'border-radius:6px;cursor:pointer;font-weight:600;font-size:12px;">🖨️ Печать</button>'
            f'<span style="margin-left:auto;align-self:center;color:#475569;font-size:12px;">'
            f'Ответов: <b>{total}</b></span>'
            f'</div>'
            f'<textarea id="answers-plain-text" readonly '
            f'style="position:absolute;left:-9999px;">{escape(plain_text)}</textarea>'
        )
        for stage, items in grouped.items():
            parts.append(
                f'<div style="margin-bottom:14px;border:1px solid #e2e8f0;border-radius:8px;'
                f'overflow:hidden;background:#fff;">'
                f'<div style="background:#0f172a;color:#fff;padding:8px 12px;font-weight:600;'
                f'font-size:12px;">{escape(stage)} · {len(items)}</div>'
                f'<div style="padding:6px 12px;">'
            )
            for a in items:
                parts.append(
                    f'<div style="padding:8px 0;border-bottom:1px dashed #e2e8f0;">'
                    f'<div style="color:#64748b;font-size:10px;text-transform:uppercase;'
                    f'margin-bottom:4px;">Q{a.question.order}</div>'
                    f'<div style="color:#0f172a;font-weight:500;margin-bottom:4px;font-size:12px;">'
                    f'{escape(a.question.text)}</div>'
                    f'<div style="background:#f1f5f9;padding:6px 10px;border-radius:5px;'
                    f'color:#0f172a;font-size:12px;white-space:pre-wrap;">'
                    f'{escape(_format_answer_value(a.value))}</div>'
                    f'</div>'
                )
            parts.append('</div></div>')
        parts.append('</div>')
        parts.append("""
        <script>
        (function() {
          var btn = document.getElementById('copy-answers-btn');
          var ta  = document.getElementById('answers-plain-text');
          if (!btn || !ta) return;
          btn.addEventListener('click', function() {
            ta.style.left = '0'; ta.select();
            try { document.execCommand('copy'); btn.innerText = '✓ Скопировано'; setTimeout(function(){btn.innerText='📋 Скопировать';}, 1500); }
            catch(e) { if (navigator.clipboard) navigator.clipboard.writeText(ta.value); }
            ta.style.left = '-9999px';
          });
        })();
        </script>
        """)
        return mark_safe("".join(parts))

    # ── custom URLs (CSV экспорт) ──────────────────────────────────────────

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
        submission = Submission.objects.select_related(
            "client", "template", "template__industry", "tariff"
        ).get(pk=object_id)
        buf = io.StringIO()
        buf.write("﻿")
        writer = csv.writer(buf, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["Этап", "№", "Вопрос", "Тип", "Ответ", "Дата ответа"])
        for stage, items in _grouped_answers(submission).items():
            for a in items:
                writer.writerow([
                    stage, a.question.order, a.question.text,
                    a.question.get_field_type_display(),
                    _format_answer_value(a.value),
                    a.answered_at.strftime("%Y-%m-%d %H:%M") if a.answered_at else "",
                ])
        client = submission.client
        slug = (
            f"{client.company}_{client.name}".replace(" ", "_")
            if client else f"submission_{submission.id}"
        )
        response = HttpResponse(buf.getvalue(), content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = (
            f'attachment; filename*=UTF-8\'\'{quote("baqsy_answers_" + slug + ".csv")}'
        )
        return response

    # ── workflow actions ───────────────────────────────────────────────────

    def _ensure_report(self, submission) -> AuditReport:
        report, _ = AuditReport.objects.get_or_create(
            submission=submission,
            defaults={"admin_text": "", "status": AuditReport.Status.DRAFT},
        )
        return report

    @action(description="🤖 Сгенерировать AI-черновик", url_path="generate-ai-draft")
    def generate_ai_draft(self, request, object_id):
        from apps.ai.parameter_analyzer import assemble_full_report
        submission = Submission.objects.select_related("client", "report").get(pk=object_id)
        report = self._ensure_report(submission)
        try:
            text = assemble_full_report(submission)
        except Exception as exc:
            messages.error(request, f"Ошибка генерации: {exc}")
            return HttpResponseRedirect(
                reverse("admin:submissions_submission_change", args=(object_id,))
            )
        existing = (report.admin_text or "").strip()
        report.admin_text = f"{existing}\n\n---\n\n{text}" if existing else text
        report.save(update_fields=["admin_text", "updated_at"])
        messages.success(
            request,
            _("✓ AI-черновик готов. Проверьте текст ниже и нажмите «📨 Отправить клиенту»."),
        )
        return HttpResponseRedirect(
            reverse("admin:submissions_submission_change", args=(object_id,))
        )

    @action(description="📨 Отправить клиенту", url_path="send-to-client")
    def send_to_client(self, request, object_id):
        """Главное действие админа — утвердить + поставить PDF в очередь."""
        from apps.reports.services import approve_report
        submission = Submission.objects.select_related("client").get(pk=object_id)
        report = self._ensure_report(submission)
        ok, err = approve_report(report)
        if not ok:
            messages.error(request, err)
        else:
            messages.success(
                request,
                _(
                    "✓ Отчёт утверждён. PDF готовится — обновите страницу через "
                    "5–10 секунд, появится кнопка «Открыть WhatsApp»."
                ),
            )
        return HttpResponseRedirect(
            reverse("admin:submissions_submission_change", args=(object_id,))
        )

    @action(description="📦 Отметить доставленным", url_path="mark-delivered")
    def mark_delivered(self, request, object_id):
        from apps.reports.services import mark_report_delivered
        submission = Submission.objects.select_related("report").get(pk=object_id)
        report = getattr(submission, "report", None)
        if not report:
            messages.error(request, _("У заявки нет отчёта."))
        else:
            ok, err = mark_report_delivered(report)
            if not ok:
                messages.warning(request, err or "Не удалось пометить.")
            else:
                messages.success(request, _("✓ Заявка помечена как доставленная клиенту."))
        return HttpResponseRedirect(
            reverse("admin:submissions_submission_change", args=(object_id,))
        )

    # ── подсказка после обычного «Сохранить» ──────────────────────────────

    def response_change(self, request, obj):
        """После обычного save показываем подсказку что делать дальше."""
        report = getattr(obj, "report", None)
        if (
            report
            and report.status == AuditReport.Status.DRAFT
            and (report.uploaded_file or (report.admin_text or "").strip())
        ):
            messages.info(
                request,
                _(
                    "✓ Сохранено. Теперь нажмите большую зелёную кнопку "
                    "«📨 Отправить клиенту» сверху страницы."
                ),
            )
        return super().response_change(request, obj)


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
        base = getattr(settings, "SITE_URL", "https://baqsy.tnriazun.com").rstrip("/")
        url = f"{base}/invite/{obj.invite_token}"
        return format_html(
            '<a href="{}" target="_blank" rel="noopener" '
            'style="color:#d97706;font-weight:600;">📎 открыть</a>', url,
        )


@admin.register(AuditGroup)
class AuditGroupAdmin(ModelAdmin):
    list_display = ("id", "submission_link", "quorum_size", "completed_count_badge", "created_at")
    list_filter = ("quorum_size",)
    search_fields = (
        "initiator_submission__client__name",
        "initiator_submission__client__company",
        "participants__email", "participants__name",
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
            "invited":     ("#dbeafe", "#1e40af"),
            "in_progress": ("#fef3c7", "#78350f"),
            "completed":   ("#d1fae5", "#065f46"),
            "expired":     ("#fee2e2", "#991b1b"),
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
