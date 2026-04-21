import logging

from django.conf import settings
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from apps.payments.models import Payment, Tariff
from apps.payments.serializers import TariffSerializer
from apps.payments.services import parse_webhook_body, parse_webhook_data, validate_hmac
from apps.submissions.models import Submission

log = logging.getLogger(__name__)


class TariffListView(generics.ListAPIView):
    """GET /api/v1/payments/tariffs/ — public list of active tariffs."""

    serializer_class = TariffSerializer
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = Tariff.objects.filter(is_active=True).order_by("price_kzt")


def _resolve_payment_tariff(submission: Submission, tariff_code: str | None) -> Tariff | None:
    """Pick the tariff that matches the payment itself.

    For an upsell, the client pays the upsell price but the submission still
    carries the original ashide_1 tariff — so we need to resolve the payment's
    own tariff from the custom `Data.tariff_code` metadata. If that resolves,
    the amount validation and tariff change logic downstream can trust it.
    """
    if tariff_code:
        tariff = Tariff.objects.filter(code=tariff_code, is_active=True).first()
        if tariff:
            return tariff
    return submission.tariff


@method_decorator(csrf_exempt, name="dispatch")
class CloudPaymentsCheckView(APIView):
    """POST /api/v1/payments/cloudpayments/check/ — pre-authorisation check.

    CloudPayments calls this before charging the card. We verify the submission
    exists, the amount matches the resolved tariff, and the submission is in a
    state where a new payment makes sense. Upsell payments are validated
    against the upsell tariff, not the submission's base tariff.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        body = request.body
        received_hmac = request.headers.get("Content-HMAC", "")
        if not validate_hmac(body, received_hmac):
            log.warning("CloudPayments Check: invalid HMAC")
            return Response(status=status.HTTP_400_BAD_REQUEST)

        payload = parse_webhook_body(body)
        meta = parse_webhook_data(payload)
        invoice_id = payload.get("InvoiceId", "")
        amount_raw = payload.get("Amount", "")
        tariff_code = meta.get("tariff_code")

        try:
            sub = Submission.objects.get(id=invoice_id)
        except (Submission.DoesNotExist, ValueError):
            log.warning("CloudPayments Check: submission %s not found", invoice_id)
            return Response({"code": 13, "reason": "Invoice not found"})

        is_upsell = tariff_code == "upsell"

        if is_upsell:
            # Upsell is only valid once the questionnaire is finished
            if sub.status not in (
                Submission.Status.COMPLETED,
                Submission.Status.UNDER_AUDIT,
                Submission.Status.DELIVERED,
            ):
                return Response({"code": 13, "reason": "Upsell not available yet"})
        else:
            # Base tariff payment: submission must still be awaiting payment
            if sub.status not in (
                Submission.Status.CREATED,
                Submission.Status.IN_PROGRESS_BASIC,
            ):
                return Response({"code": 13, "reason": "Already processed"})

        expected_tariff = _resolve_payment_tariff(sub, tariff_code)
        if expected_tariff and amount_raw:
            try:
                expected = int(expected_tariff.price_kzt)
                received = int(float(amount_raw))
                if expected != received:
                    log.warning(
                        "CloudPayments Check: amount mismatch for sub=%s tariff=%s expected=%s got=%s",
                        sub.id,
                        expected_tariff.code,
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
    idempotently via get_or_create on transaction_id, then advance the
    Submission FSM (for base tariffs) or upgrade the tariff (for upsell) and
    enqueue a bot notification task. Idempotent and atomic per submission row.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        body = request.body
        received_hmac = request.headers.get("Content-HMAC", "")
        if not validate_hmac(body, received_hmac):
            log.warning("CloudPayments Pay: invalid HMAC")
            return Response(status=status.HTTP_400_BAD_REQUEST)

        payload = parse_webhook_body(body)
        meta = parse_webhook_data(payload)
        transaction_id = payload.get("TransactionId", "")
        invoice_id = payload.get("InvoiceId", "")
        amount_raw = payload.get("Amount", "0")
        tariff_code = meta.get("tariff_code")

        if not transaction_id:
            log.warning("CloudPayments Pay: missing TransactionId in payload")
            return Response(status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            try:
                sub = Submission.objects.select_for_update().get(id=invoice_id)
            except (Submission.DoesNotExist, ValueError):
                log.error(
                    "CloudPayments Pay: submission %s not found for TransactionId=%s",
                    invoice_id,
                    transaction_id,
                )
                # Accept (return 0) — money was taken; rely on manual reconciliation.
                return Response({"code": 0})

            try:
                amount = int(float(amount_raw))
            except (ValueError, TypeError):
                amount = 0

            payment_tariff = _resolve_payment_tariff(sub, tariff_code)
            is_upsell = tariff_code == "upsell" or (
                payment_tariff is not None and payment_tariff.code == "upsell"
            )

            payment, created = Payment.objects.get_or_create(
                transaction_id=transaction_id,
                defaults={
                    "submission": sub,
                    "tariff": payment_tariff,
                    "amount": amount,
                    "currency": payload.get("Currency", "KZT"),
                    "status": Payment.Status.SUCCEEDED,
                    # Store both raw payload and decoded metadata for auditability
                    "raw_webhook": {**payload, "_data": meta},
                },
            )

            if not created:
                log.info(
                    "CloudPayments Pay: duplicate webhook TransactionId=%s, skipping",
                    transaction_id,
                )
                return Response({"code": 0})

            if is_upsell:
                ashide_2 = Tariff.objects.filter(code="ashide_2", is_active=True).first()
                if ashide_2 and sub.tariff_id != ashide_2.id:
                    sub.tariff = ashide_2
                    sub.save(update_fields=["tariff"])
                    log.info(
                        "CloudPayments Pay: submission %s upgraded to Ashide 2 (upsell tx=%s)",
                        sub.id,
                        transaction_id,
                    )
            else:
                # Base tariff — advance the FSM toward `paid`.
                from django_fsm import TransitionNotAllowed

                try:
                    if sub.status == Submission.Status.CREATED:
                        sub.start_onboarding()
                    if sub.status == Submission.Status.IN_PROGRESS_BASIC:
                        sub.mark_paid()
                    sub.save()
                    log.info(
                        "CloudPayments Pay: submission %s transitioned to paid (TransactionId=%s)",
                        sub.id,
                        transaction_id,
                    )
                except TransitionNotAllowed as exc:
                    log.info(
                        "CloudPayments Pay: no FSM transition for sub=%s status=%s tx=%s: %s",
                        sub.id,
                        sub.status,
                        transaction_id,
                        exc,
                    )

        from apps.submissions.tasks import notify_bot_payment_success

        notify_bot_payment_success.delay(str(sub.id))

        return Response({"code": 0})


class UpsellView(APIView):
    """POST /api/v1/payments/upsell/ — initiate upsell from Ashide 1 to Ashide 2.

    Returns CloudPayments Widget configuration for the upsell payment.
    Validates that the submission belongs to the authenticated client,
    the current tariff is ashide_1, and the submission is at least completed.
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def post(self, request):
        submission_id = request.data.get("submission_id")
        if not submission_id:
            return Response({"detail": "submission_id required"}, status=400)

        from apps.submissions.views import _get_client_profile

        client = _get_client_profile(request.user)
        if not client:
            return Response({"detail": "Client not found"}, status=403)

        try:
            sub = Submission.objects.get(id=submission_id, client=client)
        except (Submission.DoesNotExist, ValueError):
            return Response({"detail": "Submission not found"}, status=404)

        if not sub.tariff or sub.tariff.code != "ashide_1":
            return Response({"detail": "Upsell available only for Ashide 1"}, status=400)

        if sub.status not in (
            Submission.Status.COMPLETED,
            Submission.Status.UNDER_AUDIT,
            Submission.Status.DELIVERED,
        ):
            return Response({"detail": "Submission not yet completed"}, status=400)

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
                # `data` arrives as JSON in the webhook's Data field so the pay
                # handler can tell upsell from a base-tariff payment.
                "data": {"tariff_code": "upsell", "submission_id": str(sub.id)},
            }
        )
