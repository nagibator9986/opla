from django.db import models
from apps.core.models import TimestampedModel


class AuditReport(TimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        APPROVED = "approved", "Утверждён"
        SENT = "sent", "Отправлен"

    submission = models.OneToOneField(
        "submissions.Submission",
        on_delete=models.CASCADE,
        related_name="report",
    )
    admin_text = models.TextField(blank=True, help_text="Текст аудита от администратора")
    pdf_url = models.URLField(blank=True, help_text="MinIO presigned URL to PDF")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Аудит-отчёт"
        verbose_name_plural = "Аудит-отчёты"

    def __str__(self):
        return f"Report for {self.submission_id} ({self.status})"
