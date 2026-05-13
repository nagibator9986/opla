from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SiteSettings",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "payments_enabled",
                    models.BooleanField(
                        default=False,
                        help_text=(
                            "Если ВЫКЛЮЧЕНО — клиенты получают доступ к анкете "
                            "и отчёту БЕЗ оплаты (для тестирования или промо-"
                            "периода). Если ВКЛЮЧЕНО — стандартный флоу: тариф "
                            "→ оплата через CloudPayments → анкета → отчёт."
                        ),
                        verbose_name="Платёжная система включена",
                    ),
                ),
                (
                    "free_mode_banner",
                    models.CharField(
                        blank=True,
                        default="Период открытого доступа · аудит бесплатно",
                        help_text="Показывается над тарифами когда платежи выключены.",
                        max_length=255,
                        verbose_name="Текст плашки в свободном режиме",
                    ),
                ),
            ],
            options={
                "verbose_name": "Настройки платформы",
                "verbose_name_plural": "Настройки платформы",
            },
        ),
    ]
