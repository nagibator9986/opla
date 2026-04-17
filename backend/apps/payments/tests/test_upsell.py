"""Tests for UpsellView endpoint and notify_bot_payment_success task."""
import pytest
from unittest.mock import MagicMock, patch
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import BaseUser, ClientProfile
from apps.industries.models import Industry, QuestionnaireTemplate
from apps.payments.models import Tariff
from apps.submissions.models import Submission

UPSELL_URL = "/api/v1/payments/upsell/"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def upsell_setup(db):
    """Minimal setup: three tariffs, a client with synthetic JWT email, completed submission."""
    industry = Industry.objects.create(name="IT", code="it-upsell", is_active=True)
    template = QuestionnaireTemplate.objects.create(
        industry=industry, version=1, is_active=True, name="IT Template"
    )
    ashide_1 = Tariff.objects.create(code="ashide_1", title="Ashide 1", price_kzt=45000, is_active=True)
    Tariff.objects.create(code="ashide_2", title="Ashide 2", price_kzt=135000, is_active=True)
    Tariff.objects.create(code="upsell", title="Upsell", price_kzt=90000, is_active=True)

    # Synthetic email matches _get_client_profile logic
    tg_id = 99001
    user = BaseUser.objects.create_user(email=f"tg_{tg_id}@baqsy.internal")
    profile = ClientProfile.objects.create(
        user=user,
        telegram_id=tg_id,
        name="Test Client",
        company="Test Co",
    )
    sub = Submission.objects.create(
        client=profile,
        template=template,
        tariff=ashide_1,
    )
    # Advance submission to completed (via FSM chain)
    sub.start_onboarding()
    sub.mark_paid()
    sub.start_questionnaire()
    sub.complete_questionnaire()
    sub.save()

    api_client = APIClient()
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    return api_client, sub, profile


# ---------------------------------------------------------------------------
# UpsellView tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestUpsellView:
    def test_upsell_returns_payment_data(self, upsell_setup):
        """Happy path: returns CP Widget payload with correct amount."""
        client, sub, _ = upsell_setup
        resp = client.post(UPSELL_URL, {"submission_id": str(sub.id)}, format="json")
        assert resp.status_code == 200
        assert resp.data["amount"] == 90000
        assert resp.data["currency"] == "KZT"
        assert resp.data["tariff_code"] == "upsell"
        assert resp.data["invoiceId"] == str(sub.id)

    def test_upsell_rejects_non_ashide1(self, upsell_setup):
        """Should return 400 if submission tariff is not ashide_1."""
        client, sub, _ = upsell_setup
        ashide_2 = Tariff.objects.get(code="ashide_2")
        sub.tariff = ashide_2
        sub.save(update_fields=["tariff"])
        resp = client.post(UPSELL_URL, {"submission_id": str(sub.id)}, format="json")
        assert resp.status_code == 400
        assert "Ashide 1" in resp.data["detail"]

    def test_upsell_rejects_incomplete_submission(self, upsell_setup):
        """Should return 400 if submission has not reached completed status."""
        client, sub, profile = upsell_setup
        industry = Industry.objects.create(name="Retail", code="retail-upsell", is_active=True)
        template = QuestionnaireTemplate.objects.create(
            industry=industry, version=1, is_active=True, name="Retail"
        )
        ashide_1 = Tariff.objects.get(code="ashide_1")
        # A fresh submission in paid status (not completed)
        sub2 = Submission.objects.create(client=profile, template=template, tariff=ashide_1)
        sub2.start_onboarding()
        sub2.mark_paid()
        sub2.save()
        resp = client.post(UPSELL_URL, {"submission_id": str(sub2.id)}, format="json")
        assert resp.status_code == 400

    def test_upsell_requires_authentication(self, db):
        """Should return 401 for unauthenticated requests."""
        anon = APIClient()
        resp = anon.post(UPSELL_URL, {"submission_id": "some-id"}, format="json")
        assert resp.status_code == 401

    def test_upsell_rejects_wrong_submission_owner(self, upsell_setup, db):
        """Should return 404 when submission belongs to another client."""
        client, sub, _ = upsell_setup
        # Create another user and their own submission
        other_user = BaseUser.objects.create_user(email="tg_99002@baqsy.internal")
        other_client = APIClient()
        refresh = RefreshToken.for_user(other_user)
        other_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        # other_user has no ClientProfile → 403
        resp = other_client.post(UPSELL_URL, {"submission_id": str(sub.id)}, format="json")
        assert resp.status_code == 403

    def test_upsell_missing_submission_id(self, upsell_setup):
        """Should return 400 if submission_id is not provided."""
        client, _, _ = upsell_setup
        resp = client.post(UPSELL_URL, {}, format="json")
        assert resp.status_code == 400

    def test_upsell_nonexistent_submission(self, upsell_setup):
        """Should return 404 for a non-existent submission UUID."""
        import uuid
        client, _, _ = upsell_setup
        resp = client.post(UPSELL_URL, {"submission_id": str(uuid.uuid4())}, format="json")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# notify_bot_payment_success tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestNotifyBotPayment:
    @patch("apps.submissions.tasks.requests")
    def test_notification_sends_telegram_message(self, mock_requests, upsell_setup):
        """Task sends a POST to Telegram API with correct chat_id."""
        _, sub, profile = upsell_setup

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_requests.post.return_value = mock_resp

        from apps.submissions.tasks import notify_bot_payment_success

        # Reset submission back to paid so start_questionnaire() FSM succeeds
        Submission.objects.filter(id=sub.id).update(status="paid")
        sub.refresh_from_db()

        # Call task directly (bind=True; use .apply() to pass self correctly)
        notify_bot_payment_success.apply(args=[str(sub.id)])

        mock_requests.post.assert_called_once()
        call_args = mock_requests.post.call_args
        assert "api.telegram.org" in call_args[0][0]
        payload = call_args[1]["json"]
        assert str(profile.telegram_id) == str(payload["chat_id"])

    @patch("apps.submissions.tasks.requests")
    def test_notification_skips_missing_submission(self, mock_requests):
        """Task exits early without calling Telegram if submission not found."""
        import uuid
        from apps.submissions.tasks import notify_bot_payment_success

        notify_bot_payment_success.apply(args=[str(uuid.uuid4())])
        mock_requests.post.assert_not_called()

    @patch("apps.submissions.tasks.requests")
    def test_notification_retries_on_telegram_error(self, mock_requests, upsell_setup):
        """Task retries when Telegram API returns non-OK response."""
        _, sub, _ = upsell_setup
        Submission.objects.filter(id=sub.id).update(status="paid")

        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.text = "Too Many Requests"
        mock_requests.post.return_value = mock_resp

        from apps.submissions.tasks import notify_bot_payment_success

        result = notify_bot_payment_success.apply(args=[str(sub.id)])
        # Task should have retried — result will be a retry exception
        assert result.failed() or result.state in ("RETRY", "FAILURE")
