from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("submissions", "0002_submission_last_reminded_at"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="submission",
            index=models.Index(
                fields=["client", "-created_at"],
                name="submissions_client_created_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="submission",
            index=models.Index(
                fields=["status"],
                name="submissions_status_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="submission",
            index=models.Index(
                fields=["status", "-created_at"],
                name="submissions_status_created_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="answer",
            index=models.Index(
                fields=["submission", "question"],
                name="answers_submission_question_idx",
            ),
        ),
    ]
