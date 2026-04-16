"""Phase 1 Wave 0 stub — DATA-11 (ContentBlock)."""
from __future__ import annotations
import pytest

pytestmark = pytest.mark.xfail(strict=False, reason="Phase 1 Wave 0 stub")


@pytest.mark.django_db
def test_content_block_model():
    from apps.content.models import ContentBlock
    cb = ContentBlock.objects.create(key="landing.hero.title", value="<h1>Baqsy</h1>")
    assert cb.key == "landing.hero.title"
