"""
Phase 1 shared pytest configuration.

pytest-django discovers DJANGO_SETTINGS_MODULE from pyproject.toml
[tool.pytest.ini_options]. This file adds shared fixtures that tests across
apps can reuse.
"""
from __future__ import annotations

import pytest


@pytest.fixture
def db_empty(db):
    """Alias for pytest-django `db` fixture — explicit opt-in to DB access."""
    return db


@pytest.fixture
def frozen_now():
    """Placeholder for a future freezegun fixture. Not yet implemented."""
    pytest.skip("frozen_now fixture not yet implemented (Phase 1 scaffolding)")
