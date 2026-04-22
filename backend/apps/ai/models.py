"""AI assistant configuration + chat session/message persistence."""
from __future__ import annotations

import uuid

from django.db import models
from django.core.exceptions import ValidationError

from apps.core.models import TimestampedModel


class AIAssistantConfig(TimestampedModel):
    """Singleton — only one row allowed. Admin edits greeting/system prompt/etc.

    Configuration is fetched at chat-start time so the landing can be updated
    without a redeploy.
    """

    name = models.CharField(
        max_length=100,
        default="Baqsy AI",
        help_text="Имя ассистента, показывается в шапке чата",
    )
    model = models.CharField(
        max_length=60,
        default="gpt-4o-mini",
        help_text="Модель OpenAI (gpt-4o-mini / gpt-4o / gpt-4-turbo)",
    )
    temperature = models.FloatField(
        default=0.5,
        help_text="0.0–2.0. Чем выше — тем креативнее, но менее предсказуемо",
    )
    max_tokens = models.PositiveIntegerField(
        default=800,
        help_text="Максимальная длина ответа ассистента в токенах",
    )
    system_prompt = models.TextField(
        help_text=(
            "Системный промпт. Описывает личность ассистента, правила, "
            "тон общения. Доступны плейсхолдеры: {{name}}, {{company}}, "
            "{{industry}} — будут подставлены, если данные уже собраны."
        ),
    )
    greeting = models.TextField(
        help_text="Первое сообщение ассистента при открытии чата",
    )
    quick_replies = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            "Кнопки быстрых ответов под приветствием. Формат: "
            '[{"label": "Хочу аудит", "payload": "Расскажи про аудит"}, …]'
        ),
    )
    tariff_prompt = models.TextField(
        blank=True,
        default=(
            "Если клиент готов к оплате, предложи перейти к выбору тарифа. "
            "Упомяни две опции: Ashıde 1 (базовый, 45 000 ₸) и Ashıde 2 "
            "(полный, 135 000 ₸). Не давай технических деталей оплаты — "
            "просто предложи нажать кнопку «Выбрать тариф»."
        ),
        help_text="Дополнительная инструкция для момента, когда нужно перейти к оплате",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Конфигурация AI-ассистента"
        verbose_name_plural = "Конфигурация AI-ассистента"

    def __str__(self):
        return f"{self.name} ({self.model})"

    def clean(self):
        # Enforce singleton behaviour: reject save if another active row exists.
        if self.is_active:
            qs = AIAssistantConfig.objects.filter(is_active=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    "Активная конфигурация AI уже существует. "
                    "Деактивируйте старую перед созданием новой."
                )

    @classmethod
    def get_active(cls) -> "AIAssistantConfig | None":
        return cls.objects.filter(is_active=True).first()


class ChatSession(TimestampedModel):
    """A user's chat thread with the AI.

    Exists before the user is a ClientProfile — once the AI has gathered
    enough data (name/company/whatsapp/city/industry), we create a linked
    ClientProfile and populate `client`.
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Идёт диалог"
        QUALIFIED = "qualified", "Готов к оплате"
        PAID = "paid", "Оплачено"
        ABANDONED = "abandoned", "Заброшен"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(
        "accounts.ClientProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chat_sessions",
    )
    collected_data = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Структурированные данные, собранные ассистентом: "
            "name, company, phone_wa, city, industry_code, goals"
        ),
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    last_user_agent = models.CharField(max_length=255, blank=True)
    last_ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = "Чат-сессия"
        verbose_name_plural = "Чат-сессии"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["client"]),
        ]

    def __str__(self):
        who = self.client.name if self.client else "Аноним"
        return f"Сессия {self.id} — {who} ({self.status})"


class ChatMessage(TimestampedModel):
    class Role(models.TextChoices):
        USER = "user", "Пользователь"
        ASSISTANT = "assistant", "Ассистент"
        SYSTEM = "system", "Система"

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=16, choices=Role.choices)
    content = models.TextField()
    tokens_used = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Сообщение чата"
        verbose_name_plural = "Сообщения чата"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["session", "created_at"]),
        ]

    def __str__(self):
        return f"{self.role}: {self.content[:60]}"
