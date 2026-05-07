from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_magiclink"),
    ]

    operations = [
        migrations.DeleteModel(
            name="MagicLink",
        ),
    ]
