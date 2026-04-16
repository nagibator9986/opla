"""Tests for seed_initial management command (Plan 03)."""
from __future__ import annotations

import pytest
from django.core.management import call_command

from apps.accounts.models import BaseUser
from apps.industries.models import Industry, QuestionnaireTemplate, Question
from apps.payments.models import Tariff


@pytest.mark.django_db
def test_seed_creates_baseline_data():
    call_command("seed_initial")

    assert Industry.objects.count() == 5
    assert Tariff.objects.count() == 3
    assert QuestionnaireTemplate.objects.filter(is_active=True).count() == 5
    assert BaseUser.objects.filter(is_superuser=True).exists()

    # Each template has 9 demo questions
    for tmpl in QuestionnaireTemplate.objects.all():
        assert tmpl.questions.count() == 9

    # Verify specific tariffs with correct prices
    assert Tariff.objects.filter(code="ashide_1", price_kzt=45000).exists()
    assert Tariff.objects.filter(code="ashide_2", price_kzt=135000).exists()
    assert Tariff.objects.filter(code="upsell", price_kzt=90000).exists()


@pytest.mark.django_db
def test_seed_initial_idempotent():
    call_command("seed_initial")
    count_industries_1 = Industry.objects.count()
    count_tariffs_1 = Tariff.objects.count()
    count_templates_1 = QuestionnaireTemplate.objects.count()
    count_questions_1 = Question.objects.count()

    # Second run must not raise and must not duplicate records
    call_command("seed_initial")

    assert Industry.objects.count() == count_industries_1
    assert Tariff.objects.count() == count_tariffs_1
    assert QuestionnaireTemplate.objects.count() == count_templates_1
    assert Question.objects.count() == count_questions_1


@pytest.mark.django_db
def test_seed_industry_codes():
    call_command("seed_initial")
    expected_codes = {"retail", "it-digital", "manufacturing", "services", "food-beverage"}
    actual_codes = set(Industry.objects.values_list("code", flat=True))
    assert actual_codes == expected_codes


@pytest.mark.django_db
def test_seed_demo_template_blocks():
    """Each demo template has questions in blocks A, B, and C."""
    call_command("seed_initial")
    for tmpl in QuestionnaireTemplate.objects.all():
        blocks = set(tmpl.questions.values_list("block", flat=True))
        assert "A" in blocks
        assert "B" in blocks
        assert "C" in blocks


@pytest.mark.django_db
def test_seed_superuser_idempotent():
    """Running seed twice does not create a second superuser."""
    call_command("seed_initial")
    call_command("seed_initial")
    assert BaseUser.objects.filter(is_superuser=True).count() == 1
