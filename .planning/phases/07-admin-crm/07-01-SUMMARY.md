---
phase: 07-admin-crm
plan: 01
subsystem: admin
tags: [django-unfold, django-axes, tailwind, htmx, ckeditor, sortable2, crm, dashboard]

# Dependency graph
requires:
  - phase: 06-pdf-generation-delivery
    provides: AuditReport, DeliveryLog models needed for admin registration
  - phase: 01-infrastructure-data-model
    provides: all core models (Submission, Payment, Tariff, Industry, ClientProfile, ContentBlock)

provides:
  - django-unfold Tailwind UI applied to all 7 admin.py files
  - dashboard app with 4 stat cards (total/in_progress/delivered/revenue)
  - HTMX filter endpoint at /admin/dashboard/stats/ (industry/tariff/city/date filters)
  - django-axes brute-force protection (10 failed attempts = 1h lockout by IP)
  - baqsy/settings/test.py with AXES_ENABLED=False for safe test isolation
  - UNFOLD sidebar navigation with 5 sections and 9 links

affects: [07-admin-crm plan 02, any phase extending admin.py]

# Tech tracking
tech-stack:
  added:
    - django-unfold 0.90.0 (Tailwind-based admin UI)
    - django-axes 8.3.1 (brute-force protection)
    - django-admin-sortable2 2.2.8 (drag-and-drop ordering)
    - django-ckeditor-5 0.2.20 (rich text editing)
  patterns:
    - unfold.admin.ModelAdmin/TabularInline base classes for all admin registrations
    - DASHBOARD_CALLBACK pattern: pure function(request, context) -> context injecting stats
    - HTMX partial template pattern: _stats_cards.html fragment returned by HTMX endpoint
    - AxesStandaloneBackend + AxesMiddleware last in MIDDLEWARE for brute-force protection
    - test.py inherits dev.py and disables AXES_ENABLED=False for test isolation

key-files:
  created:
    - backend/baqsy/settings/test.py
    - backend/apps/dashboard/__init__.py
    - backend/apps/dashboard/apps.py
    - backend/apps/dashboard/views.py
    - backend/apps/dashboard/urls.py
    - backend/apps/dashboard/tests/__init__.py
    - backend/apps/dashboard/tests/test_dashboard.py
    - backend/apps/accounts/tests/test_axes.py
    - backend/templates/admin/index.html
    - backend/templates/admin/dashboard/_stats_cards.html
  modified:
    - backend/pyproject.toml
    - backend/baqsy/settings/base.py
    - backend/baqsy/urls.py
    - backend/apps/accounts/admin.py
    - backend/apps/content/admin.py
    - backend/apps/delivery/admin.py
    - backend/apps/industries/admin.py
    - backend/apps/payments/admin.py
    - backend/apps/reports/admin.py
    - backend/apps/submissions/admin.py

key-decisions:
  - "unfold must be FIRST in INSTALLED_APPS before django.contrib.admin — order is mandatory"
  - "AxesMiddleware must be LAST in MIDDLEWARE — axes docs require this for correct lockout interception"
  - "test.py settings inherits from dev.py with AXES_ENABLED=False — prevents axes lockouts from cascading into unrelated tests; axes tests use @override_settings(AXES_ENABLED=True) per-method"
  - "dashboard URL registered before admin/ in urls.py — admin catch-all would swallow /admin/dashboard/ otherwise"
  - "dashboard_callback is a pure function injecting into context dict — UNFOLD calls it at admin index render time"
  - "@override_settings cannot decorate pytest classes (only Django SimpleTestCase subclasses) — applied per-method instead"

patterns-established:
  - "All admin ModelAdmin subclasses use unfold.admin.ModelAdmin base class"
  - "All admin inline classes use unfold.admin.TabularInline/StackedInline"
  - "HTMX fragment endpoints use @staff_member_required and return render() of partial template"
  - "Stats filtering via _build_filters(request) helper building ORM filter dict from GET params"

requirements-completed: [CRM-01, CRM-02, CRM-10]

# Metrics
duration: 22min
completed: 2026-04-17
---

# Phase 7 Plan 01: Admin CRM Foundation Summary

