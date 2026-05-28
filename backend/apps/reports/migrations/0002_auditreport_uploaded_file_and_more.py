"""Add uploaded_file field + tidy help_text on AuditReport.

Generated manually so the migration commit matches what makemigrations
would produce — see Django's serializer behaviour for FileField with a
callable upload_to: the path is recorded as a dotted import.
"""
from django.db import migrations, models

import apps.reports.models


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="auditreport",
            name="uploaded_file",
            field=models.FileField(
                blank=True,
                help_text=(
                    "Готовый PDF или DOCX от админа. Если загружен — он отправляется "
                    "клиенту вместо AI-сгенерированного PDF. Можно использовать вместо "
                    "редактирования текста через AI."
                ),
                null=True,
                upload_to=apps.reports.models._uploaded_report_path,
            ),
        ),
        migrations.AlterField(
            model_name="auditreport",
            name="admin_text",
            field=models.TextField(
                blank=True,
                help_text=(
                    "Текст аудита для AI-генерации PDF. Используется только если "
                    "uploaded_file не загружен."
                ),
            ),
        ),
        migrations.AlterField(
            model_name="auditreport",
            name="pdf_url",
            field=models.URLField(
                blank=True,
                help_text=(
                    "MinIO presigned URL для PDF (заполняется автоматически при "
                    "approve, если PDF собран из admin_text)."
                ),
            ),
        ),
    ]
