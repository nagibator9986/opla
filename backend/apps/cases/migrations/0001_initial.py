from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Case",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("slug", models.SlugField(blank=True, max_length=160, unique=True)),
                ("title", models.CharField(max_length=200)),
                ("subtitle", models.CharField(blank=True, max_length=400)),
                ("company_name", models.CharField(blank=True, max_length=200)),
                ("industry", models.CharField(blank=True, max_length=100)),
                ("logo", models.ImageField(blank=True, null=True, upload_to="cases/logos/")),
                ("cover_image", models.ImageField(blank=True, null=True, upload_to="cases/covers/")),
                ("metric", models.CharField(blank=True, max_length=60)),
                ("metric_label", models.CharField(blank=True, max_length=120)),
                ("short_text", models.TextField(blank=True)),
                ("body", models.TextField(blank=True)),
                ("accent", models.CharField(
                    choices=[
                        ("emerald", "Зелёный"),
                        ("sky", "Голубой"),
                        ("amber", "Янтарный"),
                        ("rose", "Розовый"),
                        ("violet", "Фиолетовый"),
                        ("slate", "Серый"),
                    ],
                    default="emerald",
                    max_length=20,
                )),
                ("order", models.IntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "Кейс",
                "verbose_name_plural": "Кейсы",
                "ordering": ("order", "-published_at", "-created_at"),
            },
        ),
        migrations.AddIndex(
            model_name="case",
            index=models.Index(fields=["is_active", "order"], name="cases_active_order_idx"),
        ),
    ]
