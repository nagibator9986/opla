---
phase: 04-payments
plan: 01
type: execute
wave: 1
title: "CloudPayments webhook endpoints with HMAC validation"
depends_on: []
requirements: [PAY-02, PAY-03, PAY-04, PAY-05, PAY-09]
autonomous: true
files_modified:
  - backend/apps/payments/services.py
  - backend/apps/payments/views.py
  - backend/apps/payments/serializers.py
  - backend/apps/payments/urls.py
  - backend/apps/core/api_urls.py
  - backend/apps/payments/tests/test_webhook.py
nyquist_compliant: true
---

# Plan 01: CloudPayments Webhook + HMAC

## Goal

Create Check and Pay webhook endpoints with HMAC-SHA256 validation, idempotent payment processing via get_or_create + select_for_update, FSM transition to `paid`, and public tariff list endpoint.

## must_haves

- Check webhook validates HMAC, checks submission exists, amount matches tariff
- Pay webhook validates HMAC, creates Payment idempotently, transitions Submission to paid
- Invalid HMAC returns 400
- Duplicate TransactionId returns `{"code": 0}` without side effects
- GET /api/v1/tariffs/ returns active tariffs
- All tested with realistic webhook payloads

## Tasks

<task id="01-01">
<title>Create HMAC validation service</title>
<read_first>
- .planning/phases/04-payments/04-CONTEXT.md (HMAC decisions)
- .planning/research/ARCHITECTURE.md (CloudPayments HMAC pattern)
- backend/baqsy/settings/base.py (CLOUDPAYMENTS_API_SECRET)
</read_first>
<action>
Create `backend/apps/payments/services.py`:

```python
import base64
import hashlib
import hmac
import logging
from django.conf import settings

log = logging.getLogger(__name__)


def validate_hmac(body: bytes, received_hmac: str) -> bool:
    """Validate CloudPayments webhook HMAC-SHA256 signature."""
    secret = settings.CLOUDPAYMENTS_API_SECRET.encode("utf-8")
    expected = base64.b64encode(
        hmac.new(secret, body, hashlib.sha256).digest()
    ).decode("utf-8")
    return hmac.compare_digest(expected, received_hmac)
```

Add to `backend/baqsy/settings/base.py`:
```python
CLOUDPAYMENTS_PUBLIC_ID = env("CLOUDPAYMENTS_PUBLIC_ID", default="")
CLOUDPAYMENTS_API_SECRET = env("CLOUDPAYMENTS_API_SECRET", default="")
```
</action>
<acceptance_criteria>
- `backend/apps/payments/services.py` contains `def validate_hmac(`
- `backend/apps/payments/services.py` contains `hmac.compare_digest(`
- `backend/apps/payments/services.py` contains `base64.b64encode`
- `backend/baqsy/settings/base.py` contains `CLOUDPAYMENTS_API_SECRET`
</acceptance_criteria>
</task>

<task id="01-02">
<title>Create Check and Pay webhook views + tariff list</title>
<read_first>
- backend/apps/payments/models.py (Payment, Tariff)
- backend/apps/submissions/models.py (Submission FSM mark_paid)
- backend/apps/payments/services.py (validate_hmac)
- .planning/phases/04-payments/04-CONTEXT.md (webhook processing flow)
</read_first>
<action>
Create `backend/apps/payments/serializers.py`:
```python
from rest_framework import serializers
from apps.payments.models import Tariff

class TariffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tariff
        fields = ["id", "code", "title", "price_kzt", "description"]
```

