---
phase: 6
slug: pdf-generation-delivery
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-17
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.3 + pytest-django 4.9 |
| **Config file** | `backend/pyproject.toml` — `[tool.pytest.ini_options]` |
| **Quick run command** | `docker-compose exec web pytest apps/reports/ apps/delivery/ -x -q` |
| **Full suite command** | `docker-compose exec web pytest -x -q` |
| **Estimated runtime** | ~20 seconds |

---

## Sampling Rate

- **After every task commit:** Run `docker-compose exec web pytest apps/reports/ apps/delivery/ -x -q`
- **After every plan wave:** Run `docker-compose exec web pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | PDF-01..PDF-07 | unit | `pytest apps/reports/tests/ -x -q` | ❌ W0 | ⬜ pending |
| 06-01-02 | 01 | 1 | DLV-01..DLV-06 | unit | `pytest apps/delivery/tests/ -x -q` | ❌ W0 | ⬜ pending |
| 06-02-01 | 02 | 2 | PDF-01..PDF-04 | manual | Generate PDF → verify content in MinIO | manual | ⬜ pending |
| 06-02-02 | 02 | 2 | DLV-01, DLV-02 | manual | Trigger delivery → check TG/WA receipt | manual | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/apps/reports/tests/test_tasks.py` — generate_pdf idempotency, PDF content assertions
- [ ] `backend/apps/delivery/tests/test_tasks.py` — deliver_telegram, deliver_whatsapp with mocked APIs
- [ ] `backend/apps/reports/tests/test_views.py` — approve endpoint tests
- [ ] `backend/templates/pdf/audit_report.html` — Jinja2 template

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| PDF visual quality | PDF-03 | Visual/layout inspection | Generate PDF → open → check fonts, layout, cover page |
| Telegram sendDocument | DLV-01 | External API | Trigger delivery with real bot token → check TG chat |
| Wazzup24 delivery | DLV-02 | External API | Trigger delivery → check WhatsApp receipt |
| Presigned URL access | PDF-05 | Network/MinIO | Open presigned URL in browser → PDF downloads |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
