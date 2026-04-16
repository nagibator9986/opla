"""DATA-09: AuditReport model tests."""
from __future__ import annotations

import pytest

from apps.accounts.models import ClientProfile
from apps.industries.models import Industry, QuestionnaireTemplate
from apps.reports.models import AuditReport
from apps.submissions.models import Submission


@pytest.mark.django_db
def test_audit_report_model():
    ind = Industry.objects.create(name="Report Industry", code="rpt-ind")
    tpl = QuestionnaireTemplate.objects.create(industry=ind, version=1, is_active=True, name="RT1")
    client = ClientProfile.objects.create(telegram_id=88888, name="R Client", company="R Co")
    sub = Submission.objects.create(client=client, template=tpl)
    report = AuditReport.objects.create(submission=sub, admin_text="Audit findings here")
    assert report.status == AuditReport.Status.DRAFT
    assert report.submission_id == sub.pk


@pytest.mark.django_db
def test_audit_report_one_to_one():
    from django.db import IntegrityError
    ind = Industry.objects.create(name="RPT2 Industry", code="rpt-ind2")
    tpl = QuestionnaireTemplate.objects.create(industry=ind, version=1, is_active=True, name="RT2")
    client = ClientProfile.objects.create(telegram_id=88889, name="R2 Client", company="R2 Co")
    sub = Submission.objects.create(client=client, template=tpl)
    AuditReport.objects.create(submission=sub)
    with pytest.raises(IntegrityError):
        AuditReport.objects.create(submission=sub)
