import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai", "0001_initial"),
        ("submissions", "0004_rename_answers_submission_question_idx_submissions_submiss_7df7c8_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="chatsession",
            name="mode",
            field=models.CharField(
                choices=[
                    ("chat", "Свободный диалог с AI"),
                    ("questionnaire", "Анкета (по одному вопросу)"),
                ],
                default="chat",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="chatsession",
            name="submission",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="chat_sessions",
                to="submissions.submission",
            ),
        ),
        migrations.AlterField(
            model_name="chatsession",
            name="status",
            field=models.CharField(
                choices=[
                    ("active", "Идёт диалог"),
                    ("qualified", "Готов к оплате"),
                    ("paid", "Оплачено"),
                    ("questionnaire", "Проходит анкету"),
                    ("completed", "Анкета завершена"),
                    ("abandoned", "Заброшен"),
                ],
                default="active",
                max_length=20,
            ),
        ),
    ]
