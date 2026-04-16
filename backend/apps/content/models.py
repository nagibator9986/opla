from django.db import models
from apps.core.models import TimestampedModel


class ContentBlock(TimestampedModel):
    class ContentType(models.TextChoices):
        TEXT = "text", "Текст"
        HTML = "html", "HTML"

    key = models.SlugField(max_length=100, unique=True, help_text="Unique block identifier, e.g. 'hero_title'")
    title = models.CharField(max_length=255, help_text="Human-readable label for admin")
    content = models.TextField(blank=True)
    content_type = models.CharField(max_length=10, choices=ContentType.choices, default=ContentType.TEXT)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Контент-блок"
        verbose_name_plural = "Контент-блоки"
        ordering = ["key"]

    def __str__(self):
        return f"{self.title} ({self.key})"
