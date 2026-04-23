from adminsortable2.admin import SortableAdminBase, SortableInlineAdminMixin
from django import forms
from django.contrib import admin, messages
from django.db import models
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from unfold.admin import ModelAdmin, TabularInline

from apps.industries.models import Industry, Question, QuestionnaireTemplate


class QuestionInline(SortableInlineAdminMixin, TabularInline):
    """Quick-edit inline used inside QuestionnaireTemplate.

    Shows core columns so the admin can re-order / tweak text without leaving
    the template page. For conditional rules — use the dedicated Question
    change form (click the question text).
    """

    model = Question
    extra = 1
    fields = (
        "order",
        "stage",
        "text",
        "field_type",
        "required",
        "condition_question",
        "condition_values",
    )
    autocomplete_fields = ("condition_question",)
    show_change_link = True
    classes = ("collapse-on-load",)

    formfield_overrides = {
        models.TextField: {
            "widget": forms.Textarea(
                attrs={"rows": 2, "style": "width: 100%; min-width: 320px;"}
            )
        },
        models.JSONField: {
            "widget": forms.Textarea(attrs={"rows": 2, "style": "width: 100%;"})
        },
    }


@admin.register(Industry)
class IndustryAdmin(ModelAdmin):
    list_display = ("name", "code", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "code")
    prepopulated_fields = {"code": ("name",)}


@admin.register(QuestionnaireTemplate)
class QuestionnaireTemplateAdmin(SortableAdminBase, ModelAdmin):
    list_display = ("name", "industry", "version", "question_count", "is_active", "published_at")
    list_filter = ("industry", "is_active")
    search_fields = ("name", "industry__name")
    inlines = [QuestionInline]
    readonly_fields = ("version", "published_at")
    save_on_top = True

    fieldsets = (
        (None, {
            "fields": ("industry", "name", "is_active", "version", "published_at"),
        }),
        ("Тексты чата", {
            "fields": ("intro_text", "completion_text"),
            "description": (
                "<strong>intro_text</strong> — показывается перед первым вопросом. "
                "<strong>completion_text</strong> — после последнего. "
                "Плейсхолдеры: <code>{{name}}</code>, <code>{{company}}</code>, "
                "<code>{{total}}</code>."
            ),
        }),
    )

    formfield_overrides = {
        models.TextField: {
            "widget": forms.Textarea(
                attrs={"rows": 4, "style": "width: 100%; font-size: 14px; padding: 10px;"}
            )
        },
    }

    @admin.display(description="Вопросов", ordering="id")
    def question_count(self, obj):
        count = obj.questions.count()
        return format_html(
            '<span style="display:inline-block;padding:2px 10px;border-radius:999px;'
            'background:#e0f2fe;color:#075985;font-size:12px;font-weight:600;">{}</span>',
            count,
        )

    def save_model(self, request, obj, form, change):
        if change and obj.is_active:
            new_version = QuestionnaireTemplate.create_new_version(obj)
            messages.success(
                request,
                _(f"Создана новая версия шаблона: v{new_version.version}"),
            )
        else:
            super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        if obj and not obj.is_active:
            return False
        return super().has_change_permission(request, obj)


@admin.register(Question)
class QuestionAdmin(ModelAdmin):
    """Standalone Question change form — used for rich editing including
    conditional logic. The inline inside QuestionnaireTemplate is fine for
    quick edits, but setting up dependencies is easier here.
    """

    list_display = ("order", "stage_badge", "preview", "field_type", "required_badge", "template")
    list_display_links = ("preview",)
    list_filter = ("template", "field_type", "required", "block")
    search_fields = ("text", "stage", "template__name")
    ordering = ("template", "order")
    autocomplete_fields = ("condition_question",)
    save_on_top = True

    fieldsets = (
        (None, {
            "fields": ("template", "order", "stage", "block", "required"),
        }),
        ("Вопрос", {
            "fields": ("text", "placeholder", "field_type", "options"),
            "description": (
                "Для <strong>choice</strong> и <strong>multichoice</strong> "
                "в поле <em>options</em> укажите JSON:<br>"
                "<code>{\"choices\": [\"Вариант 1\", \"Вариант 2\", \"Вариант 3\"]}</code><br>"
                "Бот покажет их как кнопки под вопросом."
            ),
        }),
        ("Условная логика (адаптивный флоу)", {
            "fields": ("condition_question", "condition_values"),
            "description": (
                "Если <strong>condition_question</strong> указан, этот вопрос "
                "будет показан <em>только если</em> ответ на родительский ∈ "
                "<strong>condition_values</strong>. Оставьте пустым, чтобы "
                "вопрос показывался всегда.<br>"
                "Пример: родитель — «Ваш уровень ответственности», "
                "значения — <code>[\"Владелец / Совладелец\", \"Топ-менеджер\"]</code>."
            ),
        }),
    )

    formfield_overrides = {
        models.TextField: {
            "widget": forms.Textarea(
                attrs={"rows": 4, "style": "width: 100%; font-size: 15px; padding: 10px;"}
            )
        },
        models.JSONField: {
            "widget": forms.Textarea(
                attrs={"rows": 3, "style": "width: 100%; font-family: ui-monospace, monospace;"}
            )
        },
    }

    @admin.display(description="Этап", ordering="stage")
    def stage_badge(self, obj):
        if not obj.stage:
            return "—"
        colors = {
            "Этап I": ("#fef3c7", "#78350f"),
            "Этап II": ("#dbeafe", "#1e40af"),
            "Этап III": ("#ede9fe", "#5b21b6"),
            "Блок II · Менеджер": ("#d1fae5", "#065f46"),
            "Блок II · Владелец": ("#fee2e2", "#991b1b"),
        }
        bg, fg = "#e2e8f0", "#0f172a"
        for prefix, (pb, pf) in colors.items():
            if obj.stage.startswith(prefix):
                bg, fg = pb, pf
                break
        return format_html(
            '<span style="display:inline-block;padding:2px 8px;border-radius:999px;'
            'background:{};color:{};font-size:11px;font-weight:600;">{}</span>',
            bg,
            fg,
            obj.stage[:40],
        )

    @admin.display(description="Текст")
    def preview(self, obj):
        return (obj.text or "")[:90]

    @admin.display(description="Обяз.")
    def required_badge(self, obj):
        return format_html(
            '<span style="color:{};">{}</span>',
            "#059669" if obj.required else "#94a3b8",
            "да" if obj.required else "нет",
        )
