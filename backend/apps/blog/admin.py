from django import forms
from django.contrib import admin
from django.db import models
from django.urls import reverse
from django.utils.html import format_html

from unfold.admin import ModelAdmin

from apps.blog.models import BlogPost


@admin.register(BlogPost)
class BlogPostAdmin(ModelAdmin):
    list_display = (
        "edit_button",
        "cover_thumb",
        "title",
        "category_badge",
        "is_published",
        "order",
        "published_at",
    )
    list_display_links = ("title",)
    list_filter = ("is_published", "category")
    search_fields = ("title", "excerpt", "body")
    list_editable = ("order", "is_published")
    list_per_page = 50
    save_on_top = True
    prepopulated_fields = {"slug": ("title",)}

    fieldsets = (
        (
            "Основное",
            {
                "fields": (
                    "title",
                    "slug",
                    "category",
                    "is_published",
                    "published_at",
                    "order",
                    "reading_time_min",
                ),
                "description": (
                    "Если запись ещё в работе — оставьте «Опубликовать» выключенным. "
                    "Без даты публикации запись не появится на лендинге."
                ),
            },
        ),
        ("Обложка", {"fields": ("cover_image",)}),
        (
            "Тексты",
            {
                "fields": ("excerpt", "body"),
                "description": (
                    "<strong>Краткое описание</strong> — для карточки лендинга. "
                    "<strong>Полный текст</strong> — для страницы статьи. "
                    "Двойной перенос разделяет абзацы."
                ),
            },
        ),
    )

    formfield_overrides = {
        models.TextField: {
            "widget": forms.Textarea(
                attrs={"rows": 10, "style": "width: 100%; font-size: 15px; padding: 10px;"}
            )
        },
    }

    @admin.display(description="")
    def edit_button(self, obj):
        url = reverse("admin:blog_blogpost_change", args=[obj.pk])
        return format_html(
            '<a href="{}" style="display:inline-block;padding:4px 12px;border-radius:6px;'
            'background:#f59e0b;color:#fff;font-size:12px;font-weight:600;'
            'text-decoration:none;border:1px solid #d97706;">✏️ Изменить</a>',
            url,
        )

    @admin.display(description="Обложка")
    def cover_thumb(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="height:42px;width:60px;object-fit:cover;'
                'border-radius:6px;">',
                obj.cover_image.url,
            )
        return "—"

    @admin.display(description="Категория")
    def category_badge(self, obj):
        colors = {
            "article": ("#dbeafe", "#1e40af"),
            "glossary": ("#fef3c7", "#78350f"),
            "philosophy": ("#ede9fe", "#5b21b6"),
        }
        bg, fg = colors.get(obj.category, ("#e2e8f0", "#0f172a"))
        return format_html(
            '<span style="display:inline-block;padding:2px 10px;border-radius:999px;'
            'background:{};color:{};font-size:11px;font-weight:600;'
            'text-transform:uppercase;letter-spacing:0.04em;">{}</span>',
            bg,
            fg,
            obj.get_category_display(),
        )
