---
phase: 1
slug: infrastructure-data-model
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-15
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + pytest-django 4.9 |
| **Config file** | `backend/pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `docker-compose exec -T web pytest -x --no-header -q` |
| **Full suite command** | `docker-compose exec -T web pytest --cov=apps --cov-report=term-missing` |
| **Estimated runtime** | ~30 seconds (quick), ~90 seconds (full) |

---

## Sampling Rate

- **After every task commit:** Run `docker-compose exec -T web pytest <affected_test_file> -x -q`
- **After every plan wave:** Run `docker-compose exec -T web pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green + `docker-compose up -d` must bring all containers healthy
- **Max feedback latency:** 30 seconds per task, 90 seconds per wave

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-W0 | 01 | 0 | — | infra | `test -f backend/pyproject.toml && test -f backend/conftest.py` | ❌ W0 | ⬜ pending |
| 1-01-01 | 01 | 1 | INFRA-01 | smoke | `docker-compose config --quiet` | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 1 | INFRA-02 | smoke | `docker-compose up -d && docker-compose ps --format json \| jq -e '.[] \| select(.Health != "healthy") \| empty'` | ❌ W0 | ⬜ pending |
| 1-01-03 | 01 | 1 | INFRA-03 | unit | `pytest tests/test_settings.py::test_env_vars_loaded` | ❌ W0 | ⬜ pending |
| 1-01-04 | 01 | 1 | INFRA-04 | smoke | `docker-compose exec -T web python manage.py migrate --check` | ❌ W0 | ⬜ pending |
| 1-01-05 | 01 | 2 | INFRA-05 | unit | `pytest tests/test_pdf_fonts.py::test_cyrillic_fonts_available` | ❌ W0 | ⬜ pending |
| 1-01-06 | 01 | 2 | INFRA-06 | integration | `pytest tests/test_backup.py::test_pg_dump_to_minio` | ❌ W0 | ⬜ pending |
| 1-01-07 | 01 | 2 | INFRA-07 | doc | `test -f README.md && grep -q 'Deployment' README.md` | ❌ W0 | ⬜ pending |
| 1-02-01 | 02 | 1 | DATA-01 | unit | `pytest apps/industries/tests/test_models.py::test_industry_model` | ❌ W0 | ⬜ pending |
| 1-02-02 | 02 | 1 | DATA-02 | unit | `pytest apps/industries/tests/test_models.py::test_questionnaire_template_model` | ❌ W0 | ⬜ pending |
| 1-02-03 | 02 | 1 | DATA-03 | unit | `pytest apps/industries/tests/test_models.py::test_question_model` | ❌ W0 | ⬜ pending |
| 1-02-04 | 02 | 1 | DATA-04 | unit | `pytest apps/accounts/tests/test_models.py::test_client_profile_model` | ❌ W0 | ⬜ pending |
| 1-02-05 | 02 | 2 | DATA-05 | unit | `pytest apps/submissions/tests/test_models.py::test_submission_model` | ❌ W0 | ⬜ pending |
| 1-02-06 | 02 | 2 | DATA-06 | unit | `pytest apps/submissions/tests/test_models.py::test_answer_model` | ❌ W0 | ⬜ pending |
| 1-02-07 | 02 | 2 | DATA-07 | unit | `pytest apps/payments/tests/test_models.py::test_tariff_model` | ❌ W0 | ⬜ pending |
| 1-02-08 | 02 | 2 | DATA-08 | unit | `pytest apps/payments/tests/test_models.py::test_payment_unique_transaction_id` | ❌ W0 | ⬜ pending |
| 1-02-09 | 02 | 2 | DATA-09 | unit | `pytest apps/reports/tests/test_models.py::test_audit_report_model` | ❌ W0 | ⬜ pending |
| 1-02-10 | 02 | 2 | DATA-10 | unit | `pytest apps/delivery/tests/test_models.py::test_delivery_log_model` | ❌ W0 | ⬜ pending |
| 1-02-11 | 02 | 2 | DATA-11 | unit | `pytest apps/content/tests/test_models.py::test_content_block_model` | ❌ W0 | ⬜ pending |
| 1-02-12 | 02 | 3 | DATA-12 | integration | `pytest apps/industries/tests/test_versioning.py::test_create_new_version_deactivates_old` | ❌ W0 | ⬜ pending |
| 1-02-13 | 02 | 3 | DATA-12 | integration | `pytest apps/industries/tests/test_versioning.py::test_only_one_active_per_industry_constraint` | ❌ W0 | ⬜ pending |
| 1-02-14 | 02 | 3 | DATA-13 | integration | `pytest apps/submissions/tests/test_immutability.py::test_submission_template_id_cannot_change` | ❌ W0 | ⬜ pending |
| 1-03-01 | 03 | 3 | INFRA-04+ | integration | `pytest tests/test_seed.py::test_seed_initial_idempotent` | ❌ W0 | ⬜ pending |
| 1-03-02 | 03 | 3 | DATA-01..07 | integration | `pytest tests/test_seed.py::test_seed_creates_baseline_data` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/pyproject.toml` — Poetry manifest with pytest, pytest-django, pytest-cov in dev group
- [ ] `backend/conftest.py` — shared pytest-django fixtures (db, client, tmp_minio_bucket)
- [ ] `backend/pytest.ini` or `[tool.pytest.ini_options]` — `DJANGO_SETTINGS_MODULE=baqsy.settings.dev`, `python_files = tests.py test_*.py *_tests.py`
- [ ] `backend/apps/industries/tests/__init__.py`, `backend/apps/industries/tests/test_models.py`, `backend/apps/industries/tests/test_versioning.py` — stub files with xfail markers for DATA-01..03, DATA-12
- [ ] `backend/apps/accounts/tests/__init__.py`, `backend/apps/accounts/tests/test_models.py` — stub for DATA-04
- [ ] `backend/apps/submissions/tests/__init__.py`, `backend/apps/submissions/tests/test_models.py`, `backend/apps/submissions/tests/test_immutability.py` — stubs for DATA-05, DATA-06, DATA-13
- [ ] `backend/apps/payments/tests/__init__.py`, `backend/apps/payments/tests/test_models.py` — stubs for DATA-07, DATA-08
- [ ] `backend/apps/reports/tests/__init__.py`, `backend/apps/reports/tests/test_models.py` — stub for DATA-09
- [ ] `backend/apps/delivery/tests/__init__.py`, `backend/apps/delivery/tests/test_models.py` — stub for DATA-10
- [ ] `backend/apps/content/tests/__init__.py`, `backend/apps/content/tests/test_models.py` — stub for DATA-11
- [ ] `backend/tests/__init__.py`, `backend/tests/test_settings.py` — stubs for env loading (INFRA-03)
- [ ] `backend/tests/test_pdf_fonts.py` — stub: uses `fontconfig` subprocess to verify Cyrillic fonts (INFRA-05)
- [ ] `backend/tests/test_backup.py` — stub: mocks `pg_dump` and minio SDK (INFRA-06)
- [ ] `backend/tests/test_seed.py` — stub for seed_initial command (DATA-01..07)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Фактическое поднятие stack'а на чистой машине | INFRA-01, INFRA-02 | Требует чистого окружения, не воспроизводится внутри контейнера | `git clone <repo> && cd baqsy-system && cp .env.example .env && docker-compose up -d && docker-compose ps` |
| Доступ к http://localhost/admin/ после миграций и seed | INFRA-04, DATA-01..07 | Требует браузера и визуального подтверждения | После `docker-compose up -d` открыть http://localhost/admin/, войти с seeded superuser, убедиться что видны 5 отраслей и 3 тарифа |
| Deployment runbook за ≤2 часа | INFRA-07 | Требует таймированной реальной попытки на новом VPS | Выделить чистый Ubuntu 24.04 VPS, засечь время от клонирования до рабочего admin |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 90s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
