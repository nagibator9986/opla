import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0003_alter_clientprofile_telegram_id"),
    ]

    operations = [
        migrations.CreateModel(
            name="AIAssistantConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(default="Baqsy AI", max_length=100)),
                ("model", models.CharField(default="gpt-4o-mini", max_length=60)),
                ("temperature", models.FloatField(default=0.5)),
                ("max_tokens", models.PositiveIntegerField(default=800)),
                ("system_prompt", models.TextField()),
                ("greeting", models.TextField()),
                ("quick_replies", models.JSONField(blank=True, default=list)),
                ("tariff_prompt", models.TextField(blank=True, default="")),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "Конфигурация AI-ассистента",
                "verbose_name_plural": "Конфигурация AI-ассистента",
            },
        ),
        migrations.CreateModel(
            name="ChatSession",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("collected_data", models.JSONField(blank=True, default=dict)),
                ("status", models.CharField(
                    choices=[
                        ("active", "Идёт диалог"),
                        ("qualified", "Готов к оплате"),
                        ("paid", "Оплачено"),
                        ("abandoned", "Заброшен"),
                    ],
                    default="active",
                    max_length=20,
                )),
                ("last_user_agent", models.CharField(blank=True, max_length=255)),
                ("last_ip", models.GenericIPAddressField(blank=True, null=True)),
                ("client", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="chat_sessions",
                    to="accounts.clientprofile",
                )),
            ],
            options={
                "verbose_name": "Чат-сессия",
                "verbose_name_plural": "Чат-сессии",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ChatMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("role", models.CharField(
                    choices=[
                        ("user", "Пользователь"),
                        ("assistant", "Ассистент"),
                        ("system", "Система"),
                    ],
                    max_length=16,
                )),
                ("content", models.TextField()),
                ("tokens_used", models.PositiveIntegerField(blank=True, null=True)),
                ("session", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="messages",
                    to="ai.chatsession",
                )),
            ],
            options={
                "verbose_name": "Сообщение чата",
                "verbose_name_plural": "Сообщения чата",
                "ordering": ["created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="chatsession",
            index=models.Index(fields=["status", "-created_at"], name="ai_chatsess_status_idx"),
        ),
        migrations.AddIndex(
            model_name="chatsession",
            index=models.Index(fields=["client"], name="ai_chatsess_client_idx"),
        ),
        migrations.AddIndex(
            model_name="chatmessage",
            index=models.Index(fields=["session", "created_at"], name="ai_chatmsg_session_idx"),
        ),
    ]
