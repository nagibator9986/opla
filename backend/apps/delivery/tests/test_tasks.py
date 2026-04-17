"""Tests for delivery Celery tasks: deliver_telegram, deliver_whatsapp, _try_mark_delivered."""
from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock, call, patch

import pytest

from apps.delivery.models import DeliveryLog
from apps.reports.models import AuditReport
from apps.submissions.models import Submission
from tests.factories import (
    ClientProfileFactory,
    SubmissionFactory,
    TariffFactory,
)


def _ensure_module_mocks():
    """Inject fake modules so weasyprint/boto3 don't fail on import."""
    if "weasyprint" not in sys.modules:
        fake_wp = ModuleType("weasyprint")
        fake_wp.HTML = MagicMock()
        sys.modules["weasyprint"] = fake_wp

    if "boto3" not in sys.modules:
        fake_boto3 = ModuleType("boto3")
        fake_boto3.client = MagicMock()
        sys.modules["boto3"] = fake_boto3


_ensure_module_mocks()


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _make_under_audit_submission(**client_kwargs):
    """Create a Submission in UNDER_AUDIT status with the given client overrides."""
    client = ClientProfileFactory(**client_kwargs)
    sub = SubmissionFactory(client=client, tariff=TariffFactory(code="ashide_1"))
    # Advance FSM: created → in_progress_basic → paid → in_progress_full → completed → under_audit
    sub.start_onboarding()
    sub.save(update_fields=["status"])
    sub.mark_paid()
    sub.save(update_fields=["status"])
    sub.start_questionnaire()
    sub.save(update_fields=["status"])
    sub.complete_questionnaire()
    sub.save(update_fields=["status", "completed_at"])
    sub.start_audit()
    sub.save(update_fields=["status"])
    return sub


def _make_report(submission=None, pdf_url="https://minio.example.com/file.pdf", **kwargs):
    """Create AuditReport for a submission."""
    if submission is None:
        submission = _make_under_audit_submission()
    return AuditReport.objects.create(
        submission=submission,
        pdf_url=pdf_url,
        admin_text="Test audit",
        **kwargs,
    )


def _mock_tg_post_success(message_id: int = 42) -> MagicMock:
    """Return a mock for requests.post that handles sendMessage and sendDocument."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"result": {"message_id": message_id}}
    return mock_resp


def _mock_pdf_get() -> MagicMock:
    """Return a mock for requests.get (PDF download)."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.content = b"%PDF-1.4 fake"
    return mock_resp


# ─── deliver_telegram tests ──────────────────────────────────────────────────

@pytest.mark.django_db
def test_deliver_telegram_sends_text_first():
    """deliver_telegram calls sendMessage with companion text before sendDocument (DLV-06)."""
    report = _make_report()

    with patch("requests.post", return_value=_mock_tg_post_success()) as mock_post, \
         patch("requests.get", return_value=_mock_pdf_get()):
        from apps.delivery.tasks import deliver_telegram
        deliver_telegram(str(report.id))

    # First call must be sendMessage
    first_url = mock_post.call_args_list[0][0][0]
    assert "sendMessage" in first_url

    # sendMessage must contain the companion text
    first_json = mock_post.call_args_list[0][1]["json"]
    assert "Спасибо за обращение" in first_json["text"]


@pytest.mark.django_db
def test_deliver_telegram_sends_document():
    """deliver_telegram calls sendDocument with audit_report.pdf file (DLV-01)."""
    report = _make_report()

    with patch("requests.post", return_value=_mock_tg_post_success()) as mock_post, \
         patch("requests.get", return_value=_mock_pdf_get()):
        from apps.delivery.tasks import deliver_telegram
        deliver_telegram(str(report.id))

    # One of the post calls must be sendDocument
    send_doc_calls = [
        c for c in mock_post.call_args_list
        if "sendDocument" in c[0][0]
    ]
    assert len(send_doc_calls) == 1, "sendDocument must be called exactly once"
    _, kwargs = send_doc_calls[0]
    assert "document" in kwargs["files"]
    filename, _, mimetype = kwargs["files"]["document"]
    assert filename == "audit_report.pdf"
    assert mimetype == "application/pdf"


