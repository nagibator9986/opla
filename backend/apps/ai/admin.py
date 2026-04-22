from django import forms
from django.contrib import admin, messages
from django.db import models
from django.utils.html import format_html

from unfold.admin import ModelAdmin

from apps.ai.models import AIAssistantConfig, ChatMessage, ChatSession


@admin.register(AIAssistantConfig)
class AIAssistantConfigAdmin(ModelAdmin):
    list_display = ("name", "model", "temperature", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "system_prompt", "greeting")
    save_on_top = True

    fieldsets = (
        (
            "Основное",
            {
                "fields": ("name", "is_active"),
                "description": (
                    "Одна активная конфигурация на весь сайт. "
                    "Чтобы протестировать новую версию промпта, "
                    "создайте дубликат, деактивируйте старый, "
                    "активируйте новый."
                ),
            },
        ),
        (
            "OpenAI параметры",
            {
                "fields": ("model", "temperature", "max_tokens"),
                "description": (
                    "Рекомендуемые настройки: <code>gpt-4o-mini</code> для "
                    "скорости и стоимости, temperature 0.4–0.7, max_tokens 800. "
                    "Для более точных ответов — <code>gpt-4o</code> и "
                    "temperature 0.3."
                ),
            },
        ),
        (
            "Поведение ассистента",
            {
                "fields": ("system_prompt",),
                "description": (
                    "Системный промпт задаёт характер, правила и цель диалога. "
                    "Пример структуры: (1) кто ты и что делаешь, (2) как "
                    "общаешься (тон, длина ответов), (3) какие данные нужно "
                    "собрать у клиента, (4) как и когда предлагать тариф."
                ),
            },
        ),
        (
            "Интерфейс чата",
            {
                "fields": ("greeting", "quick_replies", "tariff_prompt"),
                "description": (
                    "<strong>Greeting</strong> — первое сообщение в чате. "
                    "<strong>Quick replies</strong> — кнопки быстрых ответов "
                    "ниже приветствия. Формат: "
                    '<code>[{"label": "Хочу аудит", "payload": "Расскажите про аудит"}]</code>. '
                    "<strong>Tariff prompt</strong> — инструкция для момента "
                    "перехода к оплате."
                ),
            },
        ),
    )

    formfield_overrides = {
        models.TextField: {
            "widget": forms.Textarea(
                attrs={
                    "rows": 10,
                    "style": "width: 100%; font-size: 14px; font-family: ui-monospace, "
                    "SFMono-Regular, Menlo, monospace; padding: 10px;",
                }
            )
        },
        models.JSONField: {
            "widget": forms.Textarea(
                attrs={"rows": 6, "style": "width: 100%; font-family: ui-monospace, monospace;"}
            )
        },
    }

    def save_model(self, request, obj, form, change):
        # Auto-deactivate any other active config — there can be only one.
        if obj.is_active:
            AIAssistantConfig.objects.exclude(pk=obj.pk).filter(is_active=True).update(
                is_active=False
            )
            messages.info(request, "Старые активные конфигурации деактивированы.")
        super().save_model(request, obj, form, change)


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ("role", "content", "tokens_used", "created_at")
    can_delete = False
    show_change_link = False

    def has_add_permission(self, request, obj):
        return False


@admin.register(ChatSession)
class ChatSessionAdmin(ModelAdmin):
    list_display = ("id_short", "client_name", "status_badge", "message_count", "created_at")
    list_filter = ("status",)
    search_fields = ("id", "client__name", "client__company", "collected_data")
    readonly_fields = (
        "id",
        "client",
        "collected_data",
        "last_user_agent",
        "last_ip",
        "created_at",
        "updated_at",
    )
    inlines = [ChatMessageInline]

    @admin.display(description="ID")
    def id_short(self, obj):
        return str(obj.id)[:8] + "…"

    @admin.display(description="Клиент")
    def client_name(self, obj):
        if obj.client:
            return f"{obj.client.name} ({obj.client.company})"
        data = obj.collected_data or {}
        if data.get("name"):
            return f"{data['name']} (черновик)"
        return "—"

    @admin.display(description="Статус")
    def status_badge(self, obj):
        colors = {
            "active": ("#fef3c7", "#92400e"),
            "qualified": ("#dbeafe", "#1e40af"),
            "paid": ("#d1fae5", "#065f46"),
            "abandoned": ("#fee2e2", "#991b1b"),
        }
        bg, fg = colors.get(obj.status, ("#e2e8f0", "#0f172a"))
        return format_html(
            '<span style="background:{};color:{};padding:3px 10px;border-radius:999px;'
            'font-size:11px;font-weight:600;text-transform:uppercase;">{}</span>',
            bg,
            fg,
            obj.get_status_display(),
        )

    @admin.display(description="Сообщений")
    def message_count(self, obj):
        return obj.messages.count()


@admin.register(ChatMessage)
class ChatMessageAdmin(ModelAdmin):
    list_display = ("created_at", "session", "role", "preview", "tokens_used")
    list_filter = ("role",)
    search_fields = ("content", "session__id")
    readonly_fields = ("session", "role", "content", "tokens_used", "created_at", "updated_at")

    @admin.display(description="Текст")
    def preview(self, obj):
        return (obj.content or "")[:80]
