from django.db import models

from apps.core.models import TimestampedModel


def _uploaded_report_path(instance, filename):
    """Путь файла загруженного админом отчёта внутри MinIO bucket.

    Используется значение submission UUID, чтобы один отчёт = один путь,
    а перезагрузка перезаписывает (AWS_S3_FILE_OVERWRITE=False даёт суффикс
    автоматически — это нормально).
    """
    sub_id = str(instance.submission_id)
    return f"reports/uploaded/{sub_id}/{filename}"


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
    admin_text = models.TextField(
        blank=True,
        help_text=(
            "Текст аудита для AI-генерации PDF. Используется только если "
            "uploaded_file не загружен."
        ),
    )
    uploaded_file = models.FileField(
        upload_to=_uploaded_report_path,
        blank=True, null=True,
        help_text=(
            "Готовый PDF или DOCX от админа. Если загружен — он отправляется "
            "клиенту вместо AI-сгенерированного PDF. Можно использовать вместо "
            "редактирования текста через AI."
        ),
    )
    pdf_url = models.URLField(
        blank=True,
        help_text=(
            "MinIO presigned URL для PDF (заполняется автоматически при "
            "approve, если PDF собран из admin_text)."
        ),
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Аудит-отчёт"
        verbose_name_plural = "Аудит-отчёты"

    def __str__(self):
        return f"Report for {self.submission_id} ({self.status})"

    @property
    def has_deliverable(self) -> bool:
        """Есть ли что отправлять клиенту — либо загруженный файл, либо
        сгенерированный PDF (pdf_url)."""
        return bool(self.uploaded_file) or bool(self.pdf_url)
