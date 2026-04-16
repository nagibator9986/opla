---
phase: 01-infrastructure-data-model
plan: 00
type: execute
wave: 0
depends_on: []
files_modified:
  - backend/pyproject.toml
  - backend/poetry.lock
  - backend/conftest.py
  - backend/apps/__init__.py
  - backend/apps/core/__init__.py
  - backend/apps/core/tests/__init__.py
  - backend/apps/accounts/__init__.py
  - backend/apps/accounts/tests/__init__.py
  - backend/apps/accounts/tests/test_models.py
  - backend/apps/industries/__init__.py
  - backend/apps/industries/tests/__init__.py
  - backend/apps/industries/tests/test_models.py
  - backend/apps/industries/tests/test_versioning.py
  - backend/apps/submissions/__init__.py
  - backend/apps/submissions/tests/__init__.py
  - backend/apps/submissions/tests/test_models.py
  - backend/apps/submissions/tests/test_immutability.py
  - backend/apps/submissions/tests/test_fsm.py
  - backend/apps/payments/__init__.py
  - backend/apps/payments/tests/__init__.py
  - backend/apps/payments/tests/test_models.py
  - backend/apps/reports/__init__.py
  - backend/apps/reports/tests/__init__.py
  - backend/apps/reports/tests/test_models.py
  - backend/apps/delivery/__init__.py
  - backend/apps/delivery/tests/__init__.py
  - backend/apps/delivery/tests/test_models.py
  - backend/apps/content/__init__.py
  - backend/apps/content/tests/__init__.py
  - backend/apps/content/tests/test_models.py
  - backend/tests/__init__.py
  - backend/tests/test_settings.py
  - backend/tests/test_pdf_fonts.py
  - backend/tests/test_backup.py
  - backend/tests/test_seed.py
autonomous: true
requirements: []
must_haves:
  truths:
    - "pytest-django is installed in Poetry dev group"
    - "backend/conftest.py exists and configures Django test DB"
    - "All test stub files listed in VALIDATION.md exist with xfail markers for unimplemented behaviors"
    - "pytest can collect all tests without import errors"
  artifacts:
    - path: backend/pyproject.toml
      provides: "Poetry manifest with pytest 8, pytest-django 4.9, pytest-cov, factory-boy in [tool.poetry.group.dev.dependencies]; [tool.pytest.ini_options] block with DJANGO_SETTINGS_MODULE=baqsy.settings.dev"
    - path: backend/conftest.py
      provides: "Shared pytest-django configuration and fixtures"
    - path: backend/apps/industries/tests/test_models.py
      provides: "xfail stubs for DATA-01, DATA-02, DATA-03"
    - path: backend/apps/industries/tests/test_versioning.py
      provides: "xfail stubs for DATA-12 (create_new_version + one_active constraint)"
    - path: backend/apps/submissions/tests/test_immutability.py
      provides: "xfail stub for DATA-13 (template_id immutable)"
    - path: backend/apps/submissions/tests/test_fsm.py
      provides: "xfail stubs for DATA-05 FSM transitions"
  key_links:
    - from: backend/pyproject.toml
      to: pytest
      via: "[tool.pytest.ini_options] configures DJANGO_SETTINGS_MODULE"
      pattern: "DJANGO_SETTINGS_MODULE.*baqsy.settings"
    - from: backend/conftest.py
      to: django
      via: "pytest-django plugin uses it for test DB setup"
      pattern: "pytest-django|django_db"
---

<objective>
Wave 0 bootstrap per Nyquist validation strategy: create test infrastructure (pytest, pytest-django, conftest.py, all per-app test stub files with xfail markers) BEFORE any implementation work begins. This gives Plans 01/02/03 a green test harness to flip xfail→pass as they implement requirements.

Purpose: Establishes the <automated> verification backbone for all Phase 1 tasks. Every model/feature task in later plans will have a failing test waiting in this scaffold.

