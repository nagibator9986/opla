---
phase: 07-admin-crm
verified: 2026-04-17T13:00:00Z
status: passed
score: 13/13 must-haves verified
---

# Phase 7: Admin CRM Verification Report

**Phase Goal:** Администратор может управлять всем жизненным циклом заказа, контентом и конфигурацией системы через веб-интерфейс без правки кода
**Verified:** 2026-04-17T13:00:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth                                                                                                          | Status     | Evidence                                                                                                                              |
|----|----------------------------------------------------------------------------------------------------------------|------------|---------------------------------------------------------------------------------------------------------------------------------------|
| 1  | Admin index page shows 4 stat cards: total orders, in progress, delivered, revenue                             | VERIFIED   | `dashboard/views.py` dashboard_callback builds `stats` dict with 4 keys; `_stats_cards.html` renders all 4 cards                    |
| 2  | Dashboard filters by industry/tariff/date update stats cards without page reload (HTMX)                        | VERIFIED   | `index.html` uses `hx-get="{% url 'admin_dashboard_stats' %}"` on form `change`; endpoint at `urls.py` name=admin_dashboard_stats    |
| 3  | 10 failed login attempts from same IP block further attempts with HTTP 429                                     | VERIFIED   | `base.py` AXES_FAILURE_LIMIT=10, AxesMiddleware last in MIDDLEWARE, AxesStandaloneBackend first in AUTHENTICATION_BACKENDS            |
| 4  | All admin pages render with django-unfold Tailwind UI (sidebar navigation visible)                             | VERIFIED   | All 7 admin.py files import from `unfold.admin`; UNFOLD dict in base.py with sidebar navigation (5 sections, 9 links)               |
| 5  | Submission list shows orders with search by client name/company and filters by status/tariff/industry          | VERIFIED   | `submissions/admin.py` search_fields=("client__name","client__company","id"), list_filter=("status","tariff","template__industry")   |
| 6  | Submission change form shows client answers read-only on left and audit text field on right                    | VERIFIED   | AnswerInline (readonly_fields set) + AuditReportInline with admin_text field both in SubmissionAdmin.inlines                          |
| 7  | Submission change page has 'Approve and Send' action that triggers PDF generation and delivery pipeline         | VERIFIED   | SubmissionAdmin.actions_detail=["approve_and_send"]; action calls ApproveReportView.as_view()(request, report_id=...)                |
| 8  | AuditReport admin also has 'Approve and Send' action button                                                    | VERIFIED   | AuditReportAdmin.actions_detail=["approve_and_send"]; identical as_view() pattern                                                    |
| 9  | Editing an active QuestionnaireTemplate creates a new version; inactive templates are read-only                | VERIFIED   | save_model calls create_new_version() when change and is_active; has_change_permission returns False when not obj.is_active           |
| 10 | Questions within a template can be reordered via drag-n-drop                                                   | VERIFIED*  | QuestionInline inherits SortableInlineAdminMixin; JS rendering requires manual browser verification                                   |
| 11 | Tariff price_kzt and is_active are editable directly from list view                                            | VERIFIED   | TariffAdmin.list_editable=("price_kzt","is_active"), list_display_links=("title",)                                                   |
| 12 | ContentBlock content field uses CKEditor5 WYSIWYG editor                                                       | VERIFIED*  | formfield_overrides={models.TextField: {"widget": CKEditor5Widget(config_name="content_block")}}; JS rendering needs browser check   |
| 13 | Industry CRUD works in admin for staff user                                                                     | VERIFIED   | IndustryAdmin registered with list_display, list_filter, search_fields, prepopulated_fields                                           |

*Items 10 and 12 have automated structural verification confirmed; the JS rendering aspect requires manual browser verification (noted in human verification section below).

**Score:** 13/13 truths verified

---

### Required Artifacts

