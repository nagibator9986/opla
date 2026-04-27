from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="BlogCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=100)),
                ("slug", models.SlugField(blank=True, max_length=120, unique=True)),
                ("description", models.TextField(blank=True)),
                ("order", models.IntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "Категория блога",
                "verbose_name_plural": "Категории блога",
                "ordering": ("order", "name"),
            },
        ),
        migrations.CreateModel(
            name="BlogPost",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("slug", models.SlugField(blank=True, max_length=200, unique=True)),
                ("title", models.CharField(max_length=255)),
                ("excerpt", models.TextField(blank=True)),
                ("body", models.TextField(blank=True)),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("article", "Статья"),
                            ("glossary", "Глоссарий"),
                            ("philosophy", "Философия"),
                        ],
                        default="article",
                        max_length=20,
                    ),
                ),
                ("cover_image", models.ImageField(blank=True, null=True, upload_to="blog/covers/")),
                ("reading_time_min", models.PositiveIntegerField(default=5)),
                ("is_published", models.BooleanField(default=False)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("order", models.IntegerField(default=0)),
            ],
            options={
                "verbose_name": "Запись блога",
                "verbose_name_plural": "Записи блога",
                "ordering": ("order", "-published_at", "-created_at"),
            },
        ),
        migrations.AddIndex(
            model_name="blogpost",
            index=models.Index(fields=["is_published", "order"], name="blog_blogpost_pub_order"),
        ),
        migrations.AddIndex(
            model_name="blogpost",
            index=models.Index(fields=["category"], name="blog_blogpost_cat"),
        ),
    ]