Output: Poetry dev-group with pytest stack, `backend/pyproject.toml` with `[tool.pytest.ini_options]`, `backend/conftest.py`, and 20+ stub test files listed in VALIDATION.md Wave 0 Requirements.
</objective>

<execution_context>
@/Users/a1111/.claude/get-shit-done/workflows/execute-plan.md
@/Users/a1111/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/REQUIREMENTS.md
@.planning/phases/01-infrastructure-data-model/01-CONTEXT.md
@.planning/phases/01-infrastructure-data-model/01-RESEARCH.md
@.planning/phases/01-infrastructure-data-model/01-VALIDATION.md
@CLAUDE.md

<interfaces>
<!-- There is no existing codebase. This is Wave 0 bootstrap. -->
<!-- Test stubs will import from modules that do NOT exist yet — that is intentional. -->
<!-- Stubs MUST use pytest.importorskip or pytest.mark.xfail(strict=False) so they DO NOT error on collection. -->

Canonical pytest-django config block (copy verbatim into backend/pyproject.toml):

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "baqsy.settings.dev"
python_files = ["tests.py", "test_*.py", "*_tests.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-ra --strict-markers"
markers = [
    "slow: marks tests as slow",
    "integration: integration tests requiring services",
]
```

Canonical Poetry dev-group block:

```toml
[tool.poetry.group.dev.dependencies]
pytest = "^8.3"
pytest-django = "^4.9"
pytest-cov = "^5.0"
pytest-mock = "^3.14"
factory-boy = "^3.3"
ruff = "^0.6"
mypy = "^1.11"
django-debug-toolbar = "^4.4"
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 0-1: Create backend/pyproject.toml with Poetry manifest + pytest config</name>
  <read_first>
    - /Users/a1111/Desktop/projects/oplata project/.planning/phases/01-infrastructure-data-model/01-CONTEXT.md (Poetry structure decisions)
    - /Users/a1111/Desktop/projects/oplata project/.planning/phases/01-infrastructure-data-model/01-RESEARCH.md (library versions lines 100-146)
    - /Users/a1111/Desktop/projects/oplata project/CLAUDE.md (stack requirements)
  </read_first>
  <files>backend/pyproject.toml</files>
  <action>
Create `backend/pyproject.toml` as a complete Poetry 1.8 manifest for the Django backend. The file MUST contain exactly these sections:

1. `[tool.poetry]` block:
```toml
[tool.poetry]
name = "baqsy-backend"
version = "0.1.0"
description = "Baqsy System — Django backend (business audit SaaS)"
authors = ["Baqsy Team"]
readme = "README.md"
package-mode = false
```

2. `[tool.poetry.dependencies]` — main group with these EXACT versions from RESEARCH.md:
```toml
[tool.poetry.dependencies]
python = "^3.12"
django = "5.2"
django-fsm-2 = "4.2.4"
psycopg2-binary = "2.9.10"
django-storages = {version = "1.14.6", extras = ["s3"]}
boto3 = ">=1.35"
django-environ = "^0.11"
weasyprint = "68.1"
gunicorn = "23.0.0"
celery = "5.6.3"
django-celery-beat = "2.7.0"
redis = "5.3.0"
django-cors-headers = "4.6.0"
structlog = "25.5.0"
django-structlog = "10.0.0"
djangorestframework = "3.17.1"
```

NOTE: DRF (djangorestframework 3.17.1) is included now for settings INSTALLED_APPS convenience even though endpoints are Phase 2.

3. `[tool.poetry.group.dev.dependencies]` — dev group (copy from interfaces block above).

4. `[tool.poetry.group.prod.dependencies]`:
```toml
[tool.poetry.group.prod.dependencies]
gunicorn = "23.0.0"
```

5. `[build-system]`:
```toml
[build-system]
requires = ["poetry-core>=1.8.0"]
build-backend = "poetry.core.masonry.api"
```

6. `[tool.pytest.ini_options]` — copy verbatim from interfaces block above.

7. `[tool.ruff]`:
```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "B", "UP", "DJ"]
ignore = ["E501"]
```

Do NOT run `poetry install` in this task — the Docker build in Plan 01 will handle that. Plan 01 will generate poetry.lock when Dockerfile builder stage runs. This task only creates the manifest file.

Why `django-environ = "^0.11"` (not 2.x as RESEARCH.md suggests): django-environ latest stable on PyPI is 0.11.x (the "^0.11" version comment in RESEARCH.md was a loose note, PyPI reality is 0.11). Pin `^0.11`.
  </action>
  <verify>
    <automated>test -f backend/pyproject.toml && grep -q 'django-fsm-2 = "4.2.4"' backend/pyproject.toml && grep -q 'DJANGO_SETTINGS_MODULE = "baqsy.settings.dev"' backend/pyproject.toml && grep -q 'pytest-django' backend/pyproject.toml</automated>
  </verify>
  <acceptance_criteria>
    - `backend/pyproject.toml` exists
    - File contains literal string `django = "5.2"`
    - File contains literal string `django-fsm-2 = "4.2.4"`
    - File contains literal string `weasyprint = "68.1"`
    - File contains literal string `celery = "5.6.3"`
    - File contains `[tool.pytest.ini_options]` section with `DJANGO_SETTINGS_MODULE = "baqsy.settings.dev"`
    - File contains `[tool.poetry.group.dev.dependencies]` with `pytest-django` entry
    - File contains `[build-system]` with `poetry-core>=1.8.0`
    - TOML parses without error: `python -c "import tomllib; tomllib.load(open('backend/pyproject.toml','rb'))"` exits 0
  </acceptance_criteria>
  <done>backend/pyproject.toml is a valid Poetry 1.8 manifest ready for `poetry install` with exact pinned versions from RESEARCH.md and pytest configured for Django test DB.</done>
</task>

<task type="auto">
  <name>Task 0-2: Create conftest.py and app package __init__ files</name>
  <read_first>
    - /Users/a1111/Desktop/projects/oplata project/.planning/phases/01-infrastructure-data-model/01-VALIDATION.md (Wave 0 Requirements section lines 70-86)
    - /Users/a1111/Desktop/projects/oplata project/.planning/phases/01-infrastructure-data-model/01-CONTEXT.md (apps/ structure lines 33-46)
  </read_first>
  <files>
backend/conftest.py
backend/apps/__init__.py
backend/apps/core/__init__.py
backend/apps/core/tests/__init__.py
backend/apps/accounts/__init__.py
backend/apps/accounts/tests/__init__.py
backend/apps/industries/__init__.py
backend/apps/industries/tests/__init__.py
backend/apps/submissions/__init__.py
backend/apps/submissions/tests/__init__.py
backend/apps/payments/__init__.py
backend/apps/payments/tests/__init__.py
backend/apps/reports/__init__.py
backend/apps/reports/tests/__init__.py
backend/apps/delivery/__init__.py
backend/apps/delivery/tests/__init__.py
backend/apps/content/__init__.py
backend/apps/content/tests/__init__.py
backend/tests/__init__.py
  </files>
  <action>
Create the Python package skeleton for all 8 Django apps + the project-level tests package. Each `__init__.py` is an empty file (zero bytes) EXCEPT where noted below.

Apps to create (8 total, matching CONTEXT.md decision): `core`, `accounts`, `industries`, `submissions`, `payments`, `reports`, `delivery`, `content`.

For EACH app create:
- `backend/apps/{app}/__init__.py` — empty file
- `backend/apps/{app}/tests/__init__.py` — empty file

Also create:
- `backend/apps/__init__.py` — empty file
- `backend/tests/__init__.py` — empty file (project-level integration tests package)

Create `backend/conftest.py` with EXACTLY this content (pytest-django picks this up automatically):

```python
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
```

This gives downstream plans a stable import target. The `db_empty` fixture is a convenience alias; `frozen_now` is a placeholder.
  </action>
  <verify>
    <automated>test -f backend/conftest.py && test -f backend/apps/__init__.py && test -f backend/apps/industries/tests/__init__.py && test -f backend/apps/submissions/tests/__init__.py && test -f backend/apps/payments/tests/__init__.py && test -f backend/apps/accounts/tests/__init__.py && test -f backend/apps/reports/tests/__init__.py && test -f backend/apps/delivery/tests/__init__.py && test -f backend/apps/content/tests/__init__.py && test -f backend/apps/core/tests/__init__.py && test -f backend/tests/__init__.py && grep -q "def db_empty" backend/conftest.py</automated>
  </verify>
  <acceptance_criteria>
    - `backend/conftest.py` exists and contains literal `def db_empty(db):`
    - All 8 app package directories have `__init__.py` and `tests/__init__.py`
    - `backend/apps/__init__.py` exists
    - `backend/tests/__init__.py` exists
    - `find backend/apps -name tests -type d | wc -l` outputs `8`
    - `python -c "import ast; ast.parse(open('backend/conftest.py').read())"` exits 0
  </acceptance_criteria>
  <done>Python package skeleton for all 8 apps exists; conftest.py provides shared pytest-django fixtures; pytest can later collect tests from these packages.</done>
</task>

<task type="auto">
  <name>Task 0-3: Create xfail test stubs for all DATA + INFRA requirements</name>
  <read_first>
    - /Users/a1111/Desktop/projects/oplata project/.planning/phases/01-infrastructure-data-model/01-VALIDATION.md (full Per-Task Verification Map)
    - /Users/a1111/Desktop/projects/oplata project/.planning/REQUIREMENTS.md (DATA-01..13 lines 19-33)
    - /Users/a1111/Desktop/projects/oplata project/.planning/phases/01-infrastructure-data-model/01-RESEARCH.md (Phase Requirements → Test Map section)
  </read_first>
  <files>
backend/apps/industries/tests/test_models.py
backend/apps/industries/tests/test_versioning.py
backend/apps/accounts/tests/test_models.py
backend/apps/submissions/tests/test_models.py
backend/apps/submissions/tests/test_immutability.py
backend/apps/submissions/tests/test_fsm.py
backend/apps/payments/tests/test_models.py
backend/apps/reports/tests/test_models.py
backend/apps/delivery/tests/test_models.py
backend/apps/content/tests/test_models.py
backend/tests/test_settings.py
backend/tests/test_pdf_fonts.py
backend/tests/test_backup.py
backend/tests/test_seed.py
  </files>
  <action>
Create test stub files. EVERY test function in these stubs MUST be marked `@pytest.mark.xfail(strict=False, reason="Phase 1 Wave 0 stub — implementation pending in Plan 01/02/03")`. The tests should import from modules that do not yet exist and reference the behavior they WILL test after implementation.

CRITICAL: Use `importorskip` or guard imports with try/except at the module level so pytest COLLECTION succeeds even though the target modules don't exist. Pattern for every test file:

```python
"""Phase 1 Wave 0 stub — {requirement IDs}."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.xfail(
    strict=False,
    reason="Phase 1 Wave 0 stub — implementation pending",
)
```

Use module-level `pytestmark` to apply xfail to every test in the file — no need to decorate each function individually. Guard all imports inside test functions (not at module top) so collection never fails.

### File: `backend/apps/industries/tests/test_models.py` (DATA-01, DATA-02, DATA-03)

```python
"""Phase 1 Wave 0 stub — DATA-01, DATA-02, DATA-03."""
from __future__ import annotations
import pytest

pytestmark = pytest.mark.xfail(strict=False, reason="Phase 1 Wave 0 stub")


@pytest.mark.django_db
def test_industry_model():
    from apps.industries.models import Industry
    obj = Industry.objects.create(name="Ритейл", slug="retail", is_active=True)
    assert obj.pk is not None
    assert obj.name == "Ритейл"


@pytest.mark.django_db
def test_questionnaire_template_model():
    from apps.industries.models import Industry, QuestionnaireTemplate
    ind = Industry.objects.create(name="IT", slug="it")
    tpl = QuestionnaireTemplate.objects.create(industry=ind, version=1, name="IT v1", is_active=True)
    assert tpl.version == 1
    assert tpl.is_active is True


@pytest.mark.django_db
def test_question_model():
    from apps.industries.models import Industry, QuestionnaireTemplate, Question
    ind = Industry.objects.create(name="F&B", slug="fnb")
    tpl = QuestionnaireTemplate.objects.create(industry=ind, version=1, name="F&B v1")
    q = Question.objects.create(
        template=tpl, order=1, text="Your revenue?",
        field_type=Question.FieldType.NUMBER, required=True, block=Question.Block.A,
    )
    assert q.order == 1
    assert q.field_type == "number"
```

### File: `backend/apps/industries/tests/test_versioning.py` (DATA-12)

```python
"""Phase 1 Wave 0 stub — DATA-12 (template versioning invariant)."""
from __future__ import annotations
import pytest
from django.db import IntegrityError

pytestmark = pytest.mark.xfail(strict=False, reason="Phase 1 Wave 0 stub")


@pytest.mark.django_db
def test_create_new_version_deactivates_old():
    from apps.industries.models import Industry, QuestionnaireTemplate
    ind = Industry.objects.create(name="Услуги", slug="services")
    v1 = QuestionnaireTemplate.objects.create(industry=ind, version=1, is_active=True, name="v1")
    v2 = QuestionnaireTemplate.create_new_version(industry_id=ind.id, name="v2")
    v1.refresh_from_db()
    assert v1.is_active is False
    assert v2.version == 2


@pytest.mark.django_db
def test_only_one_active_per_industry_constraint():
    from apps.industries.models import Industry, QuestionnaireTemplate
    ind = Industry.objects.create(name="Производство", slug="mfg")
    QuestionnaireTemplate.objects.create(industry=ind, version=1, is_active=True, name="v1")
    with pytest.raises(IntegrityError):
        QuestionnaireTemplate.objects.create(industry=ind, version=2, is_active=True, name="v2-dup")
```

### File: `backend/apps/accounts/tests/test_models.py` (DATA-04)

```python
"""Phase 1 Wave 0 stub — DATA-04 (ClientProfile)."""
from __future__ import annotations
import pytest

pytestmark = pytest.mark.xfail(strict=False, reason="Phase 1 Wave 0 stub")


@pytest.mark.django_db
def test_client_profile_model():
    from apps.accounts.models import ClientProfile
    from apps.industries.models import Industry
    ind = Industry.objects.create(name="Ритейл", slug="retail-cp")
    cp = ClientProfile.objects.create(
        telegram_id=123456789, name="Иван", company="ООО Ромашка",
        phone_wa="+77001234567", city="Алматы", industry=ind,
    )
    assert cp.telegram_id == 123456789
    assert cp.name == "Иван"


@pytest.mark.django_db
def test_base_user_email_login():
    from apps.accounts.models import BaseUser
    u = BaseUser.objects.create_user(email="admin@baqsy.kz", password="s3cret")
    assert u.email == "admin@baqsy.kz"
    assert u.check_password("s3cret")
```

### File: `backend/apps/submissions/tests/test_models.py` (DATA-05, DATA-06)

```python
"""Phase 1 Wave 0 stub — DATA-05 (Submission), DATA-06 (Answer)."""
from __future__ import annotations
import pytest

pytestmark = pytest.mark.xfail(strict=False, reason="Phase 1 Wave 0 stub")


@pytest.mark.django_db
def test_submission_model():
    from apps.submissions.models import Submission, SubmissionStatus
    # Relies on factories that do not yet exist in Phase 1 Wave 0.
    assert SubmissionStatus.CREATED == "created"


@pytest.mark.django_db
def test_answer_model_jsonb():
    from apps.submissions.models import Answer
    # Answer.value is JSONB — shape depends on question.field_type.
    # Full test requires full fixture graph; stub asserts model exists.
    assert Answer._meta.get_field("value").get_internal_type() == "JSONField"
```

### File: `backend/apps/submissions/tests/test_immutability.py` (DATA-13)

```python
"""Phase 1 Wave 0 stub — DATA-13 (Submission.template_id immutable)."""
from __future__ import annotations
import pytest
from django.core.exceptions import ValidationError

pytestmark = pytest.mark.xfail(strict=False, reason="Phase 1 Wave 0 stub")


@pytest.mark.django_db
def test_submission_template_id_cannot_change():
    from apps.accounts.models import ClientProfile
    from apps.industries.models import Industry, QuestionnaireTemplate
    from apps.submissions.models import Submission

    ind = Industry.objects.create(name="IT", slug="it-imm")
    tpl_v1 = QuestionnaireTemplate.objects.create(industry=ind, version=1, name="v1")
    tpl_v2 = QuestionnaireTemplate.objects.create(industry=ind, version=2, name="v2")
    client = ClientProfile.objects.create(
        telegram_id=42, name="A", company="B", phone_wa="+7", city="C", industry=ind,
    )
    sub = Submission.objects.create(client=client, template=tpl_v1)
    sub.template = tpl_v2
    with pytest.raises(ValidationError):
        sub.save()
```

### File: `backend/apps/submissions/tests/test_fsm.py` (DATA-05 FSM)

```python
"""Phase 1 Wave 0 stub — Submission FSM transitions."""
from __future__ import annotations
import pytest

pytestmark = pytest.mark.xfail(strict=False, reason="Phase 1 Wave 0 stub")


@pytest.mark.django_db
def test_valid_transition_created_to_in_progress_basic():
    from apps.submissions.models import Submission
    # Instance creation + transition call — needs full fixture graph.
    assert hasattr(Submission, "start_basic")


@pytest.mark.django_db
def test_invalid_transition_raises():
    from django_fsm import TransitionNotAllowed
    from apps.submissions.models import Submission
    assert TransitionNotAllowed is not None
```

### File: `backend/apps/payments/tests/test_models.py` (DATA-07, DATA-08)

```python
"""Phase 1 Wave 0 stub — DATA-07 (Tariff), DATA-08 (Payment)."""
from __future__ import annotations
import pytest
from django.db import IntegrityError

pytestmark = pytest.mark.xfail(strict=False, reason="Phase 1 Wave 0 stub")


@pytest.mark.django_db
def test_tariff_model():
    from apps.payments.models import Tariff
    t = Tariff.objects.create(code="ashide_1", title="Ashıde 1", price_kzt=45000, is_active=True)
    assert t.price_kzt == 45000


@pytest.mark.django_db
def test_payment_unique_transaction_id():
    from apps.payments.models import Payment
    # Requires Submission + Tariff fixtures. Stub asserts unique constraint exists.
    field = Payment._meta.get_field("transaction_id")
    assert field.unique is True
```

### File: `backend/apps/reports/tests/test_models.py` (DATA-09)

```python
"""Phase 1 Wave 0 stub — DATA-09 (AuditReport)."""
from __future__ import annotations
import pytest

pytestmark = pytest.mark.xfail(strict=False, reason="Phase 1 Wave 0 stub")


@pytest.mark.django_db
def test_audit_report_model():
    from apps.reports.models import AuditReport
    assert AuditReport._meta.get_field("admin_text") is not None
    assert AuditReport._meta.get_field("pdf_url") is not None
```

### File: `backend/apps/delivery/tests/test_models.py` (DATA-10)

```python
"""Phase 1 Wave 0 stub — DATA-10 (DeliveryLog)."""
from __future__ import annotations
import pytest

pytestmark = pytest.mark.xfail(strict=False, reason="Phase 1 Wave 0 stub")


@pytest.mark.django_db
def test_delivery_log_model():
    from apps.delivery.models import DeliveryLog
    assert DeliveryLog._meta.get_field("channel") is not None
    assert DeliveryLog._meta.get_field("status") is not None
```

### File: `backend/apps/content/tests/test_models.py` (DATA-11)

```python
"""Phase 1 Wave 0 stub — DATA-11 (ContentBlock)."""
from __future__ import annotations
import pytest

pytestmark = pytest.mark.xfail(strict=False, reason="Phase 1 Wave 0 stub")


@pytest.mark.django_db
def test_content_block_model():
    from apps.content.models import ContentBlock
    cb = ContentBlock.objects.create(key="landing.hero.title", value="<h1>Baqsy</h1>")
    assert cb.key == "landing.hero.title"
```

### File: `backend/tests/test_settings.py` (INFRA-03)

```python
"""Phase 1 Wave 0 stub — INFRA-03 (.env-driven config)."""
from __future__ import annotations
import pytest

pytestmark = pytest.mark.xfail(strict=False, reason="Phase 1 Wave 0 stub")


def test_env_vars_loaded():
    from django.conf import settings
    assert settings.DATABASES["default"]["ENGINE"].endswith("postgresql")
    assert "redis" in settings.CELERY_BROKER_URL
```

### File: `backend/tests/test_pdf_fonts.py` (INFRA-05)

```python
"""Phase 1 Wave 0 stub — INFRA-05 (Cyrillic fonts in Docker image)."""
from __future__ import annotations
import shutil
import subprocess
import pytest

pytestmark = pytest.mark.xfail(strict=False, reason="Phase 1 Wave 0 stub")


def test_cyrillic_fonts_available():
    if shutil.which("fc-list") is None:
        pytest.skip("fc-list not available in this environment")
    out = subprocess.check_output(["fc-list"], text=True)
    assert "Liberation" in out or "DejaVu" in out
```

### File: `backend/tests/test_backup.py` (INFRA-06)

```python
"""Phase 1 Wave 0 stub — INFRA-06 (PG backup to MinIO)."""
from __future__ import annotations
import pytest

pytestmark = pytest.mark.xfail(strict=False, reason="Phase 1 Wave 0 stub")


def test_pg_dump_to_minio(mocker):
    # Will be implemented in Plan 03 — mocks pg_dump subprocess + mc pipe.
    assert True is False, "Not implemented"
```

### File: `backend/tests/test_seed.py` (DATA-01..07 seed)

```python
"""Phase 1 Wave 0 stub — seed_initial management command."""
from __future__ import annotations
import pytest
from django.core.management import call_command

pytestmark = pytest.mark.xfail(strict=False, reason="Phase 1 Wave 0 stub")


@pytest.mark.django_db
def test_seed_initial_idempotent():
    call_command("seed_initial")
    call_command("seed_initial")  # second run must not raise


@pytest.mark.django_db
def test_seed_creates_baseline_data():
    from apps.industries.models import Industry
    from apps.payments.models import Tariff
    call_command("seed_initial")
    assert Industry.objects.count() >= 5
    assert Tariff.objects.filter(code="ashide_1").exists()
    assert Tariff.objects.filter(code="ashide_2").exists()
    assert Tariff.objects.filter(code="upsell").exists()
```

All 14 files must be created in this single task. Each file has a module-level `pytestmark = pytest.mark.xfail(...)` so every test starts as an EXPECTED FAILURE. When Plans 01/02/03 implement the corresponding feature, they simply REMOVE the `pytestmark` line (or flip to `xpass` strict) and the test becomes a green passing test — this is the Nyquist feedback loop.
  </action>
  <verify>
    <automated>test -f backend/apps/industries/tests/test_models.py && test -f backend/apps/industries/tests/test_versioning.py && test -f backend/apps/accounts/tests/test_models.py && test -f backend/apps/submissions/tests/test_models.py && test -f backend/apps/submissions/tests/test_immutability.py && test -f backend/apps/submissions/tests/test_fsm.py && test -f backend/apps/payments/tests/test_models.py && test -f backend/apps/reports/tests/test_models.py && test -f backend/apps/delivery/tests/test_models.py && test -f backend/apps/content/tests/test_models.py && test -f backend/tests/test_settings.py && test -f backend/tests/test_pdf_fonts.py && test -f backend/tests/test_backup.py && test -f backend/tests/test_seed.py && grep -l "pytestmark = pytest.mark.xfail" backend/apps/industries/tests/test_models.py && grep -l "pytestmark = pytest.mark.xfail" backend/apps/submissions/tests/test_immutability.py</automated>
  </verify>
  <acceptance_criteria>
    - All 14 test files listed in files exist
    - Every test file contains literal `pytestmark = pytest.mark.xfail(`
    - `backend/apps/industries/tests/test_models.py` contains `def test_industry_model()`, `def test_questionnaire_template_model()`, `def test_question_model()`
    - `backend/apps/industries/tests/test_versioning.py` contains `def test_create_new_version_deactivates_old()` and `def test_only_one_active_per_industry_constraint()`
    - `backend/apps/submissions/tests/test_immutability.py` contains `def test_submission_template_id_cannot_change()`
    - `backend/apps/submissions/tests/test_fsm.py` contains `def test_invalid_transition_raises()`
    - `backend/apps/payments/tests/test_models.py` contains `def test_payment_unique_transaction_id()`
    - Every test file parses as valid Python: `python -c "import ast; [ast.parse(open(f).read()) for f in ['backend/apps/industries/tests/test_models.py', 'backend/apps/submissions/tests/test_immutability.py']]"` exits 0
  </acceptance_criteria>
  <done>All 14 test stub files exist with module-level xfail markers. Each test targets a specific INFRA/DATA requirement from VALIDATION.md. Downstream plans flip xfail→pass as they implement features, giving Nyquist-compliant feedback per task commit.</done>
</task>

</tasks>

<verification>
After all tasks complete, verify Wave 0 is ready for downstream plans:

```bash
# 1. Pyproject is valid TOML with required sections
python -c "import tomllib; d = tomllib.load(open('backend/pyproject.toml','rb')); assert 'pytest' in d['tool']; assert 'poetry' in d['tool']"

# 2. Count of test stub files
find backend -name "test_*.py" -type f | wc -l  # expect >= 14

# 3. All test files are valid Python
find backend -name "test_*.py" -exec python -c "import ast; ast.parse(open('{}').read())" \;

# 4. Every app has tests/__init__.py
for app in core accounts industries submissions payments reports delivery content; do
  test -f "backend/apps/$app/tests/__init__.py" || { echo "MISSING: $app"; exit 1; }
done
```
</verification>

<success_criteria>
- `backend/pyproject.toml` is a valid Poetry 1.8 manifest with pinned versions from RESEARCH.md and `[tool.pytest.ini_options]` pointing at `baqsy.settings.dev`
- `backend/conftest.py` exists with shared pytest-django fixtures
- 8 Django app package directories exist under `backend/apps/` each with `tests/__init__.py`
- 14 test stub files exist, each with module-level `pytest.mark.xfail`
- All files are valid Python / TOML (parseable)
- NO Django settings files, NO models, NO Docker yet — that's Plans 01/02/03
- Plans 01/02/03 can immediately start using this scaffold (import paths stable)
</success_criteria>

<output>
After completion, create `.planning/phases/01-infrastructure-data-model/01-00-SUMMARY.md`
</output>
