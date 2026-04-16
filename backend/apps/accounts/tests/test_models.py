"""DATA-04: ClientProfile and BaseUser model tests."""
from __future__ import annotations

import pytest

from apps.accounts.models import BaseUser, ClientProfile
from apps.industries.models import Industry


@pytest.mark.django_db
def test_client_profile_model():
    ind = Industry.objects.create(name="Retail CP", code="retail-cp")
    cp = ClientProfile.objects.create(
        telegram_id=123456789,
        name="Иван",
        company="ООО Ромашка",
        phone_wa="+77001234567",
        city="Алматы",
        industry=ind,
    )
    assert cp.telegram_id == 123456789
    assert cp.name == "Иван"
    assert str(cp) == "Иван (ООО Ромашка)"


@pytest.mark.django_db
def test_client_profile_telegram_id_unique():
    from django.db import IntegrityError

    ClientProfile.objects.create(telegram_id=777777, name="A", company="X")
    with pytest.raises(IntegrityError):
        ClientProfile.objects.create(telegram_id=777777, name="B", company="Y")


@pytest.mark.django_db
def test_base_user_email_login():
    u = BaseUser.objects.create_user(email="admin@baqsy.kz", password="s3cret")
    assert u.email == "admin@baqsy.kz"
    assert u.check_password("s3cret")


@pytest.mark.django_db
def test_base_user_email_unique():
    from django.db import IntegrityError

    BaseUser.objects.create_user(email="unique@test.kz", password="pass1")
    with pytest.raises(IntegrityError):
        BaseUser.objects.create_user(email="unique@test.kz", password="pass2")
