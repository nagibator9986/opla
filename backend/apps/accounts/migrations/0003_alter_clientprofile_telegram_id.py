from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_clientprofile_user"),
    ]

    operations = [
        migrations.AlterField(
            model_name="clientprofile",
            name="telegram_id",
            field=models.BigIntegerField(blank=True, null=True, unique=True),
        ),
    ]
