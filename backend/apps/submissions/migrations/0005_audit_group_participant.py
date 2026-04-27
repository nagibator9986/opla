import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("submissions", "0004_rename_answers_submission_question_idx_submissions_submiss_7df7c8_idx_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditGroup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("quorum_size", models.PositiveSmallIntegerField()),
                ("invitation_text", models.TextField(blank=True)),
                (
                    "initiator_submission",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="audit_group",
                        to="submissions.submission",
                    ),
                ),
            ],
            options={
                "verbose_name": "Группа аудита",
                "verbose_name_plural": "Группы аудита",
            },
        ),
        migrations.CreateModel(
            name="AuditParticipant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=255)),
                ("email", models.EmailField(max_length=254)),
                ("phone_wa", models.CharField(blank=True, max_length=30)),
                ("invite_token", models.CharField(max_length=64, unique=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("invited", "Приглашён"),
                            ("in_progress", "Заполняет"),
                            ("completed", "Завершил"),
                            ("expired", "Истёк"),
                        ],
                        default="invited",
                        max_length=20,
                    ),
                ),
                ("invited_at", models.DateTimeField(auto_now_add=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("last_email_sent_at", models.DateTimeField(blank=True, null=True)),
                (
                    "group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="participants",
                        to="submissions.auditgroup",
                    ),
                ),
                (
                    "submission",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="participant_records",
                        to="submissions.submission",
                    ),
                ),
            ],
            options={
                "verbose_name": "Участник аудита",
                "verbose_name_plural": "Участники аудита",
                "ordering": ("group", "id"),
            },
        ),
        migrations.AddIndex(
            model_name="auditparticipant",
            index=models.Index(fields=["invite_token"], name="submission_invite_t_idx"),
        ),
        migrations.AddIndex(
            model_name="auditparticipant",
            index=models.Index(fields=["status"], name="submission_part_status_idx"),
        ),
    ]
