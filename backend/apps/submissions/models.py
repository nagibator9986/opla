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
    last_reminded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["client", "-created_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["status", "-created_at"]),
        ]

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


class AuditGroup(TimestampedModel):
    """Группа участников коллективного аудита (пакет Ashide 2).

    Один Submission «инициатора» хранит платёж и финальный отчёт. Каждый
    из 3–7 участников получает свою анонимную ссылку, по которой
    проходит ту же самую анкету. Их ответы агрегируются в отчёт админом.
    """

    initiator_submission = models.OneToOneField(
        "submissions.Submission",
        on_delete=models.CASCADE,
        related_name="audit_group",
    )
    quorum_size = models.PositiveSmallIntegerField(
        help_text="Количество участников, выбранное инициатором (3–7).",
    )
    invitation_text = models.TextField(
        blank=True,
        help_text="Текст приглашения, который рассылается участникам. "
        "Если пусто — используется дефолт.",
    )

    class Meta:
        verbose_name = "Группа аудита"
        verbose_name_plural = "Группы аудита"

    def __str__(self):
        return f"Группа {self.initiator_submission_id} · {self.quorum_size} участников"

    @property
    def completed_count(self) -> int:
        return self.participants.filter(status=AuditParticipant.Status.COMPLETED).count()

    @property
    def is_quorum_complete(self) -> bool:
        return self.completed_count >= self.quorum_size


class AuditParticipant(TimestampedModel):
    """Один участник коллективного аудита.

    Получает уникальный ``invite_token``, по которому открывает страницу
    /invite/<token> и проходит анкету анонимно (без логина).
    """

    class Status(models.TextChoices):
        INVITED = "invited", "Приглашён"
        IN_PROGRESS = "in_progress", "Заполняет"
        COMPLETED = "completed", "Завершил"
        EXPIRED = "expired", "Истёк"

    group = models.ForeignKey(
        AuditGroup,
        on_delete=models.CASCADE,
        related_name="participants",
    )
    submission = models.ForeignKey(
        "submissions.Submission",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="participant_records",
        help_text="Привязанный Submission участника. Создаётся при первом "
        "ответе. Содержит его собственные ответы.",
    )
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone_wa = models.CharField(max_length=30, blank=True)
    invite_token = models.CharField(
        max_length=64, unique=True,
        help_text="UUID4 hex без дефисов, используется в ссылке /invite/<token>.",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.INVITED,
    )
    invited_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_email_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Участник аудита"
        verbose_name_plural = "Участники аудита"
        ordering = ("group", "id")
        indexes = [
            models.Index(fields=["invite_token"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.email}) · {self.get_status_display()}"


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
        indexes = [
            models.Index(fields=["submission", "question"]),
        ]

    def __str__(self):
        return f"Ответ на Q{self.question.order} ({self.submission_id})"
