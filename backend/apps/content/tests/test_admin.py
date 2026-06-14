import pytest
from django.forms import Textarea

from django_ckeditor_5.widgets import CKEditor5Widget

from apps.content.admin import ContentBlockForm
from apps.content.models import ContentBlock


class TestContentBlockAdmin:
    def test_html_block_uses_ckeditor(self):
        """CRM-09: HTML-блок (длинный текст) редактируется через CKEditor 5."""
        block = ContentBlock(
            key="probe_html", title="x", content_type=ContentBlock.ContentType.HTML
        )
        form = ContentBlockForm(instance=block)
        assert isinstance(form.fields["content"].widget, CKEditor5Widget)

    def test_text_block_uses_plain_textarea(self):
        """Текстовая метка (заголовок/цена/ссылка) — простая textarea, без
        CKEditor: иначе редактор обернёт короткий текст в <p> и инлайн-вывод
        на фронте покажет литеральные теги."""
        block = ContentBlock(
            key="probe_text", title="x", content_type=ContentBlock.ContentType.TEXT
        )
        form = ContentBlockForm(instance=block)
        assert isinstance(form.fields["content"].widget, Textarea)
        assert not isinstance(form.fields["content"].widget, CKEditor5Widget)

    @pytest.mark.django_db
    def test_html_content_is_sanitized(self):
        """clean_content вырезает скрипты/опасные атрибуты в HTML-блоке."""
        form = ContentBlockForm(
            data={
                "key": "probe_sanitize",
                "title": "x",
                "content_type": ContentBlock.ContentType.HTML,
                "content": "<p><strong>ok</strong></p><script>alert(1)</script>",
                "is_active": "on",
            }
        )
        assert form.is_valid(), form.errors
        cleaned = form.cleaned_data["content"]
        assert "<strong>ok</strong>" in cleaned
        assert "<script>" not in cleaned

    @pytest.mark.django_db
    def test_text_content_is_not_mangled(self):
        """Текстовый блок не пропускается через nh3 — «5 < 10» остаётся как есть."""
        form = ContentBlockForm(
            data={
                "key": "probe_plain",
                "title": "x",
                "content_type": ContentBlock.ContentType.TEXT,
                "content": "5 < 10 и 20 > 3",
                "is_active": "on",
            }
        )
        assert form.is_valid(), form.errors
        assert form.cleaned_data["content"] == "5 < 10 и 20 > 3"
