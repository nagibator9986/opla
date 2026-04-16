"""Phase 1 Wave 0 stub — DATA-01, DATA-02, DATA-03."""
from __future__ import annotations
import pytest

pytestmark = pytest.mark.xfail(strict=False, reason="Phase 1 Wave 0 stub")


@pytest.mark.django_db
def test_industry_model():
    from apps.industries.models import Industry
    obj = Industry.objects.create(name="Ритейл", slug="retail", is_active=True)
    assert obj.pk is not None
    assert obj.name == "Ритейл"


@pytest.mark.django_db
def test_questionnaire_template_model():
    from apps.industries.models import Industry, QuestionnaireTemplate
    ind = Industry.objects.create(name="IT", slug="it")
    tpl = QuestionnaireTemplate.objects.create(industry=ind, version=1, name="IT v1", is_active=True)
    assert tpl.version == 1
    assert tpl.is_active is True


@pytest.mark.django_db
def test_question_model():
    from apps.industries.models import Industry, QuestionnaireTemplate, Question
    ind = Industry.objects.create(name="F&B", slug="fnb")
    tpl = QuestionnaireTemplate.objects.create(industry=ind, version=1, name="F&B v1")
    q = Question.objects.create(
        template=tpl, order=1, text="Your revenue?",
        field_type=Question.FieldType.NUMBER, required=True, block=Question.Block.A,
    )
    assert q.order == 1
    assert q.field_type == "number"
