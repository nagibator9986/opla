"""Tests for ApproveReportView API endpoint."""
from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.reports.models import AuditReport
from apps.submissions.models import Submission
from tests.factories import (
    SubmissionFactory,
    TariffFactory,
    UserFactory,
)


# ─── Ensure stub modules so imports don't fail on dev machines ────────────

def _ensure_stub_modules():
    if "weasyprint" not in sys.modules:
        fake_wp = ModuleType("weasyprint")
        fake_wp.HTML = MagicMock()
        sys.modules["weasyprint"] = fake_wp
    if "boto3" not in sys.modules:
        fake_boto3 = ModuleType("boto3")
        fake_boto3.client = MagicMock()
        sys.modules["boto3"] = fake_boto3


_ensure_stub_modules()


# ─── Helpers ────────────────────────────────────────────────────────────────

def _make_submission_completed():
    """Create a Submission that has reached COMPLETED status."""
    sub = SubmissionFactory(tariff=TariffFactory(code="ashide_1"))
    # Advance FSM: CREATED → IN_PROGRESS_BASIC → PAID → IN_PROGRESS_FULL → COMPLETED
    sub.start_onboarding()
    sub.save()
    sub.mark_paid()
    sub.save()
    sub.start_questionnaire()
    sub.save()
    sub.complete_questionnaire()
    sub.save()
    return sub


def _make_report(submission=None, admin_text="Аудит выполнен."):
    if submission is None:
        submission = _make_submission_completed()
    return AuditReport.objects.create(submission=submission, admin_text=admin_text)


def _approve_url(report_id: int) -> str:
    return f"/api/v1/reports/{report_id}/approve/"


# ─── Tests ──────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_approve_report_requires_admin():
    """Non-staff user gets 403 Forbidden."""
    report = _make_report()
    regular_user = UserFactory(is_staff=False)

    client = APIClient()
    client.force_authenticate(user=regular_user)

    resp = client.post(_approve_url(report.id))
    assert resp.status_code == 403


@pytest.mark.django_db
def test_approve_report_requires_auth():
    """Unauthenticated request gets 401."""
    report = _make_report()
    client = APIClient()
    resp = client.post(_approve_url(report.id))
    assert resp.status_code == 401


@pytest.mark.django_db
def test_approve_report_empty_admin_text():
    """Report without admin_text returns 400."""
    sub = _make_submission_completed()
    report = AuditReport.objects.create(submission=sub, admin_text="")

    admin_user = UserFactory(is_staff=True)
    client = APIClient()
    client.force_authenticate(user=admin_user)

    resp = client.post(_approve_url(report.id))
    assert resp.status_code == 400
    assert "admin_text" in resp.json().get("error", "")


@pytest.mark.django_db
def test_approve_report_starts_pipeline():
    """Staff user with valid report gets 200 and Celery chain is queued."""
    report = _make_report()

    admin_user = UserFactory(is_staff=True)
    client = APIClient()
    client.force_authenticate(user=admin_user)

    mock_chain = MagicMock()
    mock_workflow = MagicMock()
    mock_chain.return_value = mock_workflow

    with patch("celery.chain", mock_chain), \
         patch("celery.group", MagicMock(return_value=MagicMock())):
        resp = client.post(_approve_url(report.id))

    assert resp.status_code == 200
    assert resp.json() == {"status": "queued"}
    mock_workflow.delay.assert_called_once()


@pytest.mark.django_db
def test_approve_report_transitions_fsm():
    """Submission transitions from completed → under_audit on approval."""
    sub = _make_submission_completed()
    assert sub.status == Submission.Status.COMPLETED

    report = AuditReport.objects.create(submission=sub, admin_text="Аудит готов")

    admin_user = UserFactory(is_staff=True)
    client = APIClient()
    client.force_authenticate(user=admin_user)

    with patch("celery.chain") as mock_chain, \
         patch("celery.group"):
        mock_chain.return_value.delay = MagicMock()
        client.post(_approve_url(report.id))

    sub.refresh_from_db()
    assert sub.status == Submission.Status.UNDER_AUDIT


@pytest.mark.django_db
def test_approve_report_idempotent_fsm():
    """Repeat approve on under_audit submission does not raise FSM error."""
    sub = _make_submission_completed()
    sub.start_audit()
    sub.save()
    assert sub.status == Submission.Status.UNDER_AUDIT

    report = AuditReport.objects.create(submission=sub, admin_text="Аудит завершён")

    admin_user = UserFactory(is_staff=True)
    client = APIClient()
    client.force_authenticate(user=admin_user)

    with patch("celery.chain") as mock_chain, \
         patch("celery.group"):
        mock_chain.return_value.delay = MagicMock()
        resp = client.post(_approve_url(report.id))

    assert resp.status_code == 200
    sub.refresh_from_db()
    assert sub.status == Submission.Status.UNDER_AUDIT  # unchanged, no crash


@pytest.mark.django_db
def test_approve_report_not_found():
    """Non-existent report_id returns 404."""
    admin_user = UserFactory(is_staff=True)
    client = APIClient()
    client.force_authenticate(user=admin_user)

    resp = client.post("/api/v1/reports/99999/approve/")
    assert resp.status_code == 404
