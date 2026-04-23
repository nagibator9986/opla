"""Extend QuestionnaireTemplate + Question to support admin-built adaptive flows.

Adds:
* intro_text / completion_text on QuestionnaireTemplate
* stage / placeholder / condition_question / condition_values on Question
* Expands Question.FieldType to include LONGTEXT and URL
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("industries", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="questionnairetemplate",
            name="intro_text",
            field=models.TextField(
                blank=True,
                default=(
                    "Сейчас я задам вам {{total}} вопросов. Займёт около 20 минут. "
                    "Можно прерываться и возвращаться — прогресс сохраняется."
                ),
            ),
        ),
        migrations.AddField(
            model_name="questionnairetemplate",
            name="completion_text",
            field=models.TextField(
                blank=True,
                default=(
                    "Спасибо, {{name}}! Анкета завершена. Наш эксперт разберёт ответы "
                    "и пришлёт именной PDF-отчёт в WhatsApp в течение 3–5 рабочих дней."
                ),
            ),
        ),
        migrations.AddField(
            model_name="question",
            name="stage",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.AddField(
            model_name="question",
            name="placeholder",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="question",
            name="condition_question",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="dependent_questions",
                to="industries.question",
            ),
        ),
        migrations.AddField(
            model_name="question",
            name="condition_values",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AlterField(
            model_name="question",
            name="field_type",
            field=models.CharField(
                choices=[
                    ("text", "Текст (свободный ответ)"),
                    ("longtext", "Текст (длинный ответ)"),
                    ("number", "Число"),
                    ("choice", "Выбор одного (кнопки)"),
                    ("multichoice", "Множественный выбор (чек-боксы)"),
                    ("url", "Ссылка (URL)"),
                ],
                default="text",
                max_length=20,
            ),
        ),
    ]
