from django.db import migrations, models
import django.db.models.deletion

import apps.accounts.models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_alter_clientprofile_telegram_id"),
    ]

    operations = [
        migrations.CreateModel(
            name="MagicLink",
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
                    "token",
                    models.CharField(
                        default=apps.accounts.models._gen_magic_token,
                        editable=False,
                        max_length=64,
                        unique=True,
                    ),
                ),
                (
                    "expires_at",
                    models.DateTimeField(
                        default=apps.accounts.models._default_magic_expires
                    ),
                ),
                ("used_at", models.DateTimeField(blank=True, null=True)),
                (
                    "requested_ip",
                    models.GenericIPAddressField(blank=True, null=True),
                ),
                (
                    "delivered_via",
                    models.CharField(
                        blank=True,
                        help_text="whatsapp / fallback / manual",
                        max_length=20,
                    ),
                ),
                (
                    "client",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="magic_links",
                        to="accounts.clientprofile",
                    ),
                ),
            ],
            options={
                "verbose_name": "Magic-ссылка",
                "verbose_name_plural": "Magic-ссылки",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(
                        fields=["token"], name="accounts_ma_token_38a25f_idx"
                    ),
                    models.Index(
                        fields=["client", "-created_at"],
                        name="accounts_ma_client__ee2ee2_idx",
                    ),
                ],
            },
        ),
    ]
