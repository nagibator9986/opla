from django.core.exceptions import ValidationError
from django.db import models
from django_fsm import FSMField, transition

from apps.core.models import TimestampedModel, UUIDModel


class Submission(UUIDModel, TimestampedModel):
    class Status(models.TextChoices):
        CREATED = "created", "Создан"
        IN_PROGRESS_BASIC = "in_progress_basic", "Базовый онбординг"
        PAID = "paid", "Оплачен"
        IN_PROGRESS_FULL = "in_progress_full", "Заполнение анкеты"
        COMPLETED = "completed", "Анкета завершена"
        UNDER_AUDIT = "under_audit", "На аудите"
        DELIVERED = "delivered", "Доставлен"

    client = models.ForeignKey(
        "accounts.ClientProfile",
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    template = models.ForeignKey(
        "industries.QuestionnaireTemplate",
        on_delete=models.PROTECT,
        related_name="submissions",
    )
    tariff = models.ForeignKey(
        "payments.Tariff",
        on_delete=models.PROTECT,
        related_name="submissions",
        null=True,
        blank=True,
    )
    status = FSMField(default=Status.CREATED, choices=Status.choices)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ["-created_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_template_id = self.template_id

    def save(self, *args, **kwargs):
        if self.pk and self._original_template_id is not None:
            if self.template_id != self._original_template_id:
                raise ValidationError(
                    "Нельзя изменить шаблон анкеты после создания заказа."
                )
        super().save(*args, **kwargs)
        self._original_template_id = self.template_id

    def __str__(self):
        return f"Заказ {self.id} ({self.client})"

    # FSM transitions
    @transition(field=status, source=Status.CREATED, target=Status.IN_PROGRESS_BASIC)
    def start_onboarding(self):
        pass

    @transition(field=status, source=Status.IN_PROGRESS_BASIC, target=Status.PAID)
    def mark_paid(self):
        pass

    @transition(field=status, source=Status.PAID, target=Status.IN_PROGRESS_FULL)
    def start_questionnaire(self):
        pass

    @transition(field=status, source=Status.IN_PROGRESS_FULL, target=Status.COMPLETED)
    def complete_questionnaire(self):
        from django.utils import timezone
        self.completed_at = timezone.now()

    @transition(field=status, source=Status.COMPLETED, target=Status.UNDER_AUDIT)
    def start_audit(self):
        pass

    @transition(field=status, source=Status.UNDER_AUDIT, target=Status.DELIVERED)
    def mark_delivered(self):
        pass


class Answer(TimestampedModel):
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    question = models.ForeignKey(
        "industries.Question",
        on_delete=models.PROTECT,
        related_name="answers",
    )
    value = models.JSONField(help_text="Answer data: {text: ''} or {number: N} or {choice: ''} or {choices: []}")
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ответ"
        verbose_name_plural = "Ответы"
        unique_together = [("submission", "question")]
        ordering = ["question__order"]

    def __str__(self):
        return f"Ответ на Q{self.question.order} ({self.submission_id})"
