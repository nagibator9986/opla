---
phase: 06-pdf-generation-delivery
plan: 01
subsystem: api
tags: [pdf, weasyprint, jinja2, celery, minio, boto3, s3, reports]

requires:
  - phase: 01-infrastructure-data-model
    provides: AuditReport, Submission, ClientProfile, DeliveryLog models; docker-compose with MinIO
  - phase: 02-core-rest-api
    provides: DRF setup, IsAdminUser permission, api_urls.py routing
  - phase: 04-payments
    provides: Tariff model with code field (ashide_1, ashide_2, upsell)

provides:
  - Jinja2 PDF шаблон audit_report.html с обложкой, ответами и conditional ashide_2 секцией
  - CSS styles.css для WeasyPrint (A4, amber accent, answer-item border-left)
  - render_pdf(report) -> bytes через Jinja2 + WeasyPrint
  - upload_pdf_to_minio(pdf_bytes, submission_id) -> presigned_url через boto3
  - _format_answer_value Jinja2 filter: {text/number/choice/choices} -> str
  - generate_pdf Celery shared_task с идемпотентностью по pdf_url
  - ApproveReportView POST /api/v1/reports/{id}/approve/ (IsAdminUser, FSM, Celery chain)
  - deliver_telegram + deliver_whatsapp task stubs для Plan 02

affects:
  - 06-pdf-generation-delivery/06-02 (delivery tasks implement stubs from this plan)
  - Phase 07 (admin CRM calls ApproveReportView)

tech-stack:
  added:
    - jinja2 (Jinja2.Environment + FileSystemLoader для PDF templates)
    - boto3 (S3 client для MinIO upload + presigned URL)
    - weasyprint (HTML-to-PDF, system libs required in Docker)
  patterns:
    - boto3 client создаётся внутри функции (не на уровне модуля) для fork-safety в Celery prefork
    - Jinja2 environment отдельно от Django templates — autoescape=True + custom filter
    - base_url=templates_dir даёт WeasyPrint доступ к styles.css по relative path из HTML
    - Celery chain: generate_pdf.s → group(deliver_telegram.si, deliver_whatsapp.si) — .si() immutable signature

key-files:
  created:
    - backend/templates/pdf/audit_report.html
    - backend/templates/pdf/styles.css
    - backend/apps/reports/services.py
    - backend/apps/reports/tasks.py
    - backend/apps/reports/views.py
    - backend/apps/reports/serializers.py
    - backend/apps/reports/urls.py
    - backend/apps/delivery/tasks.py
    - backend/apps/reports/tests/test_tasks.py
    - backend/apps/reports/tests/test_views.py
  modified:
    - backend/apps/core/api_urls.py

key-decisions:
  - "boto3 client создаётся внутри функции upload_pdf_to_minio (не на уровне модуля) — fork-safety для Celery prefork workers"
  - "Jinja2 custom filter format_answer_value извлекает значения из typed dict {text/number/choice/choices}"
  - "WeasyPrint base_url=templates_dir позволяет найти styles.css по relative path без абсолютного URL"
  - "deliver_telegram/deliver_whatsapp — stubs в этом плане, полная реализация в Plan 02"
  - "Тесты на dev-маке мокируют weasyprint через sys.modules pre-injection (OSError если libgobject не установлен)"
  - "ApproveReportView: idempotent FSM — если submission уже under_audit, пропускаем transition без ошибки"

patterns-established:
  - "PDF-idempotency: если report.pdf_url уже установлен, generate_pdf возвращает без генерации (PDF-07)"
  - "Celery chain с group: generate_pdf.s + group(deliver_*.si) — .si() чтобы deliver_* не ждали результата generate_pdf"
  - "sys.modules pre-injection в тестах для библиотек с нативными зависимостями (weasyprint, boto3)"

requirements-completed: [PDF-01, PDF-02, PDF-03, PDF-04, PDF-05, PDF-06, PDF-07]

duration: 4min
completed: 2026-04-17
---

# Phase 06 Plan 01: PDF Generation & Approve API Summary

**Jinja2+WeasyPrint PDF pipeline с MinIO storage, generate_pdf Celery task с идемпотентностью, и ApproveReportView запускающий chain generate → deliver**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-17T09:28:45Z
- **Completed:** 2026-04-17T09:33:00Z
- **Tasks:** 2
- **Files modified:** 10 created + 1 modified

## Accomplishments

