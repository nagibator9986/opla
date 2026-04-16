"""DATA-01, DATA-02, DATA-03: Industry, QuestionnaireTemplate, Question model tests."""
from __future__ import annotations

import pytest

from apps.industries.models import Industry, Question, QuestionnaireTemplate


@pytest.mark.django_db
def test_industry_model():
    obj = Industry.objects.create(name="Retail", code="retail-m", is_active=True)
    assert obj.pk is not None
    assert obj.name == "Retail"
    assert obj.code == "retail-m"


@pytest.mark.django_db
def test_industry_code_unique():
    from django.db import IntegrityError
    Industry.objects.create(name="IT", code="it-unique")
    with pytest.raises(IntegrityError):
        Industry.objects.create(name="IT2", code="it-unique")


@pytest.mark.django_db
def test_questionnaire_template_model():
    ind = Industry.objects.create(name="IT Tpl", code="it-tpl")
    tpl = QuestionnaireTemplate.objects.create(industry=ind, version=1, name="IT v1", is_active=True)
    assert tpl.version == 1
    assert tpl.is_active is True


@pytest.mark.django_db
def test_question_model():
    ind = Industry.objects.create(name="FnB", code="fnb-q")
    tpl = QuestionnaireTemplate.objects.create(industry=ind, version=1, name="FnB v1")
    q = Question.objects.create(
        template=tpl, order=1, text="Your revenue?",
        field_type=Question.FieldType.NUMBER, required=True, block=Question.Block.A,
    )
    assert q.order == 1
    assert q.field_type == "number"


@pytest.mark.django_db
def test_question_options_jsonfield():
    ind = Industry.objects.create(name="Services", code="svc-q")
    tpl = QuestionnaireTemplate.objects.create(industry=ind, version=1, name="Svc v1")
    q = Question.objects.create(
        template=tpl, order=1, text="Choose one",
        field_type=Question.FieldType.CHOICE, options={"choices": ["a", "b", "c"]}, block=Question.Block.B,
    )
    assert q.options == {"choices": ["a", "b", "c"]}
