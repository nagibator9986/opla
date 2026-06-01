"""Add rejection_reason to Submission for qualification-filter flow."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("submissions", "0006_rename_submission_invite_t_idx_submissions_invite__3cf734_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="submission",
            name="rejection_reason",
            field=models.TextField(
                blank=True,
                default="",
                help_text=(
                    "Если заполнено — клиент не прошёл фильтр квалификации "
                    "(оборот < 50 млн ₸ или сотрудников < 10). Анкета не "
                    "продолжается, в кабинете показывается карточка отказа."
                ),
            ),
        ),
    ]
