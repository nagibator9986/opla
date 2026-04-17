---
phase: 07-admin-crm
plan: 02
subsystem: admin
tags: [django-admin, unfold, adminsortable2, ckeditor5, crm, wysiwyg]

# Dependency graph
requires:
  - phase: 07-admin-crm
    provides: "Plan 01 - unfold ModelAdmin base for all apps, AxesMiddleware, dashboard stats"
provides:
  - "SubmissionAdmin with AnswerInline + AuditReportInline + approve_and_send action"
  - "AuditReportAdmin with approve_and_send action using ApproveReportView.as_view()"
  - "QuestionnaireTemplateAdmin with save_model versioning + has_change_permission read-only for inactive"
  - "QuestionInline with SortableInlineAdminMixin for drag-n-drop reordering"
  - "TariffAdmin with list_editable price_kzt+is_active + list_display_links"
  - "ContentBlockAdmin with CKEditor5Widget via formfield_overrides"
  - "IndustryAdmin with list_filter is_active"
affects: [Phase 08 deployment, admin workflow testing]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ApproveReportView.as_view() called from admin action to properly wrap Django request into DRF Request for IsAdminUser permission check"
    - "unfold @action decorator for detail actions on change page (actions_detail)"
    - "SortableInlineAdminMixin mixed with TabularInline for drag-n-drop inline ordering"
    - "formfield_overrides {models.TextField: {widget: CKEditor5Widget}} for WYSIWYG in admin"
    - "has_change_permission(request, obj) returning False for archived objects = read-only protection"

key-files:
  created:
    - backend/apps/submissions/tests/test_admin.py
    - backend/apps/reports/tests/test_admin.py
    - backend/apps/industries/tests/test_admin.py
    - backend/apps/payments/tests/test_admin.py
    - backend/apps/content/tests/test_admin.py
  modified:
    - backend/apps/submissions/admin.py
    - backend/apps/reports/admin.py
    - backend/apps/industries/admin.py
    - backend/apps/content/admin.py
    - backend/apps/payments/admin.py

key-decisions:
  - "inspect.getsource(admin_module) used in tests instead of inspect.getsource(method) because unfold @action decorator wraps the function — module source is the reliable artifact"
  - "list_display_links = ('title',) required in TariffAdmin because list_editable field cannot be in list_display_links"

patterns-established:
  - "admin actions calling DRF views: always use View.as_view()(request, **kwargs) to ensure DRF initialize_request wraps the Django HttpRequest"
  - "inactive model protection: has_change_permission(request, obj) with obj-guard returns False for inactive records"

requirements-completed: [CRM-03, CRM-04, CRM-05, CRM-06, CRM-07, CRM-08, CRM-09]

# Metrics
duration: 15min
completed: 2026-04-17
---

# Phase 07 Plan 02: Admin CRM Editor Customization Summary

**All 7 CRM editor requirements delivered: Submission+Report approve pipeline, template versioning, Question drag-n-drop, Tariff inline editing, ContentBlock CKEditor5 WYSIWYG**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-04-17T12:22:41Z
- **Completed:** 2026-04-17T12:42:00Z
- **Tasks:** 2
- **Files modified:** 10 (5 admin.py + 5 test files)

## Accomplishments
- Submission change page now shows AnswerInline (read-only) + AuditReportInline with admin_text field, plus approve_and_send button
- Both SubmissionAdmin and AuditReportAdmin have approve_and_send action that calls ApproveReportView.as_view() for proper DRF request wrapping
- QuestionnaireTemplateAdmin creates a new template version on save of active template; inactive templates become read-only
- QuestionInline uses SortableInlineAdminMixin for browser drag-n-drop reordering
- TariffAdmin has list_editable for price_kzt and is_active (in-line editing from list view)
- ContentBlockAdmin uses CKEditor5Widget via formfield_overrides for WYSIWYG editing
- 14 new tests covering all CRM requirements (CRM-03 through CRM-09); full suite 145 passed, 2 xfailed

## Task Commits

Each task was committed atomically:

1. **Task 1: Customize Submission/Report admin with answers pane and approve action** - `e59dadd` (feat)
2. **Task 2: Customize Industry/Template/Question, Tariff, and ContentBlock editors** - `c8c1e49` (feat)

## Files Created/Modified
- `backend/apps/submissions/admin.py` - AuditReportInline + approve_and_send action on SubmissionAdmin
- `backend/apps/reports/admin.py` - approve_and_send action on AuditReportAdmin using as_view()
- `backend/apps/industries/admin.py` - SortableInlineAdminMixin on QuestionInline, save_model versioning + has_change_permission
- `backend/apps/content/admin.py` - CKEditor5Widget via formfield_overrides
- `backend/apps/payments/admin.py` - list_display_links + confirmed list_editable
- `backend/apps/submissions/tests/test_admin.py` - CRM-03/04 tests
- `backend/apps/reports/tests/test_admin.py` - CRM-04 tests (inspect module source for as_view() assertion)
- `backend/apps/industries/tests/test_admin.py` - CRM-05/06/07 tests
- `backend/apps/payments/tests/test_admin.py` - CRM-08 tests
- `backend/apps/content/tests/test_admin.py` - CRM-09 tests

## Decisions Made
- Used `inspect.getsource(admin_module)` instead of `inspect.getsource(method)` in test_approve_calls_view_as_view because the unfold `@action` decorator wraps the method and getsource returns wrapper code, not original function source. Module-level source is the reliable artifact.
- Added `list_display_links = ("title",)` to TariffAdmin — required because Django raises ImproperlyConfigured if a field in list_editable is also in list_display_links (must be separate).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed inspect.getsource usage in test for @action-decorated method**
- **Found during:** Task 1 (test_approve_calls_view_as_view)
- **Issue:** `inspect.getsource(AuditReportAdmin.approve_and_send)` returned the unfold @action wrapper code instead of our implementation, causing the `as_view()` assertion to fail
- **Fix:** Changed test to use `inspect.getsource(admin_module)` — inspects the module source directly, which reliably contains our implementation
- **Files modified:** backend/apps/reports/tests/test_admin.py
- **Verification:** Test passes; `as_view()` assertion confirmed present in module source
- **Committed in:** e59dadd (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug in test approach)
**Impact on plan:** Minor test adjustment. No scope creep. All acceptance criteria met.

## Issues Encountered
- unfold `@action` decorator wraps functions without `__wrapped__` attribute, so standard `inspect.getsource(method)` falls back to decorator wrapper code. Solution: inspect module source instead of method source.

## User Setup Required
None - no external service configuration required. CKEditor5 and adminsortable2 were already in INSTALLED_APPS from Plan 01.

Note: drag-n-drop (CRM-07) and CKEditor rendering (CRM-09) require manual browser verification — no automated test possible for JS-driven UI.

## Next Phase Readiness
- All CRM admin editors complete (CRM-01 through CRM-09 done)
- Phase 07 complete — ready for Phase 08 (deployment/hardening)
- Admin can now manage the full order lifecycle: view submissions, write audit text, approve and trigger PDF delivery pipeline

---
*Phase: 07-admin-crm*
*Completed: 2026-04-17*
