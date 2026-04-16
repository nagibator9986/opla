"""Phase 1 Wave 0 stub — DATA-07 (Tariff), DATA-08 (Payment)."""
from __future__ import annotations
import pytest
from django.db import IntegrityError

pytestmark = pytest.mark.xfail(strict=False, reason="Phase 1 Wave 0 stub")


@pytest.mark.django_db
def test_tariff_model():
    from apps.payments.models import Tariff
    t = Tariff.objects.create(code="ashide_1", title="Ashıde 1", price_kzt=45000, is_active=True)
    assert t.price_kzt == 45000


@pytest.mark.django_db
def test_payment_unique_transaction_id():
    from apps.payments.models import Payment
    # Requires Submission + Tariff fixtures. Stub asserts unique constraint exists.
    field = Payment._meta.get_field("transaction_id")
    assert field.unique is True