@pytest.mark.django_db
def test_deliver_telegram_creates_delivery_log():
    """deliver_telegram creates DeliveryLog with status=delivered and external_id set (DLV-04)."""
    report = _make_report()

    with patch("requests.post", return_value=_mock_tg_post_success(message_id=99)), \
         patch("requests.get", return_value=_mock_pdf_get()):
        from apps.delivery.tasks import deliver_telegram
        deliver_telegram(str(report.id))

    log_entry = DeliveryLog.objects.get(report=report, channel=DeliveryLog.Channel.TELEGRAM)
    assert log_entry.status == DeliveryLog.Status.DELIVERED
    assert log_entry.external_id == "99"


@pytest.mark.django_db
def test_deliver_telegram_idempotent():
    """deliver_telegram skips API calls if DeliveryLog already has status=delivered."""
    report = _make_report()
    # Pre-create a delivered DeliveryLog
    DeliveryLog.objects.create(
        report=report,
        channel=DeliveryLog.Channel.TELEGRAM,
        status=DeliveryLog.Status.DELIVERED,
        external_id="existing-123",
    )

    with patch("requests.post") as mock_post, \
         patch("requests.get") as mock_get:
        from apps.delivery.tasks import deliver_telegram
        deliver_telegram(str(report.id))

    mock_post.assert_not_called()
    mock_get.assert_not_called()


# ─── deliver_whatsapp tests ──────────────────────────────────────────────────

@pytest.mark.django_db
def test_deliver_whatsapp_calls_provider():
    """deliver_whatsapp calls Wazzup24Provider.send_document with correct args (DLV-02)."""
    client = ClientProfileFactory(phone_wa="77009876543")
    sub = _make_under_audit_submission.__wrapped__(client) if hasattr(_make_under_audit_submission, "__wrapped__") else None
    # Build manually to use our client
    sub = SubmissionFactory(client=client, tariff=TariffFactory(code="ashide_1"))
    sub.start_onboarding(); sub.save(update_fields=["status"])
    sub.mark_paid(); sub.save(update_fields=["status"])
    sub.start_questionnaire(); sub.save(update_fields=["status"])
    sub.complete_questionnaire(); sub.save(update_fields=["status", "completed_at"])
    sub.start_audit(); sub.save(update_fields=["status"])
    report = _make_report(submission=sub, pdf_url="https://minio.example.com/test.pdf")

    with patch(
        "apps.delivery.providers.wazzup24.Wazzup24Provider.send_document",
        return_value="wa-msg-123",
    ) as mock_send:
        from apps.delivery.tasks import deliver_whatsapp
        deliver_whatsapp(str(report.id))

    mock_send.assert_called_once_with(
        phone="77009876543",
        file_url="https://minio.example.com/test.pdf",
        caption="Спасибо за обращение! Ваш аудит-отчёт готов.",
    )


@pytest.mark.django_db
def test_deliver_whatsapp_creates_delivery_log():
    """deliver_whatsapp creates DeliveryLog with channel=whatsapp and status=delivered (DLV-04)."""
    client = ClientProfileFactory(phone_wa="77001111111")
    sub = SubmissionFactory(client=client, tariff=TariffFactory(code="ashide_1"))
    sub.start_onboarding(); sub.save(update_fields=["status"])
    sub.mark_paid(); sub.save(update_fields=["status"])
    sub.start_questionnaire(); sub.save(update_fields=["status"])
    sub.complete_questionnaire(); sub.save(update_fields=["status", "completed_at"])
    sub.start_audit(); sub.save(update_fields=["status"])
    report = _make_report(submission=sub)

    with patch(
        "apps.delivery.providers.wazzup24.Wazzup24Provider.send_document",
        return_value="wa-external-id",
    ):
        from apps.delivery.tasks import deliver_whatsapp
        deliver_whatsapp(str(report.id))

    log_entry = DeliveryLog.objects.get(report=report, channel=DeliveryLog.Channel.WHATSAPP)
    assert log_entry.status == DeliveryLog.Status.DELIVERED
    assert log_entry.external_id == "wa-external-id"


@pytest.mark.django_db
def test_deliver_whatsapp_no_phone_skips():
    """deliver_whatsapp creates failed DeliveryLog with error=no_phone_wa when phone_wa is empty."""
    client = ClientProfileFactory(phone_wa="")
    sub = SubmissionFactory(client=client, tariff=TariffFactory(code="ashide_1"))
    sub.start_onboarding(); sub.save(update_fields=["status"])
    sub.mark_paid(); sub.save(update_fields=["status"])
    sub.start_questionnaire(); sub.save(update_fields=["status"])
    sub.complete_questionnaire(); sub.save(update_fields=["status", "completed_at"])
    sub.start_audit(); sub.save(update_fields=["status"])
    report = _make_report(submission=sub)

    with patch(
        "apps.delivery.providers.wazzup24.Wazzup24Provider.send_document"
    ) as mock_send:
        from apps.delivery.tasks import deliver_whatsapp
        deliver_whatsapp(str(report.id))

    mock_send.assert_not_called()
    log_entry = DeliveryLog.objects.get(report=report, channel=DeliveryLog.Channel.WHATSAPP)
    assert log_entry.status == DeliveryLog.Status.FAILED
    assert log_entry.error == "no_phone_wa"


