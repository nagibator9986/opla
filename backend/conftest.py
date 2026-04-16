"""
Shared pytest configuration.

pytest-django discovers DJANGO_SETTINGS_MODULE from pyproject.toml
[tool.pytest.ini_options]. This file adds shared fixtures that tests across
apps can reuse.
"""
from __future__ import annotations

import pytest

from tests.factories import (
    ClientProfileFactory,
    IndustryFactory,
    QuestionFactory,
    QuestionnaireTemplateFactory,
    SubmissionFactory,
    TariffFactory,
    UserFactory,
)


@pytest.fixture
def db_empty(db):
    """Alias for pytest-django `db` fixture — explicit opt-in to DB access."""
    return db


@pytest.fixture
def frozen_now():
    """Placeholder for a future freezegun fixture. Not yet implemented."""
    pytest.skip("frozen_now fixture not yet implemented (Phase 1 scaffolding)")


@pytest.fixture
def user_factory():
    return UserFactory


@pytest.fixture
def industry_factory():
    return IndustryFactory


@pytest.fixture
def questionnaire_template_factory():
    return QuestionnaireTemplateFactory


@pytest.fixture
def question_factory():
    return QuestionFactory


@pytest.fixture
def tariff_factory():
    return TariffFactory


@pytest.fixture
def client_profile_factory():
    return ClientProfileFactory


@pytest.fixture
def submission_factory():
    return SubmissionFactory