| Artifact                                                             | Expected                                             | Status     | Details                                                              |
|----------------------------------------------------------------------|------------------------------------------------------|------------|----------------------------------------------------------------------|
| `backend/apps/dashboard/views.py`                                    | dashboard_callback + dashboard_stats_partial          | VERIFIED   | Both functions present, substantive, 66 lines                        |
| `backend/apps/dashboard/tests/test_dashboard.py`                     | Tests for CRM-01, CRM-02 stats and filters            | VERIFIED   | 81 lines, 7 tests covering stats counters and all filter types       |
| `backend/apps/accounts/tests/test_axes.py`                           | Test for CRM-10 brute-force lockout                   | VERIFIED   | 20 lines, test_lockout_after_failures present                        |
| `backend/baqsy/settings/test.py`                                     | Test settings with AXES_ENABLED=False                 | VERIFIED   | Contains AXES_ENABLED = False, inherits from dev.py                  |
| `backend/templates/admin/index.html`                                 | Custom dashboard template with HTMX filter form       | VERIFIED   | Contains hx-get, htmx.org script, 5-field filter form                |
| `backend/templates/admin/dashboard/_stats_cards.html`                | Partial template for HTMX stats cards fragment        | VERIFIED   | Contains stats.total, stats.in_progress, stats.delivered, stats.revenue |
| `backend/apps/submissions/admin.py`                                  | SubmissionAdmin with AuditReportInline + approve action | VERIFIED | AuditReportInline, AnswerInline, approve_and_send in actions_detail  |
| `backend/apps/reports/admin.py`                                      | AuditReportAdmin with approve_and_send action         | VERIFIED   | actions_detail=["approve_and_send"], ApproveReportView.as_view()     |
| `backend/apps/industries/admin.py`                                   | QuestionnaireTemplateAdmin with versioning + sortable | VERIFIED   | SortableInlineAdminMixin, save_model, has_change_permission          |
| `backend/apps/content/admin.py`                                      | ContentBlockAdmin with CKEditor5Widget                | VERIFIED   | formfield_overrides with CKEditor5Widget confirmed                    |
| `backend/apps/payments/admin.py`                                     | TariffAdmin with list_editable                        | VERIFIED   | list_editable=("price_kzt","is_active"), list_display_links=("title",) |

---

### Key Link Verification

| From                                            | To                                         | Via                                              | Status  | Details                                                                          |
|-------------------------------------------------|--------------------------------------------|--------------------------------------------------|---------|----------------------------------------------------------------------------------|
| `templates/admin/index.html`                    | `apps/dashboard/views.py`                  | hx-get to admin_dashboard_stats URL              | WIRED   | `hx-get="{% url 'admin_dashboard_stats' %}"` confirmed in template               |
| `baqsy/settings/base.py`                        | `apps/dashboard/views.py`                  | UNFOLD DASHBOARD_CALLBACK setting                | WIRED   | `"DASHBOARD_CALLBACK": "apps.dashboard.views.dashboard_callback"` confirmed      |
| `baqsy/settings/base.py`                        | axes                                       | AXES_FAILURE_LIMIT=10 and AxesMiddleware          | WIRED   | AXES_FAILURE_LIMIT=10, AxesMiddleware last in MIDDLEWARE confirmed                |
| `apps/submissions/admin.py`                     | `apps/reports/views.py`                    | approve_and_send calls ApproveReportView.as_view() | WIRED | `approve_view = ApproveReportView.as_view()` present in action body               |
| `apps/reports/admin.py`                         | `apps/reports/views.py`                    | approve_and_send calls ApproveReportView.as_view() | WIRED | `approve_view = ApproveReportView.as_view()` present in action body               |
| `apps/industries/admin.py`                      | `apps/industries/models.py`                | save_model calls create_new_version()            | WIRED   | `QuestionnaireTemplate.create_new_version(obj)` called in save_model             |
| `apps/content/admin.py`                         | django_ckeditor_5                          | formfield_overrides with CKEditor5Widget         | WIRED   | `from django_ckeditor_5.widgets import CKEditor5Widget` and used in overrides     |
| `baqsy/urls.py`                                 | `apps/dashboard/urls.py`                   | path("admin/dashboard/") before admin/            | WIRED   | Dashboard URL registered first in urlpatterns, before admin/ catch-all           |

---

### Requirements Coverage

| Requirement | Source Plan | Description                                                        | Status    | Evidence                                                                    |
|-------------|------------|---------------------------------------------------------------------|-----------|-----------------------------------------------------------------------------|
| CRM-01      | 07-01      | Dashboard со счётчиками: всего заказов, в работе, завершённых, выручка | SATISFIED | dashboard_callback injects stats dict with 4 counters; tests pass           |
| CRM-02      | 07-01      | Фильтры дашборда: отрасль, регион, тариф, оборот, дата             | SATISFIED | _build_filters handles industry/tariff/city/date_from/date_to; HTMX wired  |
| CRM-03      | 07-02      | Список заказов с поиском и сортировкой по статусу                   | SATISFIED | search_fields, list_filter, list_per_page=25 in SubmissionAdmin             |
| CRM-04      | 07-02      | Карточка заказа: ответы + поле аудита + кнопка «Подтвердить»        | SATISFIED | AnswerInline + AuditReportInline + approve_and_send on both Submission and AuditReport admins |
| CRM-05      | 07-02      | Редактор отраслей (CRUD)                                            | SATISFIED | IndustryAdmin registered; test_industry_crud passes                         |
| CRM-06      | 07-02      | Редактор шаблонов анкет: новая версия при изменении, история        | SATISFIED | save_model with create_new_version(); has_change_permission for inactive   |
| CRM-07      | 07-02      | Редактор вопросов: drag-n-drop, типы полей, обязательность           | SATISFIED | SortableInlineAdminMixin in QuestionInline MRO; JS rendering needs browser  |
| CRM-08      | 07-02      | Редактор тарифов (цена, описание, активность)                       | SATISFIED | list_editable=("price_kzt","is_active") with list_display_links             |
| CRM-09      | 07-02      | Редактор контент-блоков лендинга (WYSIWYG)                          | SATISFIED | CKEditor5Widget in formfield_overrides; JS rendering needs browser          |
| CRM-10      | 07-01      | Вход по email+пароль с защитой от брутфорса                         | SATISFIED | AXES_FAILURE_LIMIT=10, AxesStandaloneBackend, test_lockout_after_failures   |

