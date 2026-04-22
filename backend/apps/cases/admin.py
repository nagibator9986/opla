from django import forms
from django.contrib import admin
from django.db import models
from django.urls import reverse
from django.utils.html import format_html

from unfold.admin import ModelAdmin

from apps.cases.models import Case


@admin.register(Case)
class CaseAdmin(ModelAdmin):
    list_display = ("edit_button", "logo_thumb", "title", "company_name", "metric", "order", "is_active")
    list_display_links = ("title",)
    list_filter = ("is_active", "accent", "industry")
    list_editable = ("order", "is_active")
    search_fields = ("title", "subtitle", "company_name", "body")
    prepopulated_fields = {"slug": ("title",)}
    save_on_top = True
    ordering = ("order", "-created_at")

    fieldsets = (
        (
            "Основное",
            {
                "fields": ("title", "slug", "subtitle", "company_name", "industry", "order", "is_active", "published_at"),
            },
        ),
        (
            "Изображения",
            {
                "fields": ("logo", "cover_image"),
                "description": "Логотип — для карточки на лендинге. Обложка — на детальной странице.",
            },
        ),
        (
            "Метрика",
            {
                "fields": ("metric", "metric_label", "accent"),
                "description": 'Пример: <code>+15%</code> «маржинальности», <code>×2</code> «скорость найма»',
            },
        ),
        (
            "Тексты",
            {
                "fields": ("short_text", "body"),
                "description": "<strong>Краткое описание</strong> — на карточке лендинга (2–3 предложения). "
                "<strong>Полный текст</strong> — на детальной странице; абзацы через двойной перенос.",
            },
        ),
    )

    formfield_overrides = {
        models.TextField: {
            "widget": forms.Textarea(attrs={"rows": 8, "style": "width: 100%; font-size: 15px; padding: 10px;"})
        },
    }

    @admin.display(description="")
    def edit_button(self, obj):
        url = reverse("admin:cases_case_change", args=[obj.pk])
        return format_html(
            '<a href="{}" style="display:inline-block;padding:4px 12px;border-radius:6px;'
            'background:#f59e0b;color:#fff;font-size:12px;font-weight:600;'
            'text-decoration:none;border:1px solid #d97706;">✏️ Изменить</a>',
            url,
        )

    @admin.display(description="Лого")
    def logo_thumb(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-height:32px;max-width:80px;object-fit:contain;">',
                obj.logo.url,
            )
        return "—"
