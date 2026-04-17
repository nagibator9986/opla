"""Tests for reports.generate_pdf Celery task and supporting services."""
from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

from apps.reports.models import AuditReport
from apps.reports.services import _format_answer_value
from tests.factories import (
    ClientProfileFactory,
    QuestionFactory,
    SubmissionFactory,
    TariffFactory,
)


def _ensure_module_mocks():
    """Inject fake modules into sys.modules if they are not already installed.

    On macOS dev machines WeasyPrint system libraries (libgobject, etc.) and
    boto3 may not be installed.  This ensures ``import weasyprint`` and
    ``import boto3`` inside services.py do not raise OSError/ModuleNotFoundError
    at import time.  The per-test patches still override the symbols as needed.
    """
    if "weasyprint" not in sys.modules:
        fake_wp = ModuleType("weasyprint")
        fake_wp.HTML = MagicMock()
        sys.modules["weasyprint"] = fake_wp

    if "boto3" not in sys.modules:
        fake_boto3 = ModuleType("boto3")
        fake_boto3.client = MagicMock()
        sys.modules["boto3"] = fake_boto3


_ensure_module_mocks()


# ─── Local factory ──────────────────────────────────────────────────────────

class AuditReportFactory:
    """Simple factory for AuditReport (not factory-boy, avoids import cycles)."""

    @staticmethod
    def create(submission=None, admin_text="Аудит: всё отлично.", **kwargs):
        if submission is None:
            submission = SubmissionFactory()
        return AuditReport.objects.create(
            submission=submission,
            admin_text=admin_text,
            **kwargs,
        )


# ─── format_answer_value filter ─────────────────────────────────────────────

def test_format_answer_value_text():
    assert _format_answer_value({"text": "foo"}) == "foo"


def test_format_answer_value_number():
    assert _format_answer_value({"number": 42}) == "42"


def test_format_answer_value_choice():
    assert _format_answer_value({"choice": "option"}) == "option"


def test_format_answer_value_choices():
    assert _format_answer_value({"choices": ["a", "b"]}) == "a, b"


def test_format_answer_value_unknown_falls_back():
    """Non-dict or unexpected dict returns str representation."""
    assert _format_answer_value("raw string") == "raw string"
    result = _format_answer_value({"unknown_key": "val"})
    assert "val" in result


# ─── render_pdf service ─────────────────────────────────────────────────────

@pytest.mark.django_db
def test_render_pdf_returns_bytes():
    """render_pdf() with mocked WeasyPrint returns bytes (PDF-03)."""
    submission = SubmissionFactory(tariff=TariffFactory(code="ashide_1"))
    report = AuditReportFactory.create(submission=submission, admin_text="<p>Тест</p>")

    fake_pdf_bytes = b"%PDF-1.4 fake"
    mock_html_instance = MagicMock()
    mock_html_instance.write_pdf.return_value = fake_pdf_bytes

    with patch("weasyprint.HTML", return_value=mock_html_instance) as mock_html:
        from apps.reports.services import render_pdf
        result = render_pdf(report)

    assert isinstance(result, bytes)
    assert result == fake_pdf_bytes
    mock_html.assert_called_once()


@pytest.mark.django_db
def test_render_pdf_includes_client_and_company():
    """HTML passed to WeasyPrint contains client name and company (PDF-01, PDF-04)."""
    client = ClientProfileFactory(name="Иван Иванов", company="ТОО ТестКо")
    submission = SubmissionFactory(
        client=client,
        tariff=TariffFactory(code="ashide_1"),
    )
    report = AuditReportFactory.create(submission=submission, admin_text="Анализ готов")

    captured_html = {}

    def fake_html(string=None, base_url=None, **kwargs):
        captured_html["html"] = string
        m = MagicMock()
        m.write_pdf.return_value = b"%PDF"
        return m

    with patch("weasyprint.HTML", side_effect=fake_html):
        from apps.reports.services import render_pdf
        render_pdf(report)

    html = captured_html["html"]
    assert "Иван Иванов" in html, "Client name must appear in PDF HTML"
    assert "ТОО ТестКо" in html, "Company name must appear in PDF HTML"