Create `backend/apps/payments/views.py`:
```python
import logging
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.payments.models import Payment, Tariff
from apps.payments.serializers import TariffSerializer
from apps.payments.services import validate_hmac
from apps.submissions.models import Submission

log = logging.getLogger(__name__)


class TariffListView(generics.ListAPIView):
    """GET /api/v1/tariffs/ — public list of active tariffs."""
    serializer_class = TariffSerializer
    permission_classes = [AllowAny]
    queryset = Tariff.objects.filter(is_active=True).order_by("price_kzt")


@method_decorator(csrf_exempt, name="dispatch")
class CloudPaymentsCheckView(APIView):
    """POST /api/v1/payments/cloudpayments/check/ — pre-authorization check."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        # HMAC validation
        body = request.body
        received_hmac = request.headers.get("Content-HMAC", "")
        if not validate_hmac(body, received_hmac):
            log.warning("CloudPayments Check: invalid HMAC")
            return Response(status=status.HTTP_400_BAD_REQUEST)

        data = request.POST
        invoice_id = data.get("InvoiceId", "")
        amount = data.get("Amount", "")

        # Validate submission exists
        try:
            sub = Submission.objects.get(id=invoice_id)
        except (Submission.DoesNotExist, ValueError):
            return Response({"code": 13, "reason": "Invoice not found"})

        # Validate not already paid
        if sub.status not in ("created", "in_progress_basic"):
            return Response({"code": 13, "reason": "Already processed"})

        # Validate amount matches tariff
        if sub.tariff and str(sub.tariff.price_kzt) != str(int(float(amount))):
            log.warning("Amount mismatch: expected %s, got %s", sub.tariff.price_kzt, amount)
            return Response({"code": 13, "reason": "Amount mismatch"})

        return Response({"code": 0})


@method_decorator(csrf_exempt, name="dispatch")
class CloudPaymentsPayView(APIView):
    """POST /api/v1/payments/cloudpayments/pay/ — payment confirmation."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        body = request.body
        received_hmac = request.headers.get("Content-HMAC", "")
        if not validate_hmac(body, received_hmac):
            log.warning("CloudPayments Pay: invalid HMAC")
            return Response(status=status.HTTP_400_BAD_REQUEST)

        data = request.POST
        transaction_id = data.get("TransactionId", "")
        invoice_id = data.get("InvoiceId", "")
        amount = data.get("Amount", "0")

        with transaction.atomic():
            payment, created = Payment.objects.get_or_create(
                transaction_id=transaction_id,
                defaults={
                    "amount": int(float(amount)),
                    "currency": data.get("Currency", "KZT"),
                    "status": Payment.Status.SUCCEEDED,
                    "raw_webhook": dict(data),
                },
            )

            if not created:
                log.info("Duplicate webhook for TransactionId=%s, skipping", transaction_id)
                return Response({"code": 0})

            # Link to submission and tariff
            try:
                sub = Submission.objects.select_for_update().get(id=invoice_id)
            except (Submission.DoesNotExist, ValueError):
                log.error("Submission %s not found for TransactionId=%s", invoice_id, transaction_id)
                return Response({"code": 0})  # Accept payment, log error

            payment.submission = sub
            if sub.tariff:
                payment.tariff = sub.tariff
            payment.save()

            # FSM transition
            try:
                sub.mark_paid()
                sub.save()
                log.info("Submission %s marked as paid", sub.id)
            except Exception as e:
                log.error("FSM transition failed for %s: %s", sub.id, e)

        # Trigger bot notification
        from apps.submissions.tasks import notify_bot_payment_success
        notify_bot_payment_success.delay(str(sub.id))

        return Response({"code": 0})
```

Create `backend/apps/payments/urls.py`:
```python
from django.urls import path
from apps.payments.views import TariffListView, CloudPaymentsCheckView, CloudPaymentsPayView

urlpatterns = [
    path("tariffs/", TariffListView.as_view(), name="tariff-list"),
    path("cloudpayments/check/", CloudPaymentsCheckView.as_view(), name="cp-check"),
    path("cloudpayments/pay/", CloudPaymentsPayView.as_view(), name="cp-pay"),
]
```

Update `backend/apps/core/api_urls.py` — add:
```python
path("payments/", include("apps.payments.urls")),
```
</action>
<acceptance_criteria>
- `backend/apps/payments/views.py` contains `class CloudPaymentsCheckView(APIView):`
- `backend/apps/payments/views.py` contains `class CloudPaymentsPayView(APIView):`
- `backend/apps/payments/views.py` contains `validate_hmac(body, received_hmac)`
- `backend/apps/payments/views.py` contains `get_or_create(transaction_id=transaction_id`
- `backend/apps/payments/views.py` contains `select_for_update().get(id=invoice_id)`
- `backend/apps/payments/views.py` contains `sub.mark_paid()`
- `backend/apps/payments/views.py` contains `notify_bot_payment_success.delay`
- `backend/apps/payments/urls.py` contains `cloudpayments/check/`
- `backend/apps/payments/urls.py` contains `cloudpayments/pay/`
- `backend/apps/core/api_urls.py` contains `path("payments/"`
</acceptance_criteria>
</task>

<task id="01-03">
<title>Write webhook tests</title>
<read_first>
- backend/apps/payments/views.py
- backend/apps/payments/services.py
- backend/tests/factories.py
</read_first>
<action>
Create `backend/apps/payments/tests/test_webhook.py`:

