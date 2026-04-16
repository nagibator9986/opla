"""Phase 1 Wave 0 stub — DATA-05 (Submission), DATA-06 (Answer)."""
from __future__ import annotations
import pytest

pytestmark = pytest.mark.xfail(strict=False, reason="Phase 1 Wave 0 stub")


@pytest.mark.django_db
def test_submission_model():
    from apps.submissions.models import Submission, SubmissionStatus
    # Relies on factories that do not yet exist in Phase 1 Wave 0.
    assert SubmissionStatus.CREATED == "created"


@pytest.mark.django_db
def test_answer_model_jsonb():
    from apps.submissions.models import Answer
    # Answer.value is JSONB — shape depends on question.field_type.
    # Full test requires full fixture graph; stub asserts model exists.
    assert Answer._meta.get_field("value").get_internal_type() == "JSONField"
