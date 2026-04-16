---
phase: 01-infrastructure-data-model
plan: "00"
subsystem: testing
tags: [pytest, pytest-django, factory-boy, xfail, wave0, tdd, bootstrap]

# Dependency graph
requires: []
provides:
  - "backend/pyproject.toml: Poetry 1.8 manifest with pinned versions (Django 5.2, django-fsm-2 4.2.4, WeasyPrint 68.1, Celery 5.6.3)"
  - "backend/conftest.py: shared pytest-django fixtures (db_empty, frozen_now placeholder)"
  - "8 Django app packages under backend/apps/ each with tests/__init__.py"
  - "14 xfail test stub files covering DATA-01..13 and INFRA-03,05,06"
  - "backend/baqsy/ Django project skeleton (settings/base.py, settings/dev.py, urls.py, celery.py)"
  - "apps/core/models.py: TimestampedModel + UUIDModel abstract models"
affects:
  - "01-infrastructure-data-model/01 (Django models — flips xfail→pass)"
  - "01-infrastructure-data-model/02 (Docker Compose — flips INFRA tests)"
  - "01-infrastructure-data-model/03 (Seed/backup — flips test_seed.py, test_backup.py)"

# Tech tracking
tech-stack:
  added:
    - "pytest ^8.3"
    - "pytest-django ^4.9"
    - "pytest-cov ^5.0"
    - "pytest-mock ^3.14"
    - "factory-boy ^3.3"
    - "ruff ^0.6"
    - "mypy ^1.11"
    - "django-debug-toolbar ^4.4"
  patterns:
    - "Wave 0 Nyquist bootstrap: create xfail stubs before implementation so tests flip green as features land"
    - "module-level pytestmark = pytest.mark.xfail(strict=False) for test file-wide xfail"
    - "Guard imports inside test function bodies (not module top) to prevent collection errors"

key-files:
  created:
    - "backend/pyproject.toml"
    - "backend/conftest.py"
    - "backend/baqsy/settings/base.py"
    - "backend/baqsy/settings/dev.py"
    - "backend/apps/core/models.py"
    - "backend/apps/industries/tests/test_models.py"
    - "backend/apps/industries/tests/test_versioning.py"
    - "backend/apps/accounts/tests/test_models.py"
    - "backend/apps/submissions/tests/test_models.py"
    - "backend/apps/submissions/tests/test_immutability.py"
    - "backend/apps/submissions/tests/test_fsm.py"
    - "backend/apps/payments/tests/test_models.py"
    - "backend/apps/reports/tests/test_models.py"
    - "backend/apps/delivery/tests/test_models.py"
    - "backend/apps/content/tests/test_models.py"
    - "backend/tests/test_settings.py"
    - "backend/tests/test_pdf_fonts.py"
    - "backend/tests/test_backup.py"
    - "backend/tests/test_seed.py"
  modified: []

key-decisions:
  - "pytest-django via pyproject.toml [tool.pytest.ini_options] — no separate pytest.ini needed"
  - "module-level pytestmark avoids per-function @pytest.mark.xfail decoration boilerplate"
  - "Guard imports inside test function bodies so pytest collects files without ImportError even before models exist"
  - "django-fsm-2 (not django-fsm) — original archived October 2025, use maintained fork v4.2.4"
  - "django-environ ^0.11 (not 2.x) — PyPI latest stable is 0.11.x; version comment in RESEARCH.md was loose"

patterns-established:
  - "Wave 0 xfail pattern: every test stub has pytestmark = pytest.mark.xfail(strict=False, reason='Phase 1 Wave 0 stub')"
  - "Import-inside-function pattern: all app model imports live inside test function bodies"
  - "8 app packages under backend/apps/ with tests/ subpackage each"

requirements-completed: []

# Metrics
duration: 3min
completed: "2026-04-16"
---

# Phase 1 Plan 00: Test Bootstrap Summary

