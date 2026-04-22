from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from apps.core.models import TimestampedModel


class Case(TimestampedModel):
    """A client case study shown on the landing + own detail page."""

    slug = models.SlugField(
        max_length=160,
        unique=True,
        help_text="URL-идентификатор. Пример: retail-margin-uplift. "
        "Оставьте пустым — сгенерируется из заголовка.",
        blank=True,
    )
    title = models.CharField(
        max_length=200,
        help_text="Заголовок кейса, например «Рост маржи розничной сети»",
    )
    subtitle = models.CharField(
        max_length=400,
        blank=True,
        help_text="Короткое описание, строка под заголовком на карточке",
    )
    company_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Название компании-клиента (публично — по согласию)",
    )
    industry = models.CharField(
        max_length=100,
        blank=True,
        help_text="Ритейл / IT / Производство / …",
    )
    logo = models.ImageField(
        upload_to="cases/logos/",
        blank=True,
        null=True,
        help_text="Логотип (SVG или PNG с прозрачным фоном). 200–400px по большей стороне",
    )
    cover_image = models.ImageField(
        upload_to="cases/covers/",
        blank=True,
        null=True,
        help_text="Обложка кейса — показывается на детальной странице",
    )
    metric = models.CharField(
        max_length=60,
        blank=True,
        help_text='Крупная цифра: «+15%», «×2», «−30 дней»',
    )
    metric_label = models.CharField(
        max_length=120,
        blank=True,
        help_text='Расшифровка метрики: «маржинальности», «скорость найма»',
    )
    short_text = models.TextField(
        blank=True,
        help_text="Краткое описание на карточке на лендинге (2–3 предложения)",
    )
    body = models.TextField(
        blank=True,
        help_text="Полный текст кейса для страницы подробностей. "
        "Можно использовать двойные переносы для абзацев.",
    )
    # Gradient accent shown on cards; admin picks a preset.
    ACCENT_CHOICES = [
        ("emerald", "Зелёный"),
        ("sky", "Голубой"),
        ("amber", "Янтарный"),
        ("rose", "Розовый"),
        ("violet", "Фиолетовый"),
        ("slate", "Серый"),
    ]
    accent = models.CharField(
        max_length=20, choices=ACCENT_CHOICES, default="emerald"
    )
    order = models.IntegerField(
        default=0,
        help_text="Порядок отображения на лендинге (меньше — выше)",
    )
    is_active = models.BooleanField(default=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Кейс"
        verbose_name_plural = "Кейсы"
        ordering = ("order", "-published_at", "-created_at")
        indexes = [
            models.Index(fields=["is_active", "order"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title, allow_unicode=False)
            if not base:
                base = "case"
            slug = base
            i = 2
            while Case.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return f"/cases/{self.slug}"
