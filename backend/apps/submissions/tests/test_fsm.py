"""DATA-05: Submission FSM transition tests."""
from __future__ import annotations

import pytest
from django_fsm import TransitionNotAllowed

from apps.accounts.models import ClientProfile
from apps.industries.models import Industry, QuestionnaireTemplate
from apps.submissions.models import Submission


def make_submission(tg_id=55555):
    ind = Industry.objects.create(name=f"FSM Industry {tg_id}", code=f"fsm-{tg_id}")
    tpl = QuestionnaireTemplate.objects.create(industry=ind, version=1, is_active=True, name="FSM T")
    client = ClientProfile.objects.create(telegram_id=tg_id, name="FSM Client", company="FSM Co")
    return Submission.objects.create(client=client, template=tpl)


@pytest.mark.django_db
def test_valid_transition_created_to_in_progress_basic():
    sub = make_submission(55001)
    assert sub.status == Submission.Status.CREATED
    sub.start_onboarding()
    sub.save()
    assert sub.status == Submission.Status.IN_PROGRESS_BASIC


@pytest.mark.django_db
def test_full_happy_path_transitions():
    sub = make_submission(55002)
    sub.start_onboarding()
    sub.save()
    sub.mark_paid()
    sub.save()
    sub.start_questionnaire()
    sub.save()
    sub.complete_questionnaire()
    sub.save()
    assert sub.completed_at is not None
    sub.start_audit()
    sub.save()
    sub.mark_delivered()
    sub.save()
    assert sub.status == Submission.Status.DELIVERED


@pytest.mark.django_db
def test_invalid_transition_raises():
    sub = make_submission(55003)
    with pytest.raises(TransitionNotAllowed):
        sub.mark_paid()
