---
phase: 05-react-frontend
plan: "01"
subsystem: frontend-infra
tags: [react, vite, typescript, tailwind, axios, zustand, react-router, django-api, docker]
dependency_graph:
  requires: []
  provides:
    - ContentBlock API endpoint at GET /api/v1/content/
    - SubmissionDetailSerializer with tariff_code and pdf_url fields
    - GET /api/v1/submissions/my/ endpoint returning last client submission
    - Vite React TypeScript project scaffold
    - Axios instance with JWT Bearer + auto-refresh interceptor
    - Zustand auth store (isAuthenticated, clientProfile, setAuth, clearAuth)
    - React Router v7 with 4 routes and ProtectedRoute
    - TypeScript API types (Tariff, Submission, DeeplinkResponse, UpsellConfig, ContentBlocks)
    - CloudPayments window.cp global type declarations
    - Frontend Docker service in docker-compose
    - Nginx proxy for Vite dev server and API routing
  affects:
    - docker/docker-compose.yml
    - docker/nginx.conf
    - backend/apps/core/api_urls.py
    - backend/apps/submissions/serializers.py
    - backend/apps/submissions/views.py
    - backend/apps/submissions/urls.py
tech_stack:
  added:
    - react: "19.x"
    - react-dom: "19.x"
    - vite: "8.x"
    - typescript: "6.x"
    - tailwindcss: "4.x"
    - "@tailwindcss/vite": "4.x"
    - "@tanstack/react-query": "5.x"
    - "@tanstack/react-query-devtools": "5.x"
    - zustand: "5.x"
    - react-router-dom: "7.x"
    - axios: "1.x"
  patterns:
    - Axios response interceptor with failedQueue for parallel 401 handling
    - Zustand store with localStorage persistence (no persist middleware)
    - React Router v7 createBrowserRouter with ProtectedRoute wrapper
    - Tailwind v4 via @tailwindcss/vite plugin (no tailwind.config.js)
    - ContentBlock flat dict API pattern {key: content}
    - SubmissionDetailSerializer SerializerMethodField for related AuditReport.pdf_url
key_files:
  created:
    - backend/apps/content/views.py
    - backend/apps/content/serializers.py
    - backend/apps/content/urls.py
    - backend/apps/content/tests/test_views.py
    - frontend/src/api/axios.ts
    - frontend/src/store/authStore.ts
    - frontend/src/router/index.tsx
    - frontend/src/router/ProtectedRoute.tsx
    - frontend/src/types/api.ts
    - frontend/src/types/cloudpayments.d.ts
    - frontend/src/pages/LandingPage.tsx
    - frontend/src/pages/TariffsPage.tsx
    - frontend/src/pages/AuthPage.tsx
    - frontend/src/pages/CabinetPage.tsx
    - frontend/src/main.tsx
    - frontend/src/index.css
    - frontend/index.html
    - frontend/vite.config.ts
    - frontend/Dockerfile
    - frontend/package.json
  modified:
    - backend/apps/core/api_urls.py
    - backend/apps/submissions/serializers.py
    - backend/apps/submissions/views.py
    - backend/apps/submissions/urls.py
    - docker/docker-compose.yml
    - docker/nginx.conf
    - .env.example
decisions:
  - "ContentBlock API returns flat dict {key: content} not list — simpler for frontend to consume without key lookup"
  - "SubmissionDetailSerializer extended with pdf_url as SerializerMethodField via getattr(obj, 'report', None) pattern — avoids RelatedObjectDoesNotExist on missing AuditReport"
  - "MySubmissionView returns last by created_at — for MVP one active submission per client is enough"
  - "Axios failedQueue pattern prevents duplicate refresh calls for parallel 401s — standard battle-tested approach"
  - "Tailwind v4 @tailwindcss/vite plugin used — no tailwind.config.js needed, CSS @import only"
  - "nginx updated to proxy all non-API/non-admin routes to frontend:5173 for SPA dev mode"
metrics:
  duration: "~15 min"
  completed_date: "2026-04-17"
  tasks_completed: 2
  files_created: 20
  files_modified: 7
---

# Phase 5 Plan 01: React Frontend Foundation Summary

