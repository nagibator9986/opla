import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("industries", "0002_questionnaire_flow_extension"),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditParameter",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("code", models.SlugField(max_length=60, unique=True)),
                ("name", models.CharField(max_length=120)),
                ("description", models.TextField(blank=True)),
                ("system_prompt", models.TextField()),
                ("model", models.CharField(default="gpt-4o-mini", max_length=60)),
                ("temperature", models.FloatField(default=0.4)),
                ("max_tokens", models.PositiveIntegerField(default=1200)),
                ("order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "Параметр аудита",
                "verbose_name_plural": "Параметры аудита",
                "ordering": ("order", "name"),
            },
        ),
        migrations.AddField(
            model_name="question",
            name="parameter",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="questions",
                to="industries.auditparameter",
            ),
        ),
    ]
