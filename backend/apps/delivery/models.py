from django.db import models
from apps.core.models import TimestampedModel


class DeliveryLog(TimestampedModel):
    class Channel(models.TextChoices):
        TELEGRAM = "telegram", "Telegram"
        WHATSAPP = "whatsapp", "WhatsApp"

    class Status(models.TextChoices):
        QUEUED = "queued", "В очереди"
        SENT = "sent", "Отправлено"
        DELIVERED = "delivered", "Доставлено"
        FAILED = "failed", "Ошибка"

    report = models.ForeignKey(
        "reports.AuditReport",
        on_delete=models.CASCADE,
        related_name="deliveries",
    )
    channel = models.CharField(max_length=20, choices=Channel.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    external_id = models.CharField(max_length=255, blank=True, help_text="External message/delivery ID")
    error = models.TextField(blank=True)

    class Meta:
        verbose_name = "Лог доставки"
        verbose_name_plural = "Логи доставки"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.channel} → {self.status} ({self.report_id})"
