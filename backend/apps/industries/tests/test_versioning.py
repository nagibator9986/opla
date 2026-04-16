"""Phase 1 Wave 0 stub — DATA-12 (template versioning invariant)."""
from __future__ import annotations
import pytest
from django.db import IntegrityError

pytestmark = pytest.mark.xfail(strict=False, reason="Phase 1 Wave 0 stub")


@pytest.mark.django_db
def test_create_new_version_deactivates_old():
    from apps.industries.models import Industry, QuestionnaireTemplate
    ind = Industry.objects.create(name="Услуги", slug="services")
    v1 = QuestionnaireTemplate.objects.create(industry=ind, version=1, is_active=True, name="v1")
    v2 = QuestionnaireTemplate.create_new_version(industry_id=ind.id, name="v2")
    v1.refresh_from_db()
    assert v1.is_active is False
    assert v2.version == 2


@pytest.mark.django_db
def test_only_one_active_per_industry_constraint():
    from apps.industries.models import Industry, QuestionnaireTemplate
    ind = Industry.objects.create(name="Производство", slug="mfg")
    QuestionnaireTemplate.objects.create(industry=ind, version=1, is_active=True, name="v1")
    with pytest.raises(IntegrityError):
        QuestionnaireTemplate.objects.create(industry=ind, version=2, is_active=True, name="v2-dup")
