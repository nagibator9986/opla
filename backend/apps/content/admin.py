import re

from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from django_ckeditor_5.widgets import CKEditor5Widget
from unfold.admin import ModelAdmin

from apps.content.models import ContentBlock
from apps.core.sanitize import sanitize_html


class ContentBlockForm(forms.ModelForm):
    class Meta:
        model = ContentBlock
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rich-редактор ТОЛЬКО для HTML-блоков (длинные тексты: метод, FAQ,
        # донат и т.п.). Для текстовых меток (заголовки, цены, ссылки, кнопки)
        # — обычная textarea: CKEditor оборачивает любой текст в <p>, а такие
        # блоки выводятся на фронте инлайн как {c.key} и показали бы теги.
        if self.instance and self.instance.content_type == ContentBlock.ContentType.HTML:
            self.fields["content"].widget = CKEditor5Widget(config_name="content_block")
        else:
            self.fields["content"].widget = forms.Textarea(
                attrs={"rows": 8, "style": "width: 100%; font-size: 15px; padding: 10px;"}
            )

    def clean(self):
        # Санитайзим в clean(), а НЕ в clean_content: поля чистятся в порядке
        # объявления модели, где content идёт раньше content_type, поэтому в
        # clean_content значения content_type ещё нет (→ санитайз пропускался
        # бы). В clean() доступны все очищенные поля. Текстовые блоки не трогаем,
        # иначе nh3 исказил бы безобидный текст вроде «5 < 10».
        cleaned = super().clean()
        if cleaned.get("content_type") == ContentBlock.ContentType.HTML:
            cleaned["content"] = sanitize_html(cleaned.get("content") or "")
        return cleaned


# Map each key prefix to a human-readable section label shown in the admin
# list. Keeps the flat ContentBlock table navigable when there are 20+ blocks.
_SECTION_MAP = [
    ("hero_",             "Hero"),
    ("method_",           "Метод"),
    ("tariff_section_",   "Тарифы"),
    ("case_",             "Кейсы"),
    ("cases_",            "Кейсы"),
    ("faq_",              "FAQ"),
    ("blog_",             "Статьи"),
    ("footer_",           "Футер"),
    ("legal_",            "Реквизиты"),
    ("chat_",             "Чат / AI"),
]


def _section_for_key(key: str) -> str:
    for prefix, label in _SECTION_MAP:
        if key.startswith(prefix):
            return label
    return "Прочее"


@admin.register(ContentBlock)
class ContentBlockAdmin(ModelAdmin):
    form = ContentBlockForm
    # Edit-button column is the obvious CTA so users don't have to guess which
    # cell is clickable. `title` is also a link for those who prefer text.
    list_display = ("edit_button", "title", "section_badge", "preview", "key", "is_active")
    list_display_links = ("title", "key")
    list_filter = ("is_active", "content_type")
    search_fields = ("key", "title", "content")
    list_editable = ("is_active",)
    list_per_page = 50
    ordering = ("key",)
    save_on_top = True

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
            "description": (
                "Введите текст и нажмите «Сохранить» внизу страницы. "
                "Фронтенд подхватит изменения в течение 5 минут (или сразу "
                "при hard-refresh)."
            ),
        }),
    )
    # Виджет поля content выбирается в ContentBlockForm.__init__ по content_type:
    # CKEditor для HTML-блоков, обычная textarea для текстовых меток.

    @admin.display(description="")
    def edit_button(self, obj: ContentBlock) -> str:
        url = reverse("admin:content_contentblock_change", args=[obj.pk])
        return format_html(
            '<a href="{}" style="display:inline-block;padding:4px 12px;'
            'border-radius:6px;background:#f59e0b;color:#ffffff;'
            'font-size:12px;font-weight:600;text-decoration:none;'
            'border:1px solid #d97706;">✏️ Изменить</a>',
            url,
        )

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
        plain = re.sub(r"<[^>]+>", "", text)
        if len(plain) > 70:
            plain = plain[:67] + "…"
        return format_html('<span style="color:#475569;">{}</span>', plain)
