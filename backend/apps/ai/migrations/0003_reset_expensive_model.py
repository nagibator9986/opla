"""Force AIAssistantConfig.model back to gpt-4o-mini if a gpt-5* snapshot
was set via admin. April 2026: gpt-5-2026-03-05 was switched on in admin
and burned ~$10 in a few days. This guards against repeat at deploy time."""
from django.db import migrations


SAFE_MODEL = "gpt-4o-mini"


def reset_expensive_model(apps, schema_editor):
    AIAssistantConfig = apps.get_model("ai", "AIAssistantConfig")
    AIAssistantConfig.objects.filter(model__startswith="gpt-5").update(model=SAFE_MODEL)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("ai", "0002_chatsession_mode_submission"),
    ]

    operations = [
        migrations.RunPython(reset_expensive_model, noop_reverse),
    ]
