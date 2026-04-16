"""Phase 1 Wave 0 stub — seed_initial management command."""
from __future__ import annotations
import pytest
from django.core.management import call_command

pytestmark = pytest.mark.xfail(strict=False, reason="Phase 1 Wave 0 stub")


@pytest.mark.django_db
def test_seed_initial_idempotent():
    call_command("seed_initial")
    call_command("seed_initial")  # second run must not raise


@pytest.mark.django_db
def test_seed_creates_baseline_data():
    from apps.industries.models import Industry
    from apps.payments.models import Tariff
    call_command("seed_initial")
    assert Industry.objects.count() >= 5
    assert Tariff.objects.filter(code="ashide_1").exists()
    assert Tariff.objects.filter(code="ashide_2").exists()
    assert Tariff.objects.filter(code="upsell").exists()
