import uuid

from django.core.exceptions import ValidationError
from django.db import models


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class SiteSettings(TimestampedModel):
    """Singleton-конфигурация платформы.

    Управляется через админку, читается фронтом через
    ``/api/v1/content/`` (вместе с ContentBlocks). Singleton — в БД
    всегда ровно один экземпляр (pk=1).
    """

    payments_enabled = models.BooleanField(
        default=False,
        verbose_name="Платёжная система включена",
        help_text=(
            "Если ВЫКЛЮЧЕНО — клиенты получают доступ к анкете и отчёту "
            "БЕЗ оплаты (для тестирования или промо-периода). "
            "Если ВКЛЮЧЕНО — стандартный флоу: тариф → оплата через "
            "CloudPayments → анкета → отчёт."
        ),
    )
    free_mode_banner = models.CharField(
        max_length=255,
        blank=True,
        default="Период открытого доступа · аудит бесплатно",
        verbose_name="Текст плашки в свободном режиме",
        help_text="Показывается над тарифами когда платежи выключены.",
    )

    class Meta:
        verbose_name = "Настройки платформы"
        verbose_name_plural = "Настройки платформы"

    def __str__(self):
        return "Настройки платформы"

    def clean(self):
        # Singleton-гард: при попытке создать второй экземпляр — ошибка.
        if not self.pk and SiteSettings.objects.exists():
            raise ValidationError(
                "Настройки платформы уже существуют. Редактируйте существующую запись."
            )

    @classmethod
    def get_solo(cls) -> "SiteSettings":
        """Получить (создать, если ещё нет) singleton-настройки."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
