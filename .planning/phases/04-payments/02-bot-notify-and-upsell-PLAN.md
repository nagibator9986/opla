---
phase: 04-payments
plan: 02
type: execute
wave: 2
title: "Bot payment notification + upsell endpoint"
depends_on: [01]
requirements: [PAY-06, PAY-07, PAY-08]
autonomous: true
files_modified:
  - backend/apps/submissions/tasks.py
  - backend/apps/payments/views.py
  - backend/apps/payments/urls.py
  - backend/apps/payments/tests/test_upsell.py
nyquist_compliant: true
---

# Plan 02: Bot Notification + Upsell

## Goal

Implement the Celery task that notifies bot users of successful payment (sends Telegram message with questionnaire deep-link), and the upsell endpoint for upgrading from Ashide 1 to Ashide 2.

## must_haves

- `notify_bot_payment_success` Celery task sends Telegram message with questionnaire deep-link
- Task retries on Telegram API failure (max 3, exp backoff)
- `POST /api/v1/payments/upsell/` upgrades tariff without re-questionnaire
- Upsell validates: submission belongs to client, current tariff is ashide_1, status ≥ completed
- Kaspi Pay note: works through same CP Widget (PAY-07 = config-level, not code)

## Tasks

<task id="02-01">
<title>Implement notify_bot_payment_success Celery task</title>
<read_first>
- backend/apps/submissions/tasks.py (existing remind task — pattern to follow)
- backend/apps/submissions/models.py (Submission FSM start_questionnaire)
- .planning/phases/04-payments/04-CONTEXT.md (notification flow)
</read_first>
<action>
Add to `backend/apps/submissions/tasks.py`:

```python
@shared_task(name="submissions.notify_bot_payment_success", bind=True, max_retries=3)
def notify_bot_payment_success(self, submission_id):
    """Notify bot user that payment succeeded — send questionnaire deep-link."""
    from apps.submissions.models import Submission

    try:
        sub = Submission.objects.select_related("client").get(id=submission_id)
    except Submission.DoesNotExist:
        log.error("Submission %s not found for payment notification", submission_id)
        return

    telegram_id = sub.client.telegram_id
    deeplink = f"https://t.me/{BOT_NAME}?start=questionnaire_{sub.id}"

    # FSM: paid → in_progress_full
    try:
        sub.start_questionnaire()
        sub.save()
    except Exception as e:
        log.warning("FSM transition start_questionnaire failed for %s: %s", sub.id, e)
        # May already be transitioned — continue with notification

    text = (
        "Оплата прошла успешно! ✅\n\n"
        "Теперь давайте заполним анкету для вашего бизнес-аудита.\n"
        "Нажмите кнопку ниже, чтобы начать."
    )

    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": telegram_id,
                "text": text,
                "reply_markup": {
                    "inline_keyboard": [[{
                        "text": "Начать анкету",
                        "url": deeplink,
                    }]]
                },
            },
            timeout=10,
        )
        if not resp.ok:
            log.warning("Telegram API error: %s", resp.text)
            raise Exception(f"Telegram API {resp.status_code}")
        log.info("Payment notification sent to tg_id=%s sub=%s", telegram_id, sub.id)
    except Exception as exc:
        log.error("Failed to notify tg_id=%s: %s", telegram_id, exc)
        self.retry(exc=exc, countdown=2 ** self.request.retries * 10)
```
</action>
<acceptance_criteria>
- `backend/apps/submissions/tasks.py` contains `def notify_bot_payment_success(self, submission_id):`
- `backend/apps/submissions/tasks.py` contains `sub.start_questionnaire()`
- `backend/apps/submissions/tasks.py` contains `api.telegram.org/bot`
- `backend/apps/submissions/tasks.py` contains `self.retry(exc=exc`
</acceptance_criteria>
</task>

<task id="02-02">
<title>Create upsell endpoint</title>
<read_first>
- backend/apps/payments/views.py
- backend/apps/payments/models.py (Tariff)
- backend/apps/submissions/models.py (Submission)
- .planning/phases/04-payments/04-CONTEXT.md (upsell logic)
</read_first>
<action>
Add to `backend/apps/payments/views.py`:

```python
from rest_framework.permissions import IsAuthenticated

class UpsellView(APIView):
    """POST /api/v1/payments/upsell/ — initiate upsell from Ashide 1 to Ashide 2."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        submission_id = request.data.get("submission_id")
        if not submission_id:
            return Response({"detail": "submission_id required"}, status=400)

        # Get client profile from JWT
        from apps.submissions.views import _get_client_profile
        client = _get_client_profile(request.user)
        if not client:
            return Response({"detail": "Client not found"}, status=403)

        try:
            sub = Submission.objects.get(id=submission_id, client=client)
        except Submission.DoesNotExist:
            return Response({"detail": "Submission not found"}, status=404)

        # Validate current tariff is ashide_1
        if not sub.tariff or sub.tariff.code != "ashide_1":
            return Response({"detail": "Upsell available only for Ashide 1"}, status=400)

        # Validate status (must be at least completed)
        if sub.status not in ("completed", "under_audit", "delivered"):
            return Response({"detail": "Submission not yet completed"}, status=400)

        # Get upsell tariff
        try:
            upsell_tariff = Tariff.objects.get(code="upsell", is_active=True)
        except Tariff.DoesNotExist:
            return Response({"detail": "Upsell tariff not configured"}, status=500)

        # Return data for CloudPayments Widget
        from django.conf import settings
        return Response({
            "publicId": settings.CLOUDPAYMENTS_PUBLIC_ID,
            "amount": int(upsell_tariff.price_kzt),
            "currency": "KZT",
            "invoiceId": str(sub.id),
            "description": f"Upsell Ashide 1→2: {client.company}",
            "accountId": str(client.id),
            "tariff_code": "upsell",
        })
```

