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

    # Shown by the AI assistant BEFORE the first question. Supports placeholders
    # {{name}}, {{company}} that the AI will substitute from collected profile.
    intro_text = models.TextField(
        blank=True,
        default=(
            "Сейчас я задам вам {{total}} вопросов. Займёт около 20 минут. "
            "Можно прерываться и возвращаться — прогресс сохраняется."
        ),
        help_text=(
            "Вводный текст перед первым вопросом. Поддерживает плейсхолдеры "
            "{{name}}, {{company}}, {{total}} — подставятся автоматически."
        ),
    )
    completion_text = models.TextField(
        blank=True,
        default=(
            "Спасибо, {{name}}! Анкета завершена. Наш эксперт разберёт ответы "
            "и пришлёт именной PDF-отчёт в WhatsApp в течение 3–5 рабочих дней."
        ),
        help_text=(
            "Текст после последнего вопроса. Плейсхолдеры {{name}}, {{company}}."
        ),
    )

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
        return f"{self.name} ({self.industry.name} v{self.version})"

    @classmethod
    def create_new_version(cls, old_template):
        """Atomically create a new template version cloning questions from the old one."""
        with transaction.atomic():
            old = cls.objects.select_for_update().get(pk=old_template.pk)
            old_questions = list(old.questions.all())
            next_version = old.version + 1

            old.is_active = False
            old.save(update_fields=["is_active"])

            new_version = cls.objects.create(
                industry=old.industry,
                version=next_version,
                is_active=True,
                name=old.name,
                intro_text=old.intro_text,
                completion_text=old.completion_text,
            )

            # First pass: create all questions without conditions
            old_to_new: dict[int, Question] = {}
            for q in old_questions:
                new_q = Question.objects.create(
                    template=new_version,
                    order=q.order,
                    text=q.text,
                    stage=q.stage,
                    field_type=q.field_type,
                    options=q.options,
                    placeholder=q.placeholder,
                    required=q.required,
                    block=q.block,
                )
                old_to_new[q.pk] = new_q

            # Second pass: wire up conditional rules to the NEW question pks
            for q in old_questions:
                if q.condition_question_id:
                    new_q = old_to_new[q.pk]
                    new_q.condition_question = old_to_new.get(q.condition_question_id)
                    new_q.condition_values = q.condition_values
                    new_q.save(update_fields=["condition_question", "condition_values"])

            return new_version


class Question(TimestampedModel):
    class FieldType(models.TextChoices):
        TEXT = "text", "Текст (свободный ответ)"
        LONGTEXT = "longtext", "Текст (длинный ответ)"
        NUMBER = "number", "Число"
        CHOICE = "choice", "Выбор одного (кнопки)"
        MULTICHOICE = "multichoice", "Множественный выбор (чек-боксы)"
        URL = "url", "Ссылка (URL)"

    class Block(models.TextChoices):
        A = "A", "Блок А — Технический паспорт"
        B = "B", "Блок Б — Содержательная часть"
        C = "C", "Блок В — Глубокое сканирование"

    template = models.ForeignKey(
        QuestionnaireTemplate,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    order = models.PositiveIntegerField(
        help_text="Порядковый номер внутри анкеты (меньше — раньше)",
    )
    stage = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text=(
            "Название этапа для группировки в админке и в чате. "
            "Примеры: «Этап I: Паспорт компании», «Блок II: Менеджер»."
        ),
    )
    text = models.TextField(help_text="Формулировка вопроса (увидит клиент)")
    placeholder = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Подсказка для поля ввода (не обязательна)",
    )
    field_type = models.CharField(
        max_length=20, choices=FieldType.choices, default=FieldType.TEXT
    )
    options = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            'Варианты для choice/multichoice. Формат: '
            '<code>{"choices": ["Вариант 1", "Вариант 2", "Вариант 3"]}</code>'
        ),
    )
    required = models.BooleanField(default=True)
    block = models.CharField(
        max_length=1, choices=Block.choices, default=Block.A
    )

    # ── Conditional logic ────────────────────────────────────────────────
    # Показывать вопрос только если ответ на connected_question ∈ condition_values.
    # Если condition_question пуст — вопрос показывается всегда.
    condition_question = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dependent_questions",
        help_text=(
            "Родительский вопрос. Если указан, текущий вопрос будет показан "
            "только при совпадении ответа с одним из «Значений для показа»."
        ),
    )
    condition_values = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            'Список значений: вопрос показывается, если ответ на родительский ∈ список. '
            'Пример: <code>["Владелец / Совладелец", "Топ-менеджер"]</code>'
        ),
    )

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
        ordering = ["template", "order"]
        unique_together = [("template", "order")]

    def __str__(self):
        return f"Q{self.order}: {self.text[:50]}"

    # ── Runtime helpers used by the chat bot ─────────────────────────────
    def is_visible_for(self, answers_by_question_id: dict) -> bool:
        """Check whether this question should be shown given prior answers.

        `answers_by_question_id` maps question.id → normalised answer value
        (string for text/number/url, string for choice, list[str] for
        multichoice).
        """
        if self.condition_question_id is None:
            return True
        prior = answers_by_question_id.get(self.condition_question_id)
        if prior is None:
            return False
        needed = self.condition_values or []
        if not needed:
            return True
        if isinstance(prior, list):
            return any(v in needed for v in prior)
        return prior in needed
