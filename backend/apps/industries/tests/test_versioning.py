"""DATA-12: QuestionnaireTemplate versioning invariant tests."""
from __future__ import annotations

import pytest
from django.db import IntegrityError

from apps.industries.models import Industry, Question, QuestionnaireTemplate


@pytest.mark.django_db
def test_create_new_version_deactivates_old():
    industry = Industry.objects.create(name="Test", code="test-v")
    t1 = QuestionnaireTemplate.objects.create(industry=industry, version=1, is_active=True, name="T")
    Question.objects.create(template=t1, order=1, text="Q1", field_type="text", block="A")

    t2 = QuestionnaireTemplate.create_new_version(t1)

    t1.refresh_from_db()
    assert t1.is_active is False
    assert t2.is_active is True
    assert t2.version == 2
    assert t2.questions.count() == 1


@pytest.mark.django_db
def test_create_new_version_clones_all_questions():
    industry = Industry.objects.create(name="Clone Industry", code="clone-ind")
    t1 = QuestionnaireTemplate.objects.create(industry=industry, version=1, is_active=True, name="T")
    for i in range(3):
        Question.objects.create(template=t1, order=i + 1, text=f"Q{i+1}", field_type="text", block="A")

    t2 = QuestionnaireTemplate.create_new_version(t1)

    assert t2.questions.count() == 3


@pytest.mark.django_db
def test_only_one_active_per_industry_constraint():
    industry = Industry.objects.create(name="Test2", code="test2-v")
    QuestionnaireTemplate.objects.create(industry=industry, version=1, is_active=True, name="T1")
    with pytest.raises(IntegrityError):
        QuestionnaireTemplate.objects.create(industry=industry, version=2, is_active=True, name="T2")


@pytest.mark.django_db
def test_multiple_inactive_templates_allowed():
    industry = Industry.objects.create(name="Multi", code="multi-v")
    QuestionnaireTemplate.objects.create(industry=industry, version=1, is_active=False, name="T1")
    t2 = QuestionnaireTemplate.objects.create(industry=industry, version=2, is_active=False, name="T2")
    assert t2.pk is not None
