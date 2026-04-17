import logging

from django.conf import settings
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.payments.models import Payment, Tariff
from apps.payments.serializers import TariffSerializer
from apps.payments.services import validate_hmac
from apps.submissions.models import Submission

log = logging.getLogger(__name__)


class TariffListView(generics.ListAPIView):
    """GET /api/v1/payments/tariffs/ — public list of active tariffs."""

    serializer_class = TariffSerializer
    permission_classes = [AllowAny]
    queryset = Tariff.objects.filter(is_active=True).order_by("price_kzt")


@method_decorator(csrf_exempt, name="dispatch")
class CloudPaymentsCheckView(APIView):
    """POST /api/v1/payments/cloudpayments/check/ — pre-authorisation check.

    CloudPayments calls this before charging the card. We verify the submission
    exists, the amount matches the tariff, and the submission is not already paid.
    """

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
            log.warning("CloudPayments Check: submission %s not found", invoice_id)
            return Response({"code": 13, "reason": "Invoice not found"})

        # Validate submission is not already paid or further
        if sub.status not in (
            Submission.Status.CREATED,
            Submission.Status.IN_PROGRESS_BASIC,
        ):
            return Response({"code": 13, "reason": "Already processed"})

        # Validate amount matches tariff
        if sub.tariff and amount:
            try:
                expected = int(sub.tariff.price_kzt)
                received = int(float(amount))
                if expected != received:
                    log.warning(
                        "CloudPayments Check: amount mismatch for sub=%s, expected=%s got=%s",
                        sub.id,
                        expected,
                        received,
                    )
                    return Response({"code": 13, "reason": "Amount mismatch"})
            except (ValueError, TypeError):
                return Response({"code": 13, "reason": "Invalid amount"})

        return Response({"code": 0})


@method_decorator(csrf_exempt, name="dispatch")
class CloudPaymentsPayView(APIView):
    """POST /api/v1/payments/cloudpayments/pay/ — payment confirmation.

    CloudPayments calls this after a successful charge. We create Payment
    idempotently via get_or_create on transaction_id, then advance the Submission
    FSM to `paid` and enqueue a bot notification task.
    """

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
        amount_raw = data.get("Amount", "0")

        with transaction.atomic():
            # Locate submission first — required FK for Payment
            try:
                sub = Submission.objects.select_for_update().get(id=invoice_id)
            except (Submission.DoesNotExist, ValueError):
                log.error(
                    "CloudPayments Pay: submission %s not found for TransactionId=%s",
                    invoice_id,
                    transaction_id,
                )
                # Accept the payment (return 0) but log the error — money is already taken
                return Response({"code": 0})

            try:
                amount = int(float(amount_raw))
            except (ValueError, TypeError):
                amount = 0

            payment, created = Payment.objects.get_or_create(
                transaction_id=transaction_id,
                defaults={
                    "submission": sub,
                    "tariff": sub.tariff,
                    "amount": amount,
                    "currency": data.get("Currency", "KZT"),
                    "status": Payment.Status.SUCCEEDED,
                    "raw_webhook": dict(data),
                },
            )

            if not created:
                log.info(
                    "CloudPayments Pay: duplicate webhook TransactionId=%s, skipping",
                    transaction_id,
                )
                return Response({"code": 0})

            # FSM transition: advance submission to paid state.
            # mark_paid() requires in_progress_basic; if submission is still in
            # `created` (payment arrived before onboarding completed) we advance it first.
            try:
                if sub.status == Submission.Status.CREATED:
                    sub.start_onboarding()
                sub.mark_paid()
                sub.save()
                log.info(
                    "CloudPayments Pay: submission %s transitioned to paid (TransactionId=%s)",
                    sub.id,
                    transaction_id,
                )
            except Exception as exc:
                log.error(
                    "CloudPayments Pay: FSM transition failed for sub=%s tx=%s: %s",
                    sub.id,
                    transaction_id,
                    exc,
                )

            # Handle upsell: upgrade tariff from ashide_1 to ashide_2
            if payment.tariff and payment.tariff.code == "upsell":
                ashide_2 = Tariff.objects.filter(code="ashide_2", is_active=True).first()
                if ashide_2:
                    sub.tariff = ashide_2
                    sub.save(update_fields=["tariff"])
                    log.info(
                        "CloudPayments Pay: submission %s upgraded to Ashide 2 (upsell tx=%s)",
                        sub.id,
                        transaction_id,
                    )

        # Enqueue bot notification outside the atomic block
        from apps.submissions.tasks import notify_bot_payment_success

        notify_bot_payment_success.delay(str(sub.id))

        return Response({"code": 0})


class UpsellView(APIView):
    """POST /api/v1/payments/upsell/ — initiate upsell from Ashide 1 to Ashide 2.

    Returns CloudPayments Widget configuration for the upsell payment.
    Validates that the submission belongs to the authenticated client,
    current tariff is ashide_1, and status is at least completed.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        submission_id = request.data.get("submission_id")
        if not submission_id:
            return Response({"detail": "submission_id required"}, status=400)

        # Resolve the client profile from the JWT-authenticated user
        from apps.submissions.views import _get_client_profile

        client = _get_client_profile(request.user)
        if not client:
            return Response({"detail": "Client not found"}, status=403)

        try:
            sub = Submission.objects.get(id=submission_id, client=client)
        except (Submission.DoesNotExist, ValueError):
            return Response({"detail": "Submission not found"}, status=404)

        # Validate current tariff is ashide_1
        if not sub.tariff or sub.tariff.code != "ashide_1":
            return Response({"detail": "Upsell available only for Ashide 1"}, status=400)

        # Validate submission status is at least completed
        if sub.status not in (
            Submission.Status.COMPLETED,
            Submission.Status.UNDER_AUDIT,
            Submission.Status.DELIVERED,
        ):
            return Response({"detail": "Submission not yet completed"}, status=400)

        # Fetch the active upsell tariff
        try:
            upsell_tariff = Tariff.objects.get(code="upsell", is_active=True)
        except Tariff.DoesNotExist:
            log.error("UpsellView: upsell tariff not found in DB")
            return Response({"detail": "Upsell tariff not configured"}, status=500)

        return Response(
            {
                "publicId": settings.CLOUDPAYMENTS_PUBLIC_ID,
                "amount": int(upsell_tariff.price_kzt),
                "currency": "KZT",
                "invoiceId": str(sub.id),
                "description": f"Upsell Ashide 1\u21922: {client.company}",
                "accountId": str(client.id),
                "tariff_code": "upsell",
            }
        )
