"""DATA-13: Submission.template_id immutability test."""
from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError

from apps.accounts.models import ClientProfile
from apps.industries.models import Industry, QuestionnaireTemplate
from apps.submissions.models import Submission


@pytest.mark.django_db
def test_submission_template_id_cannot_change():
    industry = Industry.objects.create(name="Retail", code="retail-imm")
    t1 = QuestionnaireTemplate.objects.create(industry=industry, version=1, is_active=True, name="R1")
    industry2 = Industry.objects.create(name="IT", code="it-imm")
    t2 = QuestionnaireTemplate.objects.create(industry=industry2, version=1, is_active=True, name="IT1")
    client = ClientProfile.objects.create(telegram_id=12345, name="Test", company="TestCo")
    sub = Submission.objects.create(client=client, template=t1)

    sub.template = t2
    with pytest.raises(ValidationError, match="Нельзя изменить шаблон"):
        sub.save()


@pytest.mark.django_db
def test_submission_same_template_save_ok():
    industry = Industry.objects.create(name="Same", code="same-tmpl")
    t1 = QuestionnaireTemplate.objects.create(industry=industry, version=1, is_active=True, name="S1")
    client = ClientProfile.objects.create(telegram_id=99999, name="C2", company="Co2")
    sub = Submission.objects.create(client=client, template=t1)
    sub.save()
    sub.refresh_from_db()
    assert sub.template_id == t1.pk
