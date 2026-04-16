"""Phase 1 Wave 0 stub — DATA-10 (DeliveryLog)."""
from __future__ import annotations
import pytest

pytestmark = pytest.mark.xfail(strict=False, reason="Phase 1 Wave 0 stub")


@pytest.mark.django_db
def test_delivery_log_model():
    from apps.delivery.models import DeliveryLog
    assert DeliveryLog._meta.get_field("channel") is not None
    assert DeliveryLog._meta.get_field("status") is not None
