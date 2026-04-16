"""Phase 1 Wave 0 stub — INFRA-03 (.env-driven config)."""
from __future__ import annotations
import pytest

pytestmark = pytest.mark.xfail(strict=False, reason="Phase 1 Wave 0 stub")


def test_env_vars_loaded():
    from django.conf import settings
    assert settings.DATABASES["default"]["ENGINE"].endswith("postgresql")
    assert "redis" in settings.CELERY_BROKER_URL
