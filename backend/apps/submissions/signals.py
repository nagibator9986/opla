"""Signals for the submissions app.

Auto-create AuditReport draft when Submission reaches `completed` status —
removes the manual step where admin had to create the report by hand and
ensures the workflow «анкета завершена → можно генерировать AI-отчёт» is
always one click away in the Submission admin.
"""
from __future__ import annotations

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.submissions.models import Submission

log = logging.getLogger(__name__)


@receiver(post_save, sender=Submission)
def create_audit_report_on_completion(sender, instance: Submission, **kwargs):
    """Создаёт пустой draft AuditReport как только анкета завершена.

    Идемпотентно: если AuditReport уже существует — ничего не делаем.
    Триггер срабатывает для статусов от `completed` и далее, чтобы покрыть
    как новый кейс (свежая completed), так и исторические заявки, которые
    могли остаться без отчёта.
    """
    if instance.status not in (
        Submission.Status.COMPLETED,
        Submission.Status.UNDER_AUDIT,
        Submission.Status.DELIVERED,
    ):
        return

    # Импорт внутри функции — apps.reports может зависеть от apps.submissions
    # и наоборот; ленивый импорт ломает цикл.
    from apps.reports.models import AuditReport

    if AuditReport.objects.filter(submission=instance).exists():
        return

    AuditReport.objects.create(
        submission=instance,
        admin_text="",
        status=AuditReport.Status.DRAFT,
    )
    log.info(
        "auto-created AuditReport draft for submission=%s (status=%s)",
        instance.id,
        instance.status,
    )
