from django import forms
from django.contrib import admin
from django.db import models
from django.utils.html import format_html

from unfold.admin import ModelAdmin

from apps.content.models import ContentBlock


# Map each key prefix to a human-readable section label shown in the admin
# list. Keeps the flat ContentBlock table navigable when there are 20+ blocks.
_SECTION_MAP = [
    ("hero_",             "Hero"),
    ("method_",           "Метод"),
    ("tariff_section_",   "Тарифы"),
    ("case_",             "Кейсы"),
    ("cases_",            "Кейсы"),
    ("faq_",              "FAQ"),
]


def _section_for_key(key: str) -> str:
    for prefix, label in _SECTION_MAP:
        if key.startswith(prefix):
            return label
    return "Прочее"


@admin.register(ContentBlock)
class ContentBlockAdmin(ModelAdmin):
    list_display = ("title", "section_badge", "preview", "key", "is_active")
    list_display_links = ("title", "key")
    list_filter = ("is_active", "content_type")
    search_fields = ("key", "title", "content")
    list_editable = ("is_active",)
    list_per_page = 50
    ordering = ("key",)
    fieldsets = (
        (None, {
            "fields": ("key", "title", "content_type", "is_active"),
            "description": (
                "Ключ (<code>key</code>) используется фронтендом и менять его "
                "нельзя, если уже выведен в лендинг. Остальные поля можно "
                "править свободно — изменения видны на сайте сразу."
            ),
        }),
        ("Содержимое", {
            "fields": ("content",),
        }),
    )
    readonly_fields = ()
    # Plain Textarea with a comfortable size. The landing renders ContentBlock
    # values as plain text via JSX — pushing HTML here would just print tags as
    # literal characters on the site. Keep it simple.
    formfield_overrides = {
        models.TextField: {
            "widget": forms.Textarea(attrs={"rows": 6, "style": "width: 100%; font-size: 15px;"})
        },
    }

    @admin.display(description="Секция", ordering="key")
    def section_badge(self, obj: ContentBlock) -> str:
        section = _section_for_key(obj.key)
        return format_html(
            '<span style="display:inline-block;padding:2px 8px;border-radius:999px;'
            'background:#fef3c7;color:#78350f;font-size:11px;font-weight:600;'
            'text-transform:uppercase;letter-spacing:0.04em;">{}</span>',
            section,
        )

    @admin.display(description="Превью")
    def preview(self, obj: ContentBlock) -> str:
        text = (obj.content or "").strip()
        if not text:
            return format_html('<span style="color:#94a3b8;">—</span>')
        # Strip HTML tags for the list preview so CKEditor markup doesn't bleed in.
        import re
        plain = re.sub(r"<[^>]+>", "", text)
        if len(plain) > 70:
            plain = plain[:67] + "…"
        return format_html('<span style="color:#475569;">{}</span>', plain)
