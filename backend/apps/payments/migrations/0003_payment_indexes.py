from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0002_initial"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="payment",
            index=models.Index(
                fields=["submission", "-created_at"],
                name="payments_submission_created_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="payment",
            index=models.Index(
                fields=["status"],
                name="payments_status_idx",
            ),
        ),
    ]
