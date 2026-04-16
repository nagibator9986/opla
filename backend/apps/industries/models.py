from django.db import models, transaction

from apps.core.models import TimestampedModel


class Industry(TimestampedModel):
    name = models.CharField(max_length=100)
    code = models.SlugField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Отрасль"
        verbose_name_plural = "Отрасли"
        ordering = ["name"]

    def __str__(self):
        return self.name


class QuestionnaireTemplate(TimestampedModel):
    industry = models.ForeignKey(
        Industry,
        on_delete=models.CASCADE,
        related_name="templates",
    )
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    name = models.CharField(max_length=255)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Шаблон анкеты"
        verbose_name_plural = "Шаблоны анкет"
        unique_together = [("industry", "version")]
        constraints = [
            models.UniqueConstraint(
                fields=["industry"],
                condition=models.Q(is_active=True),
                name="one_active_template_per_industry",
            )
        ]
        ordering = ["industry", "-version"]

    def __str__(self):
        return f"{self.industry.name} v{self.version}"

    @classmethod
    def create_new_version(cls, old_template):
        """Atomically create a new template version cloning questions from the old one.

        Deactivates old template FIRST to avoid partial unique constraint violation,
        then creates new active version.
        """
        with transaction.atomic():
            old = cls.objects.select_for_update().get(pk=old_template.pk)
            old_questions = list(old.questions.all())
            next_version = old.version + 1

            # Deactivate old BEFORE creating new (avoids partial unique constraint violation)
            old.is_active = False
            old.save(update_fields=["is_active"])

            new_version = cls.objects.create(
                industry=old.industry,
                version=next_version,
                is_active=True,
                name=old.name,
            )

            for q in old_questions:
                Question.objects.create(
                    template=new_version,
                    order=q.order,
                    text=q.text,
                    field_type=q.field_type,
                    options=q.options,
                    required=q.required,
                    block=q.block,
                )

            return new_version


class Question(TimestampedModel):
    class FieldType(models.TextChoices):
        TEXT = "text", "Текст"
        NUMBER = "number", "Число"
        CHOICE = "choice", "Выбор одного"
        MULTICHOICE = "multichoice", "Множественный выбор"

    class Block(models.TextChoices):
        A = "A", "Блок А — Технический паспорт"
        B = "B", "Блок Б — Содержательная часть"
        C = "C", "Блок В — Глубокое сканирование"

    template = models.ForeignKey(
        QuestionnaireTemplate,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    order = models.PositiveIntegerField()
    text = models.TextField()
    field_type = models.CharField(max_length=20, choices=FieldType.choices, default=FieldType.TEXT)
    options = models.JSONField(default=dict, blank=True, help_text="Options for choice/multichoice fields")
    required = models.BooleanField(default=True)
    block = models.CharField(max_length=1, choices=Block.choices, default=Block.A)

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
        ordering = ["template", "order"]
        unique_together = [("template", "order")]

    def __str__(self):
        return f"Q{self.order}: {self.text[:50]}"
