"""Tests for CloudPayments webhook endpoints and tariff list.

CloudPayments sends form-encoded payloads with a Content-HMAC header.
These tests verify HMAC validation, idempotency, FSM transitions, and
the public tariff list endpoint.
"""
import base64
import hashlib
import hmac

import pytest
from django.test import override_settings
from rest_framework.test import APIClient
from unittest.mock import patch

from apps.payments.models import Payment, Tariff
from apps.submissions.models import Submission

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TEST_SECRET = "test-secret"
CHECK_URL = "/api/v1/payments/cloudpayments/check/"
PAY_URL = "/api/v1/payments/cloudpayments/pay/"
TARIFFS_URL = "/api/v1/payments/tariffs/"


def _make_hmac(body: bytes, secret: str = TEST_SECRET) -> str:
    """Reproduce the CloudPayments HMAC-SHA256 signature."""
    return base64.b64encode(
        hmac.new(secret.encode(), body, hashlib.sha256).digest()
    ).decode()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def setup_submission(db):
    """Create a minimal but realistic submission in in_progress_basic state."""
    from tests.factories import (
        ClientProfileFactory,
        QuestionnaireTemplateFactory,
        TariffFactory,
    )

    tariff = TariffFactory(code="ashide_1", price_kzt=45000)
    profile = ClientProfileFactory()
    template = QuestionnaireTemplateFactory()
    sub = Submission.objects.create(
        client=profile,
        template=template,
        tariff=tariff,
    )
    # Advance to in_progress_basic so mark_paid() FSM transition is valid
    sub.start_onboarding()
    sub.save()
    return sub, tariff, profile


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCloudPaymentsWebhook:
    @override_settings(CLOUDPAYMENTS_API_SECRET=TEST_SECRET)
    def test_check_valid_returns_code_0(self, setup_submission):
        sub, tariff, _ = setup_submission
        body = f"InvoiceId={sub.id}&Amount=45000&Currency=KZT".encode()
        client = APIClient()
        response = client.post(
            CHECK_URL,
            body,
            content_type="application/x-www-form-urlencoded",
            HTTP_CONTENT_HMAC=_make_hmac(body),
        )
        assert response.status_code == 200
        assert response.data["code"] == 0

    @override_settings(CLOUDPAYMENTS_API_SECRET=TEST_SECRET)
    def test_check_invalid_hmac_returns_400(self, setup_submission):
        sub, _, _ = setup_submission
        body = f"InvoiceId={sub.id}&Amount=45000".encode()
        client = APIClient()
        response = client.post(
            CHECK_URL,
            body,
            content_type="application/x-www-form-urlencoded",
            HTTP_CONTENT_HMAC="invalid-hmac",
        )
        assert response.status_code == 400

    @override_settings(CLOUDPAYMENTS_API_SECRET=TEST_SECRET)
    @patch("apps.submissions.tasks.notify_bot_payment_success.delay")
    def test_pay_creates_payment_and_marks_paid(self, mock_notify, setup_submission):
        sub, tariff, _ = setup_submission
        body = f"TransactionId=TX001&InvoiceId={sub.id}&Amount=45000&Currency=KZT".encode()
        client = APIClient()
        response = client.post(
            PAY_URL,
            body,
            content_type="application/x-www-form-urlencoded",
            HTTP_CONTENT_HMAC=_make_hmac(body),
        )
        assert response.status_code == 200
        assert response.data["code"] == 0
        assert Payment.objects.filter(transaction_id="TX001").exists()
        sub.refresh_from_db()
        assert sub.status == Submission.Status.PAID
        mock_notify.assert_called_once_with(str(sub.id))

    @override_settings(CLOUDPAYMENTS_API_SECRET=TEST_SECRET)
    @patch("apps.submissions.tasks.notify_bot_payment_success.delay")
    def test_pay_idempotent_duplicate(self, mock_notify, setup_submission):
        sub, _, _ = setup_submission
        body = f"TransactionId=TX002&InvoiceId={sub.id}&Amount=45000&Currency=KZT".encode()
        hmac_val = _make_hmac(body)
        client = APIClient()
        # First call — should process normally
        r1 = client.post(
            PAY_URL,
            body,
            content_type="application/x-www-form-urlencoded",
            HTTP_CONTENT_HMAC=hmac_val,
        )
        assert r1.data["code"] == 0
        # Second call — duplicate, should be silently accepted
        response = client.post(
            PAY_URL,
            body,
            content_type="application/x-www-form-urlencoded",
            HTTP_CONTENT_HMAC=hmac_val,
        )
        assert response.data["code"] == 0
        assert Payment.objects.filter(transaction_id="TX002").count() == 1

    def test_tariffs_list(self, db):
        Tariff.objects.create(code="t1", title="T1", price_kzt=1000, is_active=True)
        Tariff.objects.create(code="t2", title="T2", price_kzt=2000, is_active=False)
        client = APIClient()
        response = client.get(TARIFFS_URL)
        assert response.status_code == 200
        assert len(response.data["results"]) == 1
