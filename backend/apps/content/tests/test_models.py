"""DATA-11: ContentBlock model tests."""
from __future__ import annotations

import pytest

from apps.content.models import ContentBlock


@pytest.mark.django_db
def test_content_block_model():
    block = ContentBlock.objects.create(
        key="hero_title",
        title="Hero Title",
        content="Welcome to Baqsy",
        content_type=ContentBlock.ContentType.TEXT,
    )
    assert block.key == "hero_title"
    assert block.is_active is True


@pytest.mark.django_db
def test_content_block_key_unique():
    from django.db import IntegrityError
    ContentBlock.objects.create(key="unique-key", title="U1", content="c1")
    with pytest.raises(IntegrityError):
        ContentBlock.objects.create(key="unique-key", title="U2", content="c2")