```python
import base64
import hashlib
import hmac
import pytest
from unittest.mock import patch
from django.test import override_settings
from rest_framework.test import APIClient

from apps.accounts.models import ClientProfile
from apps.industries.models import Industry, QuestionnaireTemplate
from apps.payments.models import Payment, Tariff
from apps.submissions.models import Submission


def _make_hmac(body: bytes, secret: str = "test-secret") -> str:
    return base64.b64encode(
        hmac.new(secret.encode(), body, hashlib.sha256).digest()
    ).decode()


@pytest.fixture
def setup_submission(db):
    industry = Industry.objects.create(name="IT", code="it", is_active=True)
    template = QuestionnaireTemplate.objects.create(industry=industry, version=1, is_active=True, name="IT v1")
    tariff = Tariff.objects.create(code="ashide_1", title="Ashide 1", price_kzt=45000, is_active=True)
    profile = ClientProfile.objects.create(telegram_id=12345, name="Test", company="TestCo")
    sub = Submission.objects.create(client=profile, template=template, tariff=tariff)
    return sub, tariff, profile


@pytest.mark.django_db
@override_settings(CLOUDPAYMENTS_API_SECRET="test-secret")
class TestCloudPaymentsWebhook:
    def test_check_valid_returns_code_0(self, setup_submission):
        sub, tariff, _ = setup_submission
        body = f"InvoiceId={sub.id}&Amount=45000&Currency=KZT".encode()
        client = APIClient()
        response = client.post(
            "/api/v1/payments/cloudpayments/check/",
            body,
            content_type="application/x-www-form-urlencoded",
            HTTP_CONTENT_HMAC=_make_hmac(body),
        )
        assert response.status_code == 200
        assert response.data["code"] == 0

    def test_check_invalid_hmac_returns_400(self, setup_submission):
        sub, _, _ = setup_submission
        body = f"InvoiceId={sub.id}&Amount=45000".encode()
        client = APIClient()
        response = client.post(
            "/api/v1/payments/cloudpayments/check/",
            body,
            content_type="application/x-www-form-urlencoded",
            HTTP_CONTENT_HMAC="invalid-hmac",
        )
        assert response.status_code == 400

    @patch("apps.submissions.tasks.notify_bot_payment_success.delay")
    def test_pay_creates_payment_and_marks_paid(self, mock_notify, setup_submission):
        sub, tariff, _ = setup_submission
        body = f"TransactionId=TX001&InvoiceId={sub.id}&Amount=45000&Currency=KZT".encode()
        client = APIClient()
        response = client.post(
            "/api/v1/payments/cloudpayments/pay/",
            body,
            content_type="application/x-www-form-urlencoded",
            HTTP_CONTENT_HMAC=_make_hmac(body),
        )
        assert response.status_code == 200
        assert response.data["code"] == 0
        assert Payment.objects.filter(transaction_id="TX001").exists()
        sub.refresh_from_db()
        assert sub.status == "paid"
        mock_notify.assert_called_once_with(str(sub.id))

    @patch("apps.submissions.tasks.notify_bot_payment_success.delay")
    def test_pay_idempotent_duplicate(self, mock_notify, setup_submission):
        sub, _, _ = setup_submission
        body = f"TransactionId=TX002&InvoiceId={sub.id}&Amount=45000&Currency=KZT".encode()
        hmac_val = _make_hmac(body)
        client = APIClient()
        client.post("/api/v1/payments/cloudpayments/pay/", body,
                     content_type="application/x-www-form-urlencoded", HTTP_CONTENT_HMAC=hmac_val)
        response = client.post("/api/v1/payments/cloudpayments/pay/", body,
                               content_type="application/x-www-form-urlencoded", HTTP_CONTENT_HMAC=hmac_val)
        assert response.data["code"] == 0
        assert Payment.objects.filter(transaction_id="TX002").count() == 1

    def test_tariffs_list(self, db):
        Tariff.objects.create(code="t1", title="T1", price_kzt=1000, is_active=True)
        Tariff.objects.create(code="t2", title="T2", price_kzt=2000, is_active=False)
        client = APIClient()
        response = client.get("/api/v1/payments/tariffs/")
        assert response.status_code == 200
        assert len(response.data["results"]) == 1
```
</action>
<acceptance_criteria>
- `backend/apps/payments/tests/test_webhook.py` contains `def test_check_valid_returns_code_0`
- `backend/apps/payments/tests/test_webhook.py` contains `def test_check_invalid_hmac_returns_400`
- `backend/apps/payments/tests/test_webhook.py` contains `def test_pay_creates_payment_and_marks_paid`
- `backend/apps/payments/tests/test_webhook.py` contains `def test_pay_idempotent_duplicate`
- `pytest apps/payments/tests/test_webhook.py -x` exits 0
</acceptance_criteria>
</task>

## Verification

```bash
pytest apps/payments/tests/ -x -q  # all webhook tests pass
```