Add to `backend/apps/payments/urls.py`:
```python
from apps.payments.views import UpsellView
# Add to urlpatterns:
path("upsell/", UpsellView.as_view(), name="payment-upsell"),
```

Update the Pay webhook to handle upsell payments — when tariff is "upsell", update `submission.tariff` to ashide_2:
Add to `CloudPaymentsPayView.post()` after saving payment, before notification:
```python
# Handle upsell: upgrade tariff
if payment.tariff and payment.tariff.code == "upsell":
    ashide_2 = Tariff.objects.filter(code="ashide_2", is_active=True).first()
    if ashide_2:
        sub.tariff = ashide_2
        sub.save(update_fields=["tariff"])
        log.info("Upsell: submission %s upgraded to Ashide 2", sub.id)
```
</action>
<acceptance_criteria>
- `backend/apps/payments/views.py` contains `class UpsellView(APIView):`
- `backend/apps/payments/views.py` contains `tariff.code != "ashide_1"`
- `backend/apps/payments/views.py` contains `upsell_tariff = Tariff.objects.get(code="upsell"`
- `backend/apps/payments/urls.py` contains `path("upsell/"`
- `backend/apps/payments/views.py` contains `payment.tariff.code == "upsell"`
</acceptance_criteria>
</task>

<task id="02-03">
<title>Write upsell and notification tests</title>
<read_first>
- backend/apps/payments/views.py (UpsellView)
- backend/apps/submissions/tasks.py (notify_bot_payment_success)
</read_first>
<action>
Create `backend/apps/payments/tests/test_upsell.py`:

```python
import pytest
from unittest.mock import patch
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import BaseUser, ClientProfile
from apps.industries.models import Industry, QuestionnaireTemplate
from apps.payments.models import Tariff
from apps.submissions.models import Submission


@pytest.fixture
def upsell_setup(db):
    industry = Industry.objects.create(name="IT", code="it", is_active=True)
    template = QuestionnaireTemplate.objects.create(industry=industry, version=1, is_active=True, name="IT")
    ashide_1 = Tariff.objects.create(code="ashide_1", title="A1", price_kzt=45000, is_active=True)
    ashide_2 = Tariff.objects.create(code="ashide_2", title="A2", price_kzt=135000, is_active=True)
    upsell = Tariff.objects.create(code="upsell", title="Upsell", price_kzt=90000, is_active=True)
    profile = ClientProfile.objects.create(telegram_id=12345, name="Test", company="Co")
    user = BaseUser.objects.create_user(email="tg_12345@baqsy.internal")
    sub = Submission.objects.create(client=profile, template=template, tariff=ashide_1, status="completed")
    
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client, sub, profile


@pytest.mark.django_db
class TestUpsell:
    def test_upsell_returns_payment_data(self, upsell_setup):
        client, sub, _ = upsell_setup
        resp = client.post("/api/v1/payments/upsell/", {"submission_id": str(sub.id)}, format="json")
        assert resp.status_code == 200
        assert resp.data["amount"] == 90000
        assert resp.data["currency"] == "KZT"

    def test_upsell_rejects_non_ashide1(self, upsell_setup):
        client, sub, _ = upsell_setup
        sub.tariff = Tariff.objects.get(code="ashide_2")
        sub.save(update_fields=["tariff"])
        resp = client.post("/api/v1/payments/upsell/", {"submission_id": str(sub.id)}, format="json")
        assert resp.status_code == 400

    def test_upsell_rejects_incomplete_submission(self, upsell_setup):
        client, sub, _ = upsell_setup
        sub.status = "in_progress_full"
        sub.save(update_fields=["status"])
        resp = client.post("/api/v1/payments/upsell/", {"submission_id": str(sub.id)}, format="json")
        assert resp.status_code == 400


@pytest.mark.django_db
class TestNotifyBotPayment:
    @patch("apps.submissions.tasks.requests")
    def test_notification_sends_telegram_message(self, mock_requests, upsell_setup):
        _, sub, profile = upsell_setup
        sub.status = "paid"
        sub.save(update_fields=["status"])
        
        mock_resp = mock_requests.post.return_value
        mock_resp.ok = True
        
        from apps.submissions.tasks import notify_bot_payment_success
        notify_bot_payment_success(str(sub.id))
        
        mock_requests.post.assert_called_once()
        call_args = mock_requests.post.call_args
        assert "api.telegram.org" in call_args[0][0]
        assert str(profile.telegram_id) == str(call_args[1]["json"]["chat_id"])
```
</action>
<acceptance_criteria>
- `backend/apps/payments/tests/test_upsell.py` contains `def test_upsell_returns_payment_data`
- `backend/apps/payments/tests/test_upsell.py` contains `def test_upsell_rejects_non_ashide1`
- `backend/apps/payments/tests/test_upsell.py` contains `def test_notification_sends_telegram_message`
- `pytest apps/payments/tests/ -x` exits 0
</acceptance_criteria>
</task>

## Verification

```bash
pytest apps/payments/tests/ apps/submissions/tests/ -x -q
```
