"""Phase 1 Wave 0 stub — DATA-04 (ClientProfile)."""
from __future__ import annotations
import pytest

pytestmark = pytest.mark.xfail(strict=False, reason="Phase 1 Wave 0 stub")


@pytest.mark.django_db
def test_client_profile_model():
    from apps.accounts.models import ClientProfile
    from apps.industries.models import Industry
    ind = Industry.objects.create(name="Ритейл", slug="retail-cp")
    cp = ClientProfile.objects.create(
        telegram_id=123456789, name="Иван", company="ООО Ромашка",
        phone_wa="+77001234567", city="Алматы", industry=ind,
    )
    assert cp.telegram_id == 123456789
    assert cp.name == "Иван"


@pytest.mark.django_db
def test_base_user_email_login():
    from apps.accounts.models import BaseUser
    u = BaseUser.objects.create_user(email="admin@baqsy.kz", password="s3cret")
    assert u.email == "admin@baqsy.kz"
    assert u.check_password("s3cret")