**Orphaned requirements check:** No requirements mapped to Phase 7 in REQUIREMENTS.md that are not covered by 07-01 or 07-02 plans.

---

### Anti-Patterns Found

No anti-patterns detected in key files. Scan of dashboard/views.py, submissions/admin.py, reports/admin.py, industries/admin.py, content/admin.py, payments/admin.py returned zero matches for TODO/FIXME/placeholder/return null/empty implementations.

---

### Human Verification Required

#### 1. django-unfold Tailwind UI Rendering

**Test:** Log in to /admin/ and confirm the sidebar with 5 navigation sections is visible, along with Tailwind-styled cards.
**Expected:** Sidebar shows Аналитика, Заказы, Контент, Конфигурация, Пользователи sections. Pages are styled with Tailwind (not Django's default admin CSS).
**Why human:** Template rendering and CSS loading cannot be verified from static code analysis alone.

#### 2. HTMX Filter Live Update

**Test:** On the dashboard, change the Отрасль dropdown. Confirm stats cards update without a full page reload.
**Expected:** Stats cards content changes in-place (HTMX partial swap). No browser navigation event fires.
**Why human:** Requires a running browser with HTMX loaded from unpkg CDN.

#### 3. Question Drag-and-Drop Reordering (CRM-07)

**Test:** Open a QuestionnaireTemplate change page. Try dragging question rows to reorder them.
**Expected:** Rows can be reordered by drag-and-drop; order is saved on form submit.
**Why human:** adminsortable2 JS drag-n-drop behavior cannot be verified without a running browser.

#### 4. CKEditor5 WYSIWYG Rendering (CRM-09)

**Test:** Open a ContentBlock change page. Confirm the content field shows a CKEditor5 toolbar (not a plain textarea).
**Expected:** Rich text editor with toolbar (bold, italic, link, lists, etc.) renders in place of the plain textarea.
**Why human:** CKEditor5 initialization is JavaScript-driven; widget presence is verified structurally but visual rendering needs browser.

#### 5. Approve and Send Button Pipeline

**Test:** Create a Submission with a linked AuditReport. Enter admin_text, click "Подтвердить и отправить PDF". Confirm success message appears and a Celery task is enqueued.
**Expected:** Green success message displayed; PDF generation Celery task visible in worker logs.
**Why human:** Requires a fully running system with Celery worker and connected delivery providers.

---

### Summary

Phase 7 goal is fully achieved at the code level. All 10 CRM requirements have substantive implementations:

- **CRM-01/02:** Dashboard app is complete with `dashboard_callback` injecting 4-key stats, HTMX endpoint wired at `/admin/dashboard/stats/`, filter form covering industry/tariff/city/date range.
- **CRM-03/04:** SubmissionAdmin has AnswerInline (read-only) + AuditReportInline + `approve_and_send` action calling `ApproveReportView.as_view()` correctly. AuditReportAdmin has the same approve action.
- **CRM-05:** IndustryAdmin registered with full CRUD.
- **CRM-06:** QuestionnaireTemplateAdmin.save_model calls `create_new_version()` for active templates; `has_change_permission` gates inactive templates as read-only.
- **CRM-07:** QuestionInline inherits `SortableInlineAdminMixin` for drag-n-drop ordering.
- **CRM-08:** TariffAdmin has `list_editable` for price_kzt and is_active with correct `list_display_links`.
- **CRM-09:** ContentBlockAdmin uses `CKEditor5Widget` via `formfield_overrides`.
- **CRM-10:** `AXES_FAILURE_LIMIT=10`, `AxesMiddleware` last in MIDDLEWARE, `AxesStandaloneBackend` first in `AUTHENTICATION_BACKENDS`, `test.py` with `AXES_ENABLED=False` for test isolation.

All 7 admin.py files use `unfold.admin.ModelAdmin` base classes. UNFOLD sidebar navigation configured with 5 sections and 9 links. Package versions pinned: django-unfold 0.90.0, django-axes 8.3.1, django-admin-sortable2 2.2.8, django-ckeditor-5 0.2.20.

5 items require human browser verification: Tailwind UI rendering, HTMX live filter, drag-n-drop, CKEditor JS, and the end-to-end approve+deliver pipeline. These are inherently visual/runtime behaviors with correct structural implementations confirmed.

---

_Verified: 2026-04-17T13:00:00Z_
_Verifier: Claude (gsd-verifier)_
