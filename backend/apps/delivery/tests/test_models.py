"""DATA-10: DeliveryLog model tests."""
from __future__ import annotations

import pytest

from apps.accounts.models import ClientProfile
from apps.delivery.models import DeliveryLog
from apps.industries.models import Industry, QuestionnaireTemplate
from apps.reports.models import AuditReport
from apps.submissions.models import Submission


@pytest.mark.django_db
def test_delivery_log_model():
    ind = Industry.objects.create(name="Dlv Industry", code="dlv-ind")
    tpl = QuestionnaireTemplate.objects.create(industry=ind, version=1, is_active=True, name="DT1")
    client = ClientProfile.objects.create(telegram_id=99001, name="D Client", company="D Co")
    sub = Submission.objects.create(client=client, template=tpl)
    report = AuditReport.objects.create(submission=sub)
    log = DeliveryLog.objects.create(report=report, channel=DeliveryLog.Channel.TELEGRAM)
    assert log.status == DeliveryLog.Status.QUEUED
    assert log.channel == "telegram"


@pytest.mark.django_db
def test_delivery_log_multiple_channels():
    ind = Industry.objects.create(name="Dlv2 Industry", code="dlv-ind2")
    tpl = QuestionnaireTemplate.objects.create(industry=ind, version=1, is_active=True, name="DT2")
    client = ClientProfile.objects.create(telegram_id=99002, name="D2 Client", company="D2 Co")
    sub = Submission.objects.create(client=client, template=tpl)
    report = AuditReport.objects.create(submission=sub)
    tg_log = DeliveryLog.objects.create(report=report, channel=DeliveryLog.Channel.TELEGRAM)
    wa_log = DeliveryLog.objects.create(report=report, channel=DeliveryLog.Channel.WHATSAPP)
    assert report.deliveries.count() == 2
