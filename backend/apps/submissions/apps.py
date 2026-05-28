from django.apps import AppConfig


class SubmissionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.submissions"
    verbose_name = "Submissions"

    def ready(self):
        # Подключаем сигналы: автосоздание AuditReport при completed/under_audit
        from apps.submissions import signals  # noqa: F401