# ─── _try_mark_delivered tests ───────────────────────────────────────────────

@pytest.mark.django_db
def test_try_mark_delivered_both_channels():
    """When both TG and WA DeliveryLogs are delivered, Submission transitions to delivered."""
    client = ClientProfileFactory(phone_wa="77002222222")
    sub = SubmissionFactory(client=client, tariff=TariffFactory(code="ashide_1"))
    sub.start_onboarding(); sub.save(update_fields=["status"])
    sub.mark_paid(); sub.save(update_fields=["status"])
    sub.start_questionnaire(); sub.save(update_fields=["status"])
    sub.complete_questionnaire(); sub.save(update_fields=["status", "completed_at"])
    sub.start_audit(); sub.save(update_fields=["status"])
    report = _make_report(submission=sub)

    DeliveryLog.objects.create(
        report=report, channel=DeliveryLog.Channel.TELEGRAM, status=DeliveryLog.Status.DELIVERED
    )
    DeliveryLog.objects.create(
        report=report, channel=DeliveryLog.Channel.WHATSAPP, status=DeliveryLog.Status.DELIVERED
    )

    from apps.delivery.tasks import _try_mark_delivered
    _try_mark_delivered(report)

    sub.refresh_from_db()
    assert sub.status == Submission.Status.DELIVERED


@pytest.mark.django_db
def test_try_mark_delivered_one_missing():
    """When only Telegram is delivered (WA pending), Submission stays in under_audit."""
    client = ClientProfileFactory(phone_wa="77003333333")
    sub = SubmissionFactory(client=client, tariff=TariffFactory(code="ashide_1"))
    sub.start_onboarding(); sub.save(update_fields=["status"])
    sub.mark_paid(); sub.save(update_fields=["status"])
    sub.start_questionnaire(); sub.save(update_fields=["status"])
    sub.complete_questionnaire(); sub.save(update_fields=["status", "completed_at"])
    sub.start_audit(); sub.save(update_fields=["status"])
    report = _make_report(submission=sub)

    # Only Telegram delivered, WhatsApp not yet
    DeliveryLog.objects.create(
        report=report, channel=DeliveryLog.Channel.TELEGRAM, status=DeliveryLog.Status.DELIVERED
    )

    from apps.delivery.tasks import _try_mark_delivered
    _try_mark_delivered(report)

    sub.refresh_from_db()
    assert sub.status == Submission.Status.UNDER_AUDIT


@pytest.mark.django_db
def test_try_mark_delivered_no_wa_phone():
    """When client has no phone_wa and Telegram is delivered, Submission transitions to delivered."""
    client = ClientProfileFactory(phone_wa="")
    sub = SubmissionFactory(client=client, tariff=TariffFactory(code="ashide_1"))
    sub.start_onboarding(); sub.save(update_fields=["status"])
    sub.mark_paid(); sub.save(update_fields=["status"])
    sub.start_questionnaire(); sub.save(update_fields=["status"])
    sub.complete_questionnaire(); sub.save(update_fields=["status", "completed_at"])
    sub.start_audit(); sub.save(update_fields=["status"])
    report = _make_report(submission=sub)

    # Only Telegram delivered; no WA required since phone_wa is empty
    DeliveryLog.objects.create(
        report=report, channel=DeliveryLog.Channel.TELEGRAM, status=DeliveryLog.Status.DELIVERED
    )

    from apps.delivery.tasks import _try_mark_delivered
    _try_mark_delivered(report)

    sub.refresh_from_db()
    assert sub.status == Submission.Status.DELIVERED


# ─── autoretry attribute test ────────────────────────────────────────────────

def test_deliver_telegram_retries_on_network_error():
    """deliver_telegram task has autoretry_for=(RequestException,) attribute (DLV-05)."""
    from requests.exceptions import RequestException

    from apps.delivery.tasks import deliver_telegram

    assert hasattr(deliver_telegram, "autoretry_for")
    assert RequestException in deliver_telegram.autoretry_for