**pytest-django harness with 14 xfail test stubs covering all DATA-01..13 and INFRA requirements, plus Poetry manifest with pinned production and dev dependencies**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-16T05:40:52Z
- **Completed:** 2026-04-16T05:44:09Z
- **Tasks:** 3
- **Files modified:** 46

## Accomplishments
- Poetry 1.8 manifest (`backend/pyproject.toml`) with exact pinned versions from RESEARCH.md and `[tool.pytest.ini_options]` block pointing at `baqsy.settings.dev`
- Python package skeleton: 8 Django app directories each with `__init__.py` and `tests/__init__.py`; shared `conftest.py` with `db_empty` and `frozen_now` fixtures
- 14 xfail test stub files covering every DATA and INFRA requirement from VALIDATION.md — Plans 01/02/03 flip these from xfail to green as they implement features
- Django project skeleton (`backend/baqsy/`) with settings split (base/dev/prod), celery.py, urls.py with `/health/` endpoint, and `apps/core/models.py` (TimestampedModel + UUIDModel)

## Task Commits

Each task was committed atomically:

1. **Task 0-1: backend/pyproject.toml** - `9cca1d9` (chore)
2. **Task 0-2: conftest.py + app packages + Django skeleton** - `5ccd56c` (chore)
3. **Task 0-3: xfail test stubs (14 files)** - `28aec38` (test)

**Plan metadata:** see docs commit (created with SUMMARY.md)

## Files Created/Modified
- `backend/pyproject.toml` - Poetry 1.8 manifest; Django 5.2, django-fsm-2 4.2.4, WeasyPrint 68.1, pytest-django 4.9
- `backend/conftest.py` - Shared pytest-django fixtures: db_empty alias, frozen_now placeholder
- `backend/baqsy/settings/base.py` - Django base settings with django-environ, INSTALLED_APPS for all 8 apps, AUTH_USER_MODEL, Celery, MinIO
- `backend/baqsy/settings/dev.py` - DEBUG=True, console email backend, logging
- `backend/baqsy/urls.py` - Minimal URL config with /admin/ and /health/ endpoint
- `backend/apps/core/models.py` - TimestampedModel (created_at/updated_at) and UUIDModel abstract base classes
- `backend/apps/industries/tests/test_models.py` - xfail stubs for DATA-01, DATA-02, DATA-03
- `backend/apps/industries/tests/test_versioning.py` - xfail stubs for DATA-12 versioning invariant
- `backend/apps/submissions/tests/test_immutability.py` - xfail stub for DATA-13 template_id immutability
- `backend/apps/submissions/tests/test_fsm.py` - xfail stubs for DATA-05 FSM transitions
- `backend/tests/test_seed.py` - xfail stubs for seed_initial management command
- 9 more xfail test files for remaining DATA and INFRA requirements

## Decisions Made
- `django-environ = "^0.11"` — PyPI latest stable is 0.11.x; RESEARCH.md version comment was a loose note, not a 2.x version
- `django-fsm-2 = "4.2.4"` chosen over original `django-fsm` (archived October 2025, import path stays `from django_fsm import ...`)
- module-level `pytestmark = pytest.mark.xfail(strict=False)` instead of per-function decorator — less boilerplate, same effect
- All app imports guarded inside test function bodies — pytest collection succeeds even before models are implemented

## Deviations from Plan

None — plan executed exactly as written. The pre-existing files (`baqsy/` skeleton, `apps/core/models.py`, `apps/accounts/models.py`) found in the working tree were already correctly structured per CONTEXT.md decisions and were committed as part of the scaffold.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required in this plan. Test infrastructure only.

## Next Phase Readiness
- Plan 01 (Django apps + models) can now use `pytest apps/ -x -q` immediately and see xfail results
- As each model is implemented, the corresponding xfail stub flips to a passing test
- `baqsy.settings.dev` is configured and DJANGO_SETTINGS_MODULE is set in pyproject.toml
- All 8 app packages are importable — no import errors on collection

---
*Phase: 01-infrastructure-data-model*
*Completed: 2026-04-16*
