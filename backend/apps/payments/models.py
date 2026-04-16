from django.db import models

from apps.core.models import TimestampedModel, UUIDModel


class Tariff(TimestampedModel):
    code = models.SlugField(max_length=50, unique=True)
    title = models.CharField(max_length=255)
    price_kzt = models.DecimalField(max_digits=10, decimal_places=0, help_text="Цена в тенге")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Тариф"
        verbose_name_plural = "Тарифы"
        ordering = ["price_kzt"]

    def __str__(self):
        return f"{self.title} ({self.price_kzt} ₸)"


class Payment(UUIDModel, TimestampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Ожидание"
        SUCCEEDED = "succeeded", "Успешно"
        FAILED = "failed", "Ошибка"
        REFUNDED = "refunded", "Возврат"

    submission = models.ForeignKey(
        "submissions.Submission",
        on_delete=models.CASCADE,
        related_name="payments",
    )
    tariff = models.ForeignKey(
        Tariff,
        on_delete=models.PROTECT,
        related_name="payments",
    )
    transaction_id = models.CharField(max_length=255, unique=True, help_text="CloudPayments TransactionId")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    amount = models.DecimalField(max_digits=10, decimal_places=0)
    currency = models.CharField(max_length=3, default="KZT")
    raw_webhook = models.JSONField(default=dict, blank=True, help_text="Raw CloudPayments webhook payload")

    class Meta:
        verbose_name = "Платёж"
        verbose_name_plural = "Платежи"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment {self.transaction_id} ({self.status})"