**django-unfold Tailwind UI on all 7 admin.py files, HTMX dashboard with 4 stat cards + 5-field filter form, and django-axes brute-force lockout after 10 failed login attempts**

## Performance

- **Duration:** 22 min
- **Started:** 2026-04-17T11:59:00Z
- **Completed:** 2026-04-17T12:21:38Z
- **Tasks:** 2
- **Files modified:** 20

## Accomplishments
- Installed django-unfold 0.90.0, django-axes 8.3.1, django-admin-sortable2 2.2.8, django-ckeditor-5 0.2.20
- Migrated all 7 admin.py files to unfold.admin.ModelAdmin/TabularInline base classes with UNFOLD sidebar navigation (5 sections, 9 links)
- Created dashboard app with dashboard_callback (4 stat cards: total/in_progress/delivered/revenue) and HTMX partial endpoint at /admin/dashboard/stats/ with 5-field filter form (industry/tariff/city/date_from/date_to)
- Configured django-axes: AXES_FAILURE_LIMIT=10, AXES_COOLOFF_TIME=1h, lockout by ip_address; created test.py with AXES_ENABLED=False for safe test isolation
- 8 tests passing: 7 dashboard + 1 axes lockout

## Task Commits

1. **Task 1: Install packages, configure settings, migrate all admin.py to unfold** - `04a1106` (feat)
2. **Task 2: Create dashboard app with stats callback and HTMX filtering** - `f6d1205` (feat)

## Files Created/Modified
- `backend/pyproject.toml` - added 4 new packages; pytest DJANGO_SETTINGS_MODULE → baqsy.settings.test
- `backend/baqsy/settings/base.py` - unfold first in INSTALLED_APPS, axes config, UNFOLD dict, CKEDITOR_5_CONFIGS
- `backend/baqsy/settings/test.py` - new file, inherits dev.py with AXES_ENABLED=False
- `backend/baqsy/urls.py` - dashboard URL prefix before admin/ catch-all
- `backend/apps/*/admin.py` (7 files) - all migrated to unfold.admin.ModelAdmin/TabularInline
- `backend/apps/dashboard/views.py` - dashboard_callback + dashboard_stats_partial HTMX endpoint
- `backend/apps/dashboard/urls.py` - admin_dashboard_stats URL pattern
- `backend/templates/admin/index.html` - HTMX filter form + stats-cards container
- `backend/templates/admin/dashboard/_stats_cards.html` - partial with stats.total/in_progress/delivered/revenue

## Decisions Made
- `unfold` must be FIRST in INSTALLED_APPS before `django.contrib.admin` — unfold overrides admin templates
- `AxesMiddleware` must be LAST in MIDDLEWARE — required by axes documentation for correct request interception
- Dashboard URL registered before `admin/` to avoid catch-all swallowing `/admin/dashboard/stats/`
- `test.py` with `AXES_ENABLED=False` prevents axes from blocking test logins; axes-specific tests enable it per-method with `@override_settings`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `@override_settings` on pytest class causes ValueError**
- **Found during:** Task 2 (test_axes.py collection)
- **Issue:** `@override_settings` decorator cannot be applied to plain pytest classes — Django requires `SimpleTestCase` subclass. Caused `ValueError: Only subclasses of Django SimpleTestCase can be decorated with override_settings`
- **Fix:** Moved `@override_settings(AXES_ENABLED=True, ...)` from class level to method level
- **Files modified:** `backend/apps/accounts/tests/test_axes.py`
- **Verification:** `pytest apps/accounts/tests/test_axes.py` passes (1 passed)
- **Committed in:** `f6d1205` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** Minor — axes test logic unchanged, only decorator placement fixed. No scope creep.

## Issues Encountered
- `poetry` not available in system PATH — used `pip3 install` directly for package installation. Packages correctly listed in pyproject.toml for Docker/CI Poetry resolution.

## Next Phase Readiness
- Unfold UI foundation complete — Plan 02 can now add custom admin actions (approve, generate PDF trigger, etc.)
- All admin registrations migrated — no additional unfold migration needed in Plan 02
- Axes + test.py in place — future tests won't be blocked by brute-force lockout

---
*Phase: 07-admin-crm*
*Completed: 2026-04-17*
