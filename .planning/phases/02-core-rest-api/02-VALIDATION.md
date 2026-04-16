---
phase: 2
slug: core-rest-api
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-16
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + pytest-django 4.9 + DRF APIClient |
| **Config file** | `backend/pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `cd backend && python -m pytest -x --no-header -q` |
| **Full suite command** | `cd backend && python -m pytest --cov=apps --cov-report=term-missing` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest <affected_test_file> -x -q`
- **After every plan wave:** Run `python -m pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 45 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | Status |
|---------|------|------|-------------|-----------|-------------------|--------|
| 2-W0 | 00 | 0 | — | infra | `python -m pytest --collect-only` | ⬜ pending |
| 2-01-01 | 01 | 1 | API-01 | integration | `pytest apps/accounts/tests/test_api.py::test_jwt_auth` | ⬜ pending |
| 2-01-02 | 01 | 1 | API-02 | integration | `pytest apps/accounts/tests/test_api.py::test_session_auth` | ⬜ pending |
| 2-01-03 | 01 | 1 | API-10 | integration | `pytest apps/accounts/tests/test_deeplink.py::test_create_deeplink` | ⬜ pending |
| 2-01-04 | 01 | 1 | API-11 | integration | `pytest apps/accounts/tests/test_deeplink.py::test_exchange_deeplink` | ⬜ pending |
| 2-02-01 | 02 | 1 | API-03 | integration | `pytest apps/accounts/tests/test_onboarding.py` | ⬜ pending |
| 2-02-02 | 02 | 1 | API-04 | integration | `pytest apps/industries/tests/test_api.py` | ⬜ pending |
| 2-03-01 | 03 | 2 | API-05 | integration | `pytest apps/submissions/tests/test_api.py::test_create_submission` | ⬜ pending |
| 2-03-02 | 03 | 2 | API-06 | integration | `pytest apps/submissions/tests/test_api.py::test_next_question` | ⬜ pending |
| 2-03-03 | 03 | 2 | API-07 | integration | `pytest apps/submissions/tests/test_api.py::test_save_answer` | ⬜ pending |
| 2-03-04 | 03 | 2 | API-08 | integration | `pytest apps/submissions/tests/test_api.py::test_complete_submission` | ⬜ pending |
| 2-03-05 | 03 | 2 | API-09 | integration | `pytest apps/submissions/tests/test_api.py::test_get_submission_status` | ⬜ pending |

---

## Wave 0 Requirements

- [ ] `djangorestframework-simplejwt` added to pyproject.toml
- [ ] `rest_framework` and `rest_framework_simplejwt` in INSTALLED_APPS
- [ ] DRF settings in base.py (auth classes, pagination, renderers)
- [ ] SIMPLE_JWT settings in base.py
- [ ] ClientProfile.user OneToOneField migration (if needed per research)
- [ ] Test factory files for ClientProfile, Industry, Submission, etc.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| JWT token expiry after 1h | API-01 | Requires waiting 1h or mocking time | Use `freezegun` in tests to verify |

---

## Validation Sign-Off

- [ ] All tasks have automated verify
- [ ] Sampling continuity maintained
- [ ] Wave 0 covers all MISSING references
- [ ] Feedback latency < 45s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
