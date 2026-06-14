from django.db import migrations

# Блоки, которые редактируются как форматированный HTML (CKEditor) и выводятся
# на фронте через <SafeHtml> в .prose. Остальные блоки — простые текстовые
# метки (заголовки, цены, ссылки) и остаются content_type='text'.
HTML_KEYS = ["method_text", "donation_message", "processing_message"]
FAQ_ANSWER_RE = r"^faq_\d+_a$"


def set_html(apps, schema_editor):
    ContentBlock = apps.get_model("content", "ContentBlock")
    ContentBlock.objects.filter(key__in=HTML_KEYS).update(content_type="html")
    ContentBlock.objects.filter(key__regex=FAQ_ANSWER_RE).update(content_type="html")


def revert(apps, schema_editor):
    ContentBlock = apps.get_model("content", "ContentBlock")
    ContentBlock.objects.filter(key__in=HTML_KEYS).update(content_type="text")
    ContentBlock.objects.filter(key__regex=FAQ_ANSWER_RE).update(content_type="text")


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(set_html, revert),
    ]
