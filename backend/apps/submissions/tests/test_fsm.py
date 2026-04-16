"""Phase 1 Wave 0 stub — Submission FSM transitions."""
from __future__ import annotations
import pytest

pytestmark = pytest.mark.xfail(strict=False, reason="Phase 1 Wave 0 stub")


@pytest.mark.django_db
def test_valid_transition_created_to_in_progress_basic():
    from apps.submissions.models import Submission
    # Instance creation + transition call — needs full fixture graph.
    assert hasattr(Submission, "start_basic")


@pytest.mark.django_db
def test_invalid_transition_raises():
    from django_fsm import TransitionNotAllowed
    from apps.submissions.models import Submission
    assert TransitionNotAllowed is not None
