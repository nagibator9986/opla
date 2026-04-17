---
phase: 05-react-frontend
plan: 02
subsystem: ui
tags: [react, tailwind, tanstack-query, cloudpayments, typescript]

requires:
  - phase: 05-react-frontend-01
    provides: axios instance with JWT interceptor, auth store, TypeScript types, Tailwind v4 setup, router scaffold

provides:
  - Landing page with Hero/Method/Tariffs/Cases/FAQ sections wired to ContentBlock and Tariffs APIs
  - TariffsPage standalone page for Telegram deep-link entry
  - CloudPayments Widget wrapper (openPaymentWidget)
  - Reusable Button and Card UI primitives
  - useContentBlocks and useTariffs TanStack Query hooks with staleTime and fallback

affects: [06-pdf-audit, 07-whatsapp-delivery]

tech-stack:
  added: []
  patterns:
    - ContentBlock flat-dict API consumed via TanStack Query hook with static fallback data
    - openPaymentWidget wraps window.cp with availability guard before instantiation
    - TariffsSection and TariffsPage share formatPrice helper and TariffCard pattern
    - FaqSection dynamically discovers faq_N_q keys from content dict

key-files:
  created:
    - frontend/src/api/content.ts
    - frontend/src/api/tariffs.ts
    - frontend/src/api/payments.ts
    - frontend/src/hooks/useContentBlocks.ts
    - frontend/src/hooks/useTariffs.ts
    - frontend/src/components/payment/openPaymentWidget.ts
    - frontend/src/components/ui/Button.tsx
    - frontend/src/components/ui/Card.tsx
    - frontend/src/components/layout/Header.tsx
    - frontend/src/components/layout/Footer.tsx
    - frontend/src/components/landing/HeroSection.tsx
    - frontend/src/components/landing/MethodSection.tsx
    - frontend/src/components/landing/TariffsSection.tsx
    - frontend/src/components/landing/CasesSection.tsx
    - frontend/src/components/landing/FaqSection.tsx
    - frontend/src/components/landing/CtaFooter.tsx
  modified:
    - frontend/src/pages/LandingPage.tsx
    - frontend/src/pages/TariffsPage.tsx

key-decisions:
  - "openPaymentWidget guards window.cp?.CloudPayments before instantiation — shows alert if widget script not loaded"
  - "useContentBlocks uses placeholderData (not initialData) so API response replaces fallback without cache mutation"
  - "TariffsPage loads GET /api/v1/submissions/my/ when isAuthenticated to get submission UUID for invoiceId"
  - "FaqSection dynamically discovers faq_N_q keys — adding new FAQ items requires only ContentBlock API update"
  - "ashide_2 tariff card always rendered with highlight=true for premium visual treatment"

patterns-established:
  - "Content from API with static fallback: useQuery with placeholderData for zero-flash rendering"
  - "Payment trigger pattern: check auth → alert or call openPaymentWidget"
  - "Skeleton loading cards match final card dimensions to prevent layout shift"

requirements-completed: [WEB-02, WEB-03, WEB-07, PAY-01]

duration: 18min
completed: 2026-04-17
---

# Phase 05 Plan 02: Landing Page and TariffsPage Summary

**Full-stack landing page with 6 sections driven by ContentBlock API, CloudPayments Widget integration, and a standalone TariffsPage for Telegram deep-link entry**

## Performance

- **Duration:** 18 min
- **Started:** 2026-04-17T08:09:24Z
- **Completed:** 2026-04-17T08:27:00Z
- **Tasks:** 2
- **Files modified:** 18

## Accomplishments

- API layer (content, tariffs, payments) + TanStack Query hooks with staleTime 5min and fallback data
- Full landing page: Hero (dark gradient), Method (3-step), Tariffs (cards from API), Cases (2-col grid), FAQ (accordion), CtaFooter — all consuming ContentBlock API
- Fixed responsive Header with hamburger mobile menu, dark Footer
- TariffsPage as standalone deep-link entry point from Telegram bot, loads user submission for invoiceId
- CloudPayments Widget called through openPaymentWidget wrapper with window.cp guard
- npm run build passes — 153 modules, 381 kB bundle

## Task Commits

1. **Task 1: API functions, hooks, and UI primitives** - `d97ae87` (feat)
2. **Task 2: Landing sections, Header/Footer, LandingPage, TariffsPage** - `f9a5905` (feat)

**Plan metadata:** (pending final commit)

## Files Created/Modified

- `frontend/src/api/content.ts` - getContentBlocks function
- `frontend/src/api/tariffs.ts` - getTariffs function
- `frontend/src/api/payments.ts` - initiateUpsell function
- `frontend/src/hooks/useContentBlocks.ts` - TanStack Query hook with FALLBACK dict
- `frontend/src/hooks/useTariffs.ts` - TanStack Query hook
- `frontend/src/components/payment/openPaymentWidget.ts` - CloudPayments Widget wrapper
- `frontend/src/components/ui/Button.tsx` - primary/secondary/outline variants, sm/md/lg sizes
- `frontend/src/components/ui/Card.tsx` - white/highlighted dark variants
- `frontend/src/components/layout/Header.tsx` - fixed header, responsive nav, hamburger
- `frontend/src/components/layout/Footer.tsx` - dark footer with copyright
- `frontend/src/components/landing/HeroSection.tsx` - full-screen dark gradient hero
- `frontend/src/components/landing/MethodSection.tsx` - 3-step numbered process
- `frontend/src/components/landing/TariffsSection.tsx` - API tariff cards with CP Widget
- `frontend/src/components/landing/CasesSection.tsx` - 2-col case study cards
- `frontend/src/components/landing/FaqSection.tsx` - accordion with dynamic key discovery
- `frontend/src/components/landing/CtaFooter.tsx` - Telegram CTA block
- `frontend/src/pages/LandingPage.tsx` - full page composition
- `frontend/src/pages/TariffsPage.tsx` - standalone page with submission loading

## Decisions Made

- `openPaymentWidget` uses `window.cp?.CloudPayments` optional chaining with user-facing alert if widget script not loaded (handles async script loading edge case)
- `useContentBlocks` uses `placeholderData` not `initialData` — placeholder doesn't write to cache so real API data replaces it cleanly on fetch
- `TariffsPage` fetches `GET /submissions/my/` to get submission UUID for `invoiceId` passed to CloudPayments — enables proper payment tracking
- `FaqSection` dynamically scans for `faq_N_q` keys starting at 1 — new FAQ items added via CMS without code changes

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

`VITE_CLOUDPAYMENTS_PUBLIC_ID` environment variable must be set in `frontend/.env` for CloudPayments Widget to function. See `.env.example`.

## Next Phase Readiness

- Landing and TariffsPage fully functional pending backend ContentBlock and Tariffs API being live
- Cabinet page (AuthPage, CabinetPage stubs from Plan 01) ready for Phase 05-03 if planned
- CloudPayments integration ready — needs real `publicId` in env and CP widget script tag in `index.html`

---
*Phase: 05-react-frontend*
*Completed: 2026-04-17*
