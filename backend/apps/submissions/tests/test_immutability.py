"""Phase 1 Wave 0 stub — DATA-13 (Submission.template_id immutable)."""
from __future__ import annotations
import pytest
from django.core.exceptions import ValidationError

pytestmark = pytest.mark.xfail(strict=False, reason="Phase 1 Wave 0 stub")


@pytest.mark.django_db
def test_submission_template_id_cannot_change():
    from apps.accounts.models import ClientProfile
    from apps.industries.models import Industry, QuestionnaireTemplate
    from apps.submissions.models import Submission

    ind = Industry.objects.create(name="IT", slug="it-imm")
    tpl_v1 = QuestionnaireTemplate.objects.create(industry=ind, version=1, name="v1")
    tpl_v2 = QuestionnaireTemplate.objects.create(industry=ind, version=2, name="v2")
    client = ClientProfile.objects.create(
        telegram_id=42, name="A", company="B", phone_wa="+7", city="C", industry=ind,
    )
    sub = Submission.objects.create(client=client, template=tpl_v1)
    sub.template = tpl_v2
    with pytest.raises(ValidationError):
        sub.save()
