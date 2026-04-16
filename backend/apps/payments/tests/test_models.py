"""DATA-07, DATA-08: Tariff and Payment model tests."""
from __future__ import annotations

import pytest
from django.db import IntegrityError

from apps.accounts.models import ClientProfile
from apps.industries.models import Industry, QuestionnaireTemplate
from apps.payments.models import Payment, Tariff
from apps.submissions.models import Submission


@pytest.mark.django_db
def test_tariff_model():
    t = Tariff.objects.create(code="ashide_1", title="Ashide 1", price_kzt=45000, is_active=True)
    assert t.price_kzt == 45000
    assert str(t) == "Ashide 1 (45000 \u20b8)"


@pytest.mark.django_db
def test_payment_unique_transaction_id():
    ind = Industry.objects.create(name="Pay Industry", code="pay-ind1")
    tpl = QuestionnaireTemplate.objects.create(industry=ind, version=1, is_active=True, name="PT1")
    client = ClientProfile.objects.create(telegram_id=66666, name="PC", company="PCo")
    sub = Submission.objects.create(client=client, template=tpl)
    tariff = Tariff.objects.create(code="ashide_pay", title="Test", price_kzt=1000)

    Payment.objects.create(submission=sub, tariff=tariff, transaction_id="TX123", amount=1000)
    with pytest.raises(IntegrityError):
        Payment.objects.create(submission=sub, tariff=tariff, transaction_id="TX123", amount=1000)


@pytest.mark.django_db
def test_payment_raw_webhook_jsonfield():
    ind = Industry.objects.create(name="Pay Industry2", code="pay-ind2")
    tpl = QuestionnaireTemplate.objects.create(industry=ind, version=1, is_active=True, name="PT2")
    client = ClientProfile.objects.create(telegram_id=77777, name="PC2", company="PCo2")
    sub = Submission.objects.create(client=client, template=tpl)
    tariff = Tariff.objects.create(code="ashide_pay2", title="Test2", price_kzt=1000)
    payload = {"TransactionId": "TX999", "Status": "Completed", "Amount": 1000}

    p = Payment.objects.create(
        submission=sub, tariff=tariff, transaction_id="TX999", amount=1000, raw_webhook=payload
    )
    p.refresh_from_db()
    assert p.raw_webhook == payload