**One-liner:** Vite React 19 + TypeScript SPA scaffold with axios JWT interceptor, Zustand auth store, React Router v7, Tailwind v4 — plus ContentBlock API and SubmissionDetailSerializer pdf_url extension on Django.

## What Was Built

### Backend (Task 1)

**ContentBlock API** — new `GET /api/v1/content/` endpoint returning a flat dict of active content blocks `{"hero_title": "...", "hero_subtitle": "..."}`. Permission is `AllowAny` (public). The response format is a plain dict keyed by `ContentBlock.key` for easy frontend consumption without array iteration.

**SubmissionDetailSerializer extensions:**
- `tariff_code` via `CharField(source="tariff.code")` — exposes tariff code needed for Upsell button visibility logic
- `pdf_url` via `SerializerMethodField` accessing `obj.report.pdf_url` through `getattr` — safe when AuditReport doesn't exist yet (returns null)

**MySubmissionView** — new `GET /api/v1/submissions/my/` endpoint returning the latest submission for the authenticated JWT client. Uses existing `_get_client_profile()` helper. Returns 404 with `{"detail": "Нет активных заказов."}` when no submission exists. Route placed before `<uuid:pk>/` to avoid UUID routing conflict.

3 tests for ContentBlock API: active blocks returned, empty dict when none, anonymous access allowed.

### Frontend (Task 2)

**Vite + React 19 + TypeScript scaffold** in `frontend/` with all locked dependencies installed.

**Infrastructure layers:**
- `src/api/axios.ts` — axios instance with request interceptor (Bearer token from localStorage) and response interceptor with auto-refresh on 401. Uses `isRefreshing` flag + `failedQueue` array to handle concurrent requests during refresh. On refresh failure calls `useAuthStore.getState().clearAuth()`.
- `src/store/authStore.ts` — Zustand 5.x store with `isAuthenticated`, `clientProfile`, `setAuth()`, `clearAuth()`. State initialized from localStorage for page reload persistence.
- `src/router/index.tsx` — `createBrowserRouter` with 4 routes: `/` (LandingPage), `/tariffs` (TariffsPage), `/auth/:uuid` (AuthPage), `/cabinet` (ProtectedRoute → CabinetPage).
- `src/router/ProtectedRoute.tsx` — redirects to `/` if not authenticated.
- `src/types/api.ts` — TypeScript interfaces for all API responses.
- `src/types/cloudpayments.d.ts` — `declare global` for `window.cp.CloudPayments`.

**Tailwind v4** configured via `@tailwindcss/vite` plugin in `vite.config.ts` + `@import "tailwindcss"` in `index.css` (no `tailwind.config.js`).

**Docker integration:**
- `frontend/Dockerfile` using `node:22-alpine`
- `frontend` service added to `docker/docker-compose.yml` with volume mount, port 5173, `VITE_CLOUDPAYMENTS_PUBLIC_ID` env var
- `docker/nginx.conf` updated with frontend proxy locations (`/assets/`, `/@vite/`, SPA fallback `/`), plus explicit `/api/` and `/admin/` routes to Django

## Verification Results

- `pytest apps/content/tests/test_views.py -x -q` — 3 passed
- `cd frontend && npm run build` — exit 0, 309KB JS bundle, 5.9KB CSS
- `docker-compose config --quiet` — valid YAML (tested with temp .env)
- `grep -n "content/" backend/apps/core/api_urls.py` — route found at line 10

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check

### Files Exist
- backend/apps/content/views.py: FOUND
- backend/apps/content/serializers.py: FOUND
- backend/apps/content/urls.py: FOUND
- backend/apps/content/tests/test_views.py: FOUND
- frontend/src/api/axios.ts: FOUND
- frontend/src/store/authStore.ts: FOUND
- frontend/src/router/index.tsx: FOUND
- frontend/Dockerfile: FOUND

### Commits
- ad51e53: feat(05-01): ContentBlock API, SubmissionDetailSerializer extensions, MySubmissionView
- 5fc577a: feat(05-01): Vite scaffold, axios/Zustand/router infrastructure, Docker frontend service

## Self-Check: PASSED
