from django.db import models
from django.utils.text import slugify

from apps.core.models import TimestampedModel


class BlogCategory(TimestampedModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Категория блога"
        verbose_name_plural = "Категории блога"
        ordering = ("order", "name")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=False) or "category"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class BlogPost(TimestampedModel):
    """Статья блога / глоссарий-термин.

    Админ вручную наполняет тело статьи. На лендинге показываем превью
    последних 3 опубликованных, на /blog/<slug> — полный текст.
    """

    class Category(models.TextChoices):
        ARTICLE = "article", "Статья"
        GLOSSARY = "glossary", "Глоссарий"
        PHILOSOPHY = "philosophy", "Философия"

    slug = models.SlugField(
        max_length=200, unique=True, blank=True,
        help_text="URL-идентификатор. Генерируется из заголовка автоматически.",
    )
    title = models.CharField(max_length=255)
    excerpt = models.TextField(
        blank=True,
        help_text="Краткое описание (1–2 предложения), показывается на карточке "
        "лендинга и в превью статьи.",
    )
    body = models.TextField(
        blank=True,
        help_text="Полный текст статьи. Двойной перенос — новый абзац. "
        "Поддерживается простой текст; HTML-теги отображаются как символы.",
    )
    category = models.CharField(
        max_length=20, choices=Category.choices, default=Category.ARTICLE,
    )
    cover_image = models.ImageField(
        upload_to="blog/covers/", blank=True, null=True,
        help_text="Обложка для карточки и страницы статьи (рекомендация 1600×900).",
    )
    reading_time_min = models.PositiveIntegerField(
        default=5,
        help_text="Время чтения в минутах (для подписи на карточке).",
    )
    is_published = models.BooleanField(
        default=False,
        help_text="Опубликовать статью. Не отмечайте — пока готовите черновик.",
    )
    published_at = models.DateTimeField(null=True, blank=True)
    order = models.IntegerField(
        default=0,
        help_text="Порядок отображения на лендинге (меньше — раньше). "
        "При равных — по дате публикации.",
    )

    class Meta:
        verbose_name = "Запись блога"
        verbose_name_plural = "Записи блога"
        ordering = ("order", "-published_at", "-created_at")
        indexes = [
            models.Index(fields=["is_published", "order"]),
            models.Index(fields=["category"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title, allow_unicode=False) or "post"
            slug = base
            i = 2
            while BlogPost.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
