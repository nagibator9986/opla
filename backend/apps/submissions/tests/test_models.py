"""DATA-05, DATA-06: Submission and Answer model tests."""
from __future__ import annotations

import pytest

from apps.accounts.models import ClientProfile
from apps.industries.models import Industry, Question, QuestionnaireTemplate
from apps.submissions.models import Answer, Submission


@pytest.mark.django_db
def test_submission_model_creation():
    ind = Industry.objects.create(name="Sub Industry", code="sub-ind1")
    tpl = QuestionnaireTemplate.objects.create(industry=ind, version=1, is_active=True, name="T1")
    client = ClientProfile.objects.create(telegram_id=11111, name="Test", company="TestCo")
    sub = Submission.objects.create(client=client, template=tpl)
    assert sub.pk is not None
    assert sub.status == Submission.Status.CREATED


@pytest.mark.django_db
def test_submission_has_uuid_pk():
    import uuid
    ind = Industry.objects.create(name="UUID Industry", code="uuid-ind")
    tpl = QuestionnaireTemplate.objects.create(industry=ind, version=1, is_active=True, name="T2")
    client = ClientProfile.objects.create(telegram_id=22222, name="Test", company="TestCo")
    sub = Submission.objects.create(client=client, template=tpl)
    assert isinstance(sub.pk, uuid.UUID)


@pytest.mark.django_db
def test_answer_model_jsonb():
    ind = Industry.objects.create(name="Ans Industry", code="ans-ind1")
    tpl = QuestionnaireTemplate.objects.create(industry=ind, version=1, is_active=True, name="T3")
    client = ClientProfile.objects.create(telegram_id=33333, name="Test", company="TestCo")
    sub = Submission.objects.create(client=client, template=tpl)
    question = Question.objects.create(
        template=tpl, order=1, text="Q?", field_type=Question.FieldType.TEXT, block=Question.Block.A
    )
    answer = Answer.objects.create(submission=sub, question=question, value={"text": "My answer"})
    assert answer.value == {"text": "My answer"}
    assert Answer._meta.get_field("value").get_internal_type() == "JSONField"


@pytest.mark.django_db
def test_answer_unique_per_submission_question():
    from django.db import IntegrityError
    ind = Industry.objects.create(name="Ans Industry2", code="ans-ind2")
    tpl = QuestionnaireTemplate.objects.create(industry=ind, version=1, is_active=True, name="T4")
    client = ClientProfile.objects.create(telegram_id=44444, name="Test", company="TestCo")
    sub = Submission.objects.create(client=client, template=tpl)
    question = Question.objects.create(
        template=tpl, order=1, text="Q?", field_type=Question.FieldType.NUMBER, block=Question.Block.A
    )
    Answer.objects.create(submission=sub, question=question, value={"number": 42})
    with pytest.raises(IntegrityError):
        Answer.objects.create(submission=sub, question=question, value={"number": 99})
