import secrets
from datetime import timedelta

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.core.models import TimestampedModel
from apps.accounts.managers import UserManager


class BaseUser(AbstractBaseUser, PermissionsMixin, TimestampedModel):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Администратор"
        verbose_name_plural = "Администраторы"

    def __str__(self):
        return self.email


class ClientProfile(TimestampedModel):
    user = models.OneToOneField(
        "accounts.BaseUser",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="client_profile",
    )
    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True)
    name = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    phone_wa = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100, blank=True)
    industry = models.ForeignKey(
        "industries.Industry",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clients",
    )

    class Meta:
        verbose_name = "Профиль клиента"
        verbose_name_plural = "Профили клиентов"

    def __str__(self):
        return f"{self.name} ({self.company})"


def _gen_magic_token() -> str:
    return secrets.token_urlsafe(32)


def _default_magic_expires():
    return timezone.now() + timedelta(minutes=15)


class MagicLink(TimestampedModel):
    """Одноразовая ссылка для входа клиента по WhatsApp-номеру.

    Поток: клиент в модалке «Войти» вводит свой WhatsApp → backend ищет
    ClientProfile по `phone_wa`, создаёт MagicLink с TTL 15 мин и шлёт
    ссылку через WhatsApp-провайдера. По клику ссылка валидируется
    (токен не использован, не истёк) и выдаётся JWT-пара.
    """

    token = models.CharField(
        max_length=64, unique=True, default=_gen_magic_token, editable=False
    )
    client = models.ForeignKey(
        ClientProfile,
        on_delete=models.CASCADE,
        related_name="magic_links",
    )
    expires_at = models.DateTimeField(default=_default_magic_expires)
    used_at = models.DateTimeField(null=True, blank=True)
    requested_ip = models.GenericIPAddressField(null=True, blank=True)
    delivered_via = models.CharField(
        max_length=20,
        blank=True,
        help_text="whatsapp / fallback / manual",
    )

    class Meta:
        verbose_name = "Magic-ссылка"
        verbose_name_plural = "Magic-ссылки"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["token"]),
            models.Index(fields=["client", "-created_at"]),
        ]

    def __str__(self):
        return f"MagicLink {self.token[:10]}… → {self.client_id}"

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    @property
    def is_used(self) -> bool:
        return self.used_at is not None

    @property
    def is_valid(self) -> bool:
        return not self.is_used and not self.is_expired
