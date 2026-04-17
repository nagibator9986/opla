---
phase: 05-react-frontend
plan: "03"
subsystem: frontend-auth-cabinet
tags: [react, typescript, deeplink, jwt, zustand, tanstack-query, cloudpayments, cabinet]
dependency_graph:
  requires:
    - "05-01: axios instance, Zustand authStore, TypeScript API types, ProtectedRoute"
    - "05-02: Button, Card UI components, openPaymentWidget, payments API (initiateUpsell)"
  provides:
    - "Deep-link auth flow: /auth/:uuid → JWT exchange → /cabinet redirect"
    - "useSubmission hook: TanStack Query wrapper for GET /api/v1/submissions/my/"
    - "StatusProgress component: 4-step progress bar for submission status"
    - "PdfDownloadButton component: conditional PDF download or placeholder"
    - "UpsellCard component: ashide_1-only upgrade card with CP Widget integration"
    - "CabinetPage: full personal cabinet with order info, status, PDF, upsell"
  affects:
    - frontend/src/pages/AuthPage.tsx
    - frontend/src/pages/CabinetPage.tsx
    - frontend/src/api/auth.ts (new)
    - frontend/src/api/submissions.ts (new)
    - frontend/src/hooks/useSubmission.ts (new)
tech_stack:
  added: []
  patterns:
    - "Plain axios (not api instance) for deeplink exchange — no JWT interceptor needed before auth"
    - "TanStack Query enabled flag pattern: query runs only when isAuthenticated"
    - "UpsellCard visibility controlled by tariffCode + status guard — returns null if not applicable"
    - "Skeleton loader via animate-pulse placeholder cards in CabinetPage"
    - "StatusProgress dual layout: md:hidden for vertical mobile, hidden md:flex for horizontal desktop"
key_files:
  created:
    - frontend/src/api/auth.ts
    - frontend/src/api/submissions.ts
    - frontend/src/hooks/useSubmission.ts
    - frontend/src/components/cabinet/StatusProgress.tsx
    - frontend/src/components/cabinet/PdfDownloadButton.tsx
    - frontend/src/components/cabinet/UpsellCard.tsx
  modified:
    - frontend/src/pages/AuthPage.tsx
    - frontend/src/pages/CabinetPage.tsx
decisions:
  - "exchangeDeeplink uses plain axios (not api instance) — client has no JWT at exchange time, interceptors would interfere"
  - "UpsellCard visibility: tariffCode === 'ashide_1' AND status in completed/under_audit/delivered — prevents premature upsell offer"
  - "StatusProgress stepIndex computed via findIndex on statuses arrays — robust against new statuses added"
  - "CabinetPage uses separate Card for each section (info/status/pdf/upsell) — clear visual separation"
metrics:
  duration: "~10 min"
  completed_date: "2026-04-17"
  tasks_completed: 2
  files_created: 6
  files_modified: 2
---

# Phase 5 Plan 03: Auth Deep-Link and Personal Cabinet Summary

**One-liner:** Deep-link UUID-to-JWT exchange via plain axios, personal cabinet with 4-step status progress bar, PDF download button, and ashide_1-only upsell card with CloudPayments Widget integration.

## What Was Built

### Task 1: Auth Flow and Submission API

**`frontend/src/api/auth.ts`** — `exchangeDeeplink(uuid)` using plain axios (not the API instance) to POST `{ token: uuid }` to `/api/v1/bot/deeplink/exchange/`. Returns `DeeplinkResponse` with access/refresh tokens. Plain axios is required because the JWT interceptor would corrupt a pre-auth request.

**`frontend/src/api/submissions.ts`** — `getMySubmission()` using the authenticated `api` instance to GET `/api/v1/submissions/my/`. Returns the full `Submission` object including `tariff_code` and `pdf_url`.

**`frontend/src/hooks/useSubmission.ts`** — TanStack Query hook with `enabled: isAuthenticated` guard. 30-second staleTime. Query key `['my-submission']` used by UpsellCard to invalidate after successful payment.

**`frontend/src/pages/AuthPage.tsx`** (replaced stub) — Reads `:uuid` param, calls `exchangeDeeplink`, stores tokens via `setAuth`, redirects to `/cabinet` on success. On error shows "Ссылка истекла или недействительна" with a link to the bot. Loading spinner while in progress.

### Task 2: Cabinet Components and CabinetPage

**`frontend/src/components/cabinet/StatusProgress.tsx`** — Horizontal progress bar on md+ screens, vertical stack on mobile. 4 steps: Оплачено / Анкета / На аудите / Готово. Status mapping: `paid`/`in_progress_basic` → step 1; `in_progress_full` → step 2; `completed`/`under_audit` → step 3; `delivered` → step 4. Completed steps: `bg-emerald-500` with checkmark. Current step: `bg-amber-500 animate-pulse`. Future steps: `bg-slate-300`.

**`frontend/src/components/cabinet/PdfDownloadButton.tsx`** — If `pdfUrl` is set: renders a Button wrapping an `<a href target="_blank">`. If null: plain text "Отчёт ещё не готов" in `text-slate-400`.

**`frontend/src/components/cabinet/UpsellCard.tsx`** — Returns null if `tariffCode !== 'ashide_1'` or `status` not in `[completed, under_audit, delivered]`. Otherwise renders a Card with upgrade copy ("90 000 ₸"), calls `initiateUpsell(submissionId)`, then `openPaymentWidget` with success/fail callbacks. Success invalidates `['my-submission']` query and alerts user. API errors displayed inline.

**`frontend/src/pages/CabinetPage.tsx`** (replaced stub) — Uses `useSubmission()` and `useAuthStore`. Greeting with client name. Three loading states: skeleton (isLoading), no-order message (isError or no submission), full content (submission loaded). Content layout: order info Card, StatusProgress Card, PdfDownloadButton Card, UpsellCard. Logout button calls `clearAuth` + navigate to `/`.

## Verification Results

- `npx tsc --noEmit` — exit 0 (after Task 1)
- `npm run build` — exit 0, 380.98KB JS bundle (after Task 2)

## Deviations from Plan

None — plan executed exactly as written.

Note: `frontend/src/components/layout/Header.tsx` was found already populated by an intermediate commit (not from plan 02 execution but committed separately). Used as-is.

## Self-Check

### Files Exist
- frontend/src/api/auth.ts: FOUND
- frontend/src/api/submissions.ts: FOUND
- frontend/src/hooks/useSubmission.ts: FOUND
- frontend/src/components/cabinet/StatusProgress.tsx: FOUND
- frontend/src/components/cabinet/PdfDownloadButton.tsx: FOUND
- frontend/src/components/cabinet/UpsellCard.tsx: FOUND
- frontend/src/pages/AuthPage.tsx: FOUND
- frontend/src/pages/CabinetPage.tsx: FOUND

### Commits
- da8d9e6: feat(05-03): auth deep-link exchange, submissions API, useSubmission hook, AuthPage
- aa1566a: feat(05-03): личный кабинет — StatusProgress, PdfDownloadButton, UpsellCard, CabinetPage

## Self-Check: PASSED