- Jinja2 PDF шаблон с обложкой (имя клиента, компания, отрасль, тариф, дата) и conditional ashide_2 секцией
- generate_pdf Celery shared_task: рендеринг через WeasyPrint, загрузка в MinIO, сохранение presigned URL — идемпотентный по pdf_url
- ApproveReportView: staff-only, FSM completed→under_audit, Celery chain с доставкой — 20 тестов проходят

## Task Commits

Each task was committed atomically:

1. **Task 1: Jinja2 PDF template + CSS + generate_pdf + services** - `b45d6c3` (feat)
2. **Task 2: ApproveReportView + URL wiring + delivery stubs + tests** - `14d41b9` (feat)

**Plan metadata:** (see final commit below)

## Files Created/Modified

- `backend/templates/pdf/audit_report.html` — Jinja2 шаблон: обложка, audit_section, answers loop, ashide_2 conditional block
- `backend/templates/pdf/styles.css` — WeasyPrint CSS: @page A4, cover-page, answer-item border-left amber, extended-section
- `backend/apps/reports/services.py` — render_pdf (Jinja2+WeasyPrint→bytes), upload_pdf_to_minio (boto3 S3), _format_answer_value filter
- `backend/apps/reports/tasks.py` — generate_pdf shared_task name="reports.generate_pdf", идемпотентность, retry 3x
- `backend/apps/reports/views.py` — ApproveReportView: IsAdminUser, admin_text validation, FSM transition, Celery chain
- `backend/apps/reports/serializers.py` — AuditReportSerializer (read-only fields)
- `backend/apps/reports/urls.py` — path("<int:report_id>/approve/", ...)
- `backend/apps/delivery/tasks.py` — deliver_telegram + deliver_whatsapp stubs для Plan 02
- `backend/apps/core/api_urls.py` — добавлен path("reports/", include("apps.reports.urls"))
- `backend/apps/reports/tests/test_tasks.py` — 11 тестов: format_filter, render_pdf, idempotency, ashide2
- `backend/apps/reports/tests/test_views.py` — 7 тестов: auth, FSM, pipeline, idempotency, 404

## Decisions Made

- boto3 client создаётся внутри функции (не модульный уровень) — fork-safety для Celery prefork
- Jinja2 отдельно от Django template engine — custom filter `format_answer_value` для Answer.value typed dict
- WeasyPrint `base_url=templates_dir` для resolve relative CSS URL
- `.si()` (immutable signature) для deliver_* в chain — они получают report_id напрямую, не из результата generate_pdf
- Тесты: sys.modules pre-injection для weasyprint/boto3 на dev машинах без системных библиотек

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] sys.modules pre-injection для weasyprint и boto3 в тестах**
- **Found during:** Task 1 (test execution)
- **Issue:** WeasyPrint падал с OSError (libgobject не установлен на macOS), boto3 с ModuleNotFoundError — `patch("weasyprint.HTML")` не мог патчить несуществующий модуль
- **Fix:** Добавлен `_ensure_module_mocks()` в оба тестовых файла — injecting fake ModuleType в sys.modules до выполнения тестов
- **Files modified:** test_tasks.py, test_views.py
- **Verification:** `20 passed` в полном прогоне apps/reports/
- **Committed in:** b45d6c3 (Task 1), 14d41b9 (Task 2)

---

**Total deviations:** 1 auto-fixed (Rule 1 — Bug fix for test environment compatibility)
**Impact on plan:** Тест-инфраструктурный фикс, не влияет на prod-код. В Docker контейнере WeasyPrint и boto3 установлены нормально.

## Issues Encountered

- WeasyPrint требует системные библиотеки (libgobject, pango) которых нет на macOS без brew. В prod Docker образе они установлены. Решено через sys.modules mock injection в тестах.

## User Setup Required

None — MinIO credentials из .env.example, конфигурация инфраструктуры выполнена в Phase 01.

## Next Phase Readiness

- generate_pdf таск готов к использованию в prod (идемпотентный, с retry)
- ApproveReportView готов: staff может утверждать отчёты и запускать pipeline
- deliver_telegram/deliver_whatsapp stubs на месте — Plan 02 заменяет логику без изменения сигнатуры
- Шаблон PDF можно расширять (Phase 06 Plan 02 может добавить delivery-специфичный footer)

---
*Phase: 06-pdf-generation-delivery*
*Completed: 2026-04-17*
