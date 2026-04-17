---
phase: 5
slug: react-frontend
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-17
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.3 + pytest-django 4.9 (backend); Vitest (frontend, to be set up in Wave 0) |
| **Config file** | `backend/pyproject.toml` — `[tool.pytest.ini_options]`; `frontend/vitest.config.ts` (Wave 0) |
| **Quick run command** | `docker-compose exec web pytest apps/content/ -x -q` |
| **Full suite command** | `docker-compose exec web pytest -x -q && docker-compose exec frontend npm run build` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `docker-compose exec web pytest apps/content/ -x -q`
- **After every plan wave:** Run `docker-compose exec web pytest -x -q && docker-compose exec frontend npm run build`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-00-01 | 00 | 0 | WEB-01 | smoke | `docker-compose exec frontend npm run build` | ❌ W0 | ⬜ pending |
| 05-00-02 | 00 | 0 | WEB-02 | unit | `docker-compose exec web pytest apps/content/tests/test_views.py -x` | ❌ W0 | ⬜ pending |
| 05-00-03 | 00 | 0 | WEB-04 | unit | `docker-compose exec web pytest apps/submissions/tests/ -k pdf_url -x` | ❌ W0 | ⬜ pending |
| 05-01-01 | 01 | 1 | WEB-02 | manual | Browser: landing sections render with ContentBlock text | manual | ⬜ pending |
| 05-01-02 | 01 | 1 | WEB-03 | manual | Browser: tariff cards load prices from API | manual | ⬜ pending |
| 05-01-03 | 01 | 1 | WEB-06 | unit | `docker-compose exec web pytest apps/accounts/tests/ -k exchange -x` | ✅ | ⬜ pending |
| 05-02-01 | 02 | 2 | WEB-04 | manual | Browser: cabinet shows status progress | manual | ⬜ pending |
| 05-02-02 | 02 | 2 | WEB-05 | manual | Browser: upsell button visible for ashide_1 | manual | ⬜ pending |
| 05-02-03 | 02 | 2 | WEB-07 | manual | Browser: responsive at 375px, 768px, 1280px | manual | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/` — Vite scaffold with React 18 + TypeScript
- [ ] `frontend/Dockerfile` — dev container
- [ ] `docker/docker-compose.yml` — add frontend service
- [ ] `docker/nginx.conf` — SPA fallback + Vite proxy
- [ ] `backend/apps/content/views.py` — ContentBlock list API
- [ ] `backend/apps/content/serializers.py` — ContentBlockSerializer
- [ ] `backend/apps/content/urls.py` — URL routing
- [ ] `backend/apps/content/tests/test_views.py` — covers WEB-02
- [ ] `backend/apps/submissions/serializers.py` — extend with pdf_url (covers WEB-04)
- [ ] `.env.example` — add VITE_CLOUDPAYMENTS_PUBLIC_ID

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Landing sections render | WEB-02 | Visual layout verification | Open `/`, check hero/method/tariffs/cases/FAQ sections display |
| Mobile-first responsive | WEB-07 | Device viewport testing | Resize to 375px, 768px, 1280px — verify layout adapts |
| CloudPayments widget opens | WEB-03 | External service + DOM interaction | Click "Оплатить" → CP modal appears (sandbox) |
| Deep-link auth redirect | WEB-06 | Full flow E2E | Navigate `/auth/{valid-uuid}` → redirects to `/cabinet` |
| Upsell CP widget | WEB-05 | External service + conditional UI | Login as ashide_1 client → click Upsell → CP modal shows 90000₸ |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