@pytest.mark.django_db
def test_render_pdf_ashide2_extended_section():
    """HTML for ashide_2 tariff includes extended section (PDF-02)."""
    tariff = TariffFactory(code="ashide_2", title="Ashide 2")
    submission = SubmissionFactory(tariff=tariff)
    report = AuditReportFactory.create(submission=submission)

    captured_html = {}

    def fake_html(string=None, base_url=None, **kwargs):
        captured_html["html"] = string
        m = MagicMock()
        m.write_pdf.return_value = b"%PDF"
        return m

    with patch("weasyprint.HTML", side_effect=fake_html):
        from apps.reports.services import render_pdf
        render_pdf(report)

    html = captured_html["html"]
    assert "ashide_2" in html or "Расширенный анализ" in html, \
        "ashide_2 conditional section must appear in HTML for ashide_2 tariff"


# ─── generate_pdf task ──────────────────────────────────────────────────────

@pytest.mark.django_db
def test_generate_pdf_creates_pdf():
    """generate_pdf task creates PDF and sets pdf_url on report (PDF-01, PDF-03)."""
    submission = SubmissionFactory(tariff=TariffFactory(code="ashide_1"))
    report = AuditReportFactory.create(submission=submission, admin_text="Тест отчёт")

    fake_presigned = "https://minio.example.com/pdfs/test.pdf?sig=xxx"

    with patch("weasyprint.HTML") as mock_html, \
         patch("boto3.client") as mock_boto3:
        mock_html_instance = MagicMock()
        mock_html_instance.write_pdf.return_value = b"%PDF-fake"
        mock_html.return_value = mock_html_instance

        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.return_value = fake_presigned
        mock_boto3.return_value = mock_s3

        from apps.reports.tasks import generate_pdf
        generate_pdf(str(report.id))

    report.refresh_from_db()
    assert report.pdf_url == fake_presigned, "pdf_url must be set after generate_pdf"


@pytest.mark.django_db
def test_generate_pdf_idempotent():
    """generate_pdf does NOT re-generate if pdf_url already set (PDF-07)."""
    existing_url = "https://minio.example.com/pdfs/existing.pdf"
    submission = SubmissionFactory(tariff=TariffFactory(code="ashide_1"))
    report = AuditReportFactory.create(
        submission=submission,
        admin_text="already done",
        pdf_url=existing_url,
    )

    with patch("boto3.client") as mock_boto3, \
         patch("weasyprint.HTML") as mock_html:
        from apps.reports.tasks import generate_pdf
        generate_pdf(str(report.id))

        mock_boto3.assert_not_called()
        mock_html.assert_not_called()

    report.refresh_from_db()
    assert report.pdf_url == existing_url, "pdf_url must not change when already set"


@pytest.mark.django_db
def test_generate_pdf_ashide2_extended():
    """generate_pdf for ashide_2 submission renders HTML with extended section (PDF-02)."""
    tariff = TariffFactory(code="ashide_2")
    submission = SubmissionFactory(tariff=tariff)
    report = AuditReportFactory.create(submission=submission, admin_text="Ashide 2 отчёт")

    captured_html = {}

    def fake_html(string=None, base_url=None, **kwargs):
        captured_html["html"] = string
        m = MagicMock()
        m.write_pdf.return_value = b"%PDF"
        return m

    with patch("weasyprint.HTML", side_effect=fake_html), \
         patch("boto3.client") as mock_boto3:
        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.return_value = "https://minio.example.com/pdfs/a2.pdf"
        mock_boto3.return_value = mock_s3

        from apps.reports.tasks import generate_pdf
        generate_pdf(str(report.id))

    html = captured_html.get("html", "")
    assert "ashide_2" in html or "Расширенный анализ" in html, \
        "Extended section must appear in HTML for ashide_2"
