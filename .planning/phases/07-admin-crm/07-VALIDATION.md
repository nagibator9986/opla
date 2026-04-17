---
phase: 7
slug: admin-crm
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-17
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x + Django test client |
| **Config file** | backend/pyproject.toml [tool.pytest.ini_options] |
| **Quick run command** | `docker-compose exec web pytest apps/dashboard/ -x -q` |
| **Full suite command** | `docker-compose exec web pytest apps/dashboard/ apps/reports/ apps/submissions/ apps/industries/ apps/content/ apps/payments/ -x -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `docker-compose exec web pytest apps/dashboard/ -x -q`
- **After every plan wave:** Run full suite command
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 0 | CRM-10 | unit | `pytest apps/dashboard/tests/test_axes.py -x` | ❌ W0 | ⬜ pending |
| 07-01-02 | 01 | 0 | CRM-01 | unit | `pytest apps/dashboard/tests/test_dashboard.py -x` | ❌ W0 | ⬜ pending |
| 07-02-01 | 02 | 1 | CRM-01, CRM-02 | integration | `pytest apps/dashboard/tests/test_dashboard.py -x` | ❌ W0 | ⬜ pending |
| 07-02-02 | 02 | 1 | CRM-03, CRM-04 | integration | `pytest apps/submissions/tests/test_admin.py -x` | ❌ W0 | ⬜ pending |
| 07-03-01 | 03 | 2 | CRM-05, CRM-06, CRM-07 | integration | `pytest apps/industries/tests/test_admin.py -x` | ❌ W0 | ⬜ pending |
| 07-03-02 | 03 | 2 | CRM-08 | unit | `pytest apps/payments/tests/test_admin.py -x` | ❌ W0 | ⬜ pending |
| 07-03-03 | 03 | 2 | CRM-09 | unit | `pytest apps/content/tests/test_admin.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/apps/dashboard/tests/test_dashboard.py` — stubs for CRM-01, CRM-02
- [ ] `backend/apps/dashboard/tests/test_axes.py` — stubs for CRM-10
- [ ] `backend/apps/submissions/tests/test_admin.py` — stubs for CRM-03, CRM-04
- [ ] `backend/apps/industries/tests/test_admin.py` — stubs for CRM-05, CRM-06, CRM-07
- [ ] `backend/apps/payments/tests/test_admin.py` — stubs for CRM-08
- [ ] `backend/apps/content/tests/test_admin.py` — stubs for CRM-09
- [ ] `backend/baqsy/settings/test.py` — test settings with AXES_ENABLED=False

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Dashboard фильтры без перезагрузки (HTMX) | CRM-02 | Requires browser JS execution | Open admin dashboard, apply industry filter, verify page does not reload |
| CKEditor WYSIWYG rendering | CRM-09 | Requires browser | Open ContentBlock change form, verify CKEditor widget loads |
| Drag-n-drop вопросов | CRM-07 | Requires browser interaction | Open QuestionnaireTemplate, drag question, verify order persists |
| «Подтвердить и отправить» triggers Celery | CRM-04 | Requires Celery worker | Click approve in admin, verify PDF generation starts in worker logs |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
