import pytest
from django.db import models

from django_ckeditor_5.widgets import CKEditor5Widget

from apps.content.admin import ContentBlockAdmin


class TestContentBlockAdmin:
    def test_ckeditor_widget(self):
        """CRM-09: ContentBlockAdmin uses CKEditor5Widget for TextField."""
        overrides = ContentBlockAdmin.formfield_overrides
        assert models.TextField in overrides
        widget = overrides[models.TextField]["widget"]
        assert isinstance(widget, CKEditor5Widget)
