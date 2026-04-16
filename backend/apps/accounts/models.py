from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

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
    telegram_id = models.BigIntegerField(unique=True)
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
