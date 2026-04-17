---
phase: 06-pdf-generation-delivery
verified: 2026-04-17T10:00:00Z
status: passed
score: 11/11 must-haves verified
re_verification: false
gaps: []
human_verification:
  - test: "Открыть presigned URL PDF в браузере"
    expected: "Корректный PDF с обложкой (имя клиента, компания, тариф), секцией аудита, ответами анкеты. Для ashide_2 — дополнительная секция «Расширенный анализ»."
    why_human: "WeasyPrint рендеринг с реальным libgobject не тестируется в CI (нет системных библиотек). Визуальное качество PDF (шрифты, отступы, page-break) требует просмотра."
  - test: "Нажать POST /api/v1/reports/{id}/approve/ от имени staff-пользователя"
    expected: "200 {\"status\": \"queued\"}, Celery chain запускается, через несколько секунд клиент получает сообщение в Telegram"
    why_human: "Требует реальный запущенный стек (Docker Compose + Redis + Celery worker + Telegram Bot Token)"
---

# Phase 06: PDF Generation & Delivery — Verification Report

**Phase Goal:** После подтверждения аудита администратором система автоматически генерирует именной PDF и доставляет его клиенту в Telegram и WhatsApp

**Verified:** 2026-04-17T10:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `generate_pdf(report_id)` создаёт PDF с именем клиента и компанией на обложке | VERIFIED | `audit_report.html:17` — `{{ client.name }}`, `{{ client.company }}`; `services.py:render_pdf` передаёт `client` в контекст; тест `test_render_pdf_includes_client_and_company` проверяет наличие в HTML |
| 2 | PDF для ashide_1 содержит 7–9 параметров, для ashide_2 — все параметры включая расширенные секции | VERIFIED | `audit_report.html:47` — `{% if tariff.code == 'ashide_2' %}` conditional block; тест `test_render_pdf_ashide2_extended_section` и `test_generate_pdf_ashide2_extended` |
| 3 | PDF загружается в MinIO и presigned URL сохраняется в `AuditReport.pdf_url` | VERIFIED | `services.py:upload_pdf_to_minio` — `s3.put_object` + `s3.generate_presigned_url`; `tasks.py:generate_pdf` — `report.pdf_url = presigned_url; report.save()`; тест `test_generate_pdf_creates_pdf` |
| 4 | Повторный вызов `generate_pdf` для отчёта с `pdf_url` не генерирует новый PDF | VERIFIED | `tasks.py:36` — `if report.pdf_url: return`; тест `test_generate_pdf_idempotent` мокирует boto3 и проверяет `assert_not_called()` |
| 5 | `POST /api/v1/reports/{id}/approve/` запускает Celery-цепочку генерации и доставки | VERIFIED | `views.py:80-87` — `chain(generate_pdf.s(...), group(deliver_telegram.si(...), deliver_whatsapp.si(...)))` + `workflow.delay()`; URL смонтирован в `api_urls.py` |
| 6 | `deliver_telegram` отправляет сопроводительный текст и PDF через Telegram Bot API sendDocument | VERIFIED | `delivery/tasks.py:80-100` — `sendMessage` с "Спасибо за обращение" перед `sendDocument`; тест `test_deliver_telegram_sends_text_first` и `test_deliver_telegram_sends_document` |
| 7 | `deliver_whatsapp` отправляет PDF через Wazzup24Provider с presigned URL в `contentUri` | VERIFIED | `delivery/tasks.py:154-165` — инстанциирует `Wazzup24Provider`, вызывает `send_document(phone, file_url, caption)`; `wazzup24.py:30` — `"contentUri": file_url`; тест `test_deliver_whatsapp_calls_provider` |
| 8 | `DeliveryLog` фиксирует статус `queued → delivered` для каждого канала | VERIFIED | `delivery/tasks.py` — `get_or_create(defaults={"status": QUEUED})` + `log_entry.status = DELIVERED; log_entry.save()`; тесты `test_deliver_telegram_creates_delivery_log`, `test_deliver_whatsapp_creates_delivery_log` |
| 9 | Временные ошибки (5xx, network) автоматически повторяются через Celery retry | VERIFIED | `delivery/tasks.py:50-57` — `autoretry_for=(RequestException,), max_retries=5, retry_backoff=True`; тест `test_deliver_telegram_retries_on_network_error` проверяет атрибут |
| 10 | После доставки в оба канала `Submission.status` переходит в `delivered` через `select_for_update` | VERIFIED | `delivery/tasks.py:43` — `Submission.objects.select_for_update().get(...)` + `sub.mark_delivered()`; тест `test_try_mark_delivered_both_channels` |
| 11 | Если у клиента нет WhatsApp-номера — WA-доставка пропускается с `DeliveryLog.status=failed` | VERIFIED | `delivery/tasks.py:129-140` — проверка `if not client.phone_wa` + `DeliveryLog` с `status=FAILED, error="no_phone_wa"`; тест `test_deliver_whatsapp_no_phone_skips` |

**Score:** 11/11 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/templates/pdf/audit_report.html` | Jinja2 шаблон с обложкой и conditional ashide_2 секцией | VERIFIED | 63 строки, содержит `{{ client.name }}`, `{{ client.company }}`, `tariff.code == 'ashide_2'`, `{{ report.admin_text \| safe }}`, loop по answers |
| `backend/templates/pdf/styles.css` | CSS для WeasyPrint (A4, фирменный стиль) | VERIFIED | 186 строк, `@page { size: A4; margin: 2cm; }`, `font-family`, `.cover-page`, `.answer-item`, `border-left: 3px solid #f59e0b` |
| `backend/apps/reports/services.py` | `render_pdf` + `upload_pdf_to_minio` + `_format_answer_value` | VERIFIED | Все три функции присутствуют, boto3 клиент создаётся внутри функции (fork-safety), `jinja2.FileSystemLoader` с `base_url` |
| `backend/apps/reports/tasks.py` | `generate_pdf` shared_task с идемпотентностью | VERIFIED | `@shared_task(name="reports.generate_pdf", bind=True, max_retries=3)`, идемпотентность на строке 36 |
| `backend/apps/reports/views.py` | `ApproveReportView` с `IsAdminUser` и Celery chain | VERIFIED | `permission_classes = [IsAdminUser]`, FSM transition, chain wiring |
| `backend/apps/reports/serializers.py` | `AuditReportSerializer` | VERIFIED | ModelSerializer с read-only полями |
| `backend/apps/reports/urls.py` | URL routing для reports | VERIFIED | `path("<int:report_id>/approve/", ...)` |
| `backend/apps/core/api_urls.py` | Включает `reports/` prefix | VERIFIED | `path("reports/", include("apps.reports.urls"))` на строке 14 |
| `backend/apps/delivery/tasks.py` | `deliver_telegram` + `deliver_whatsapp` + `_try_mark_delivered` | VERIFIED | Все три реализованы, не-заглушки. `autoretry_for=(RequestException,)` на обоих тасках |
| `backend/apps/delivery/providers/base.py` | `WhatsAppProvider` ABC | VERIFIED | `class WhatsAppProvider(ABC)` с `@abstractmethod def send_document` |
| `backend/apps/delivery/providers/wazzup24.py` | `Wazzup24Provider` implementation | VERIFIED | `BASE_URL = "https://api.wazzup24.com/v3/message"`, нормализация телефона, `contentUri` |
| `backend/apps/delivery/providers/__init__.py` | Экспортирует оба класса | VERIFIED | `__all__ = ["WhatsAppProvider", "Wazzup24Provider"]` |
| `backend/apps/reports/tests/test_tasks.py` | 11+ тестов PDF pipeline | VERIFIED | 11 тестов: format_filter × 5, render_pdf × 3, generate_pdf × 3 |
| `backend/apps/reports/tests/test_views.py` | 6+ тестов ApproveReportView | VERIFIED | 7 тестов: auth, empty_text, pipeline, FSM, idempotent, 404 |
| `backend/apps/delivery/tests/test_tasks.py` | 11+ тестов delivery tasks | VERIFIED | 11 тестов: telegram × 4, whatsapp × 3, _try_mark_delivered × 3, autoretry × 1 |
| `backend/apps/delivery/tests/test_providers.py` | 5 тестов WhatsApp providers | VERIFIED | 5 тестов: abstract guard, send_document, phone normalization, HTTP error, auth header |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `reports/tasks.py` | `templates/pdf/audit_report.html` | `jinja2.FileSystemLoader(settings.BASE_DIR / "templates" / "pdf")` | WIRED | `services.py:62-70` — FileSystemLoader + `env.get_template("audit_report.html")` |
| `reports/tasks.py` | MinIO S3 | `boto3.client.put_object` + `generate_presigned_url` | WIRED | `services.py:115-129` — `s3.put_object(...)` + `s3.generate_presigned_url(...)` |
| `reports/views.py` | `reports/tasks.py` | `chain(generate_pdf.s(...), group(deliver_telegram.si, deliver_whatsapp.si))` | WIRED | `views.py:80-87` — импорт + chain + group + `workflow.delay()` |
| `delivery/tasks.py` | Telegram Bot API | `requests.post sendMessage + sendDocument` | WIRED | `tasks.py:80-101` — два вызова `requests.post` с `sendMessage` и `sendDocument` |
| `delivery/tasks.py` | `delivery/providers/wazzup24.py` | `Wazzup24Provider.send_document()` | WIRED | `tasks.py:154` — `from apps.delivery.providers.wazzup24 import Wazzup24Provider`; `tasks.py:161-165` — `provider.send_document(...)` |
| `delivery/tasks.py` | `submissions/models.py` | `_try_mark_delivered → select_for_update → mark_delivered()` | WIRED | `tasks.py:43-46` — `Submission.objects.select_for_update().get(pk=...).mark_delivered()` |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| PDF-01 | 06-01 | Jinja2-шаблон Ashide 1 (7–9 параметров) | SATISFIED | `audit_report.html` содержит answers loop; `test_render_pdf_includes_client_and_company` |
| PDF-02 | 06-01 | Jinja2-шаблон Ashide 2 (18–24 параметра, расширенный) | SATISFIED | `{% if tariff.code == 'ashide_2' %}` conditional block; тест `test_render_pdf_ashide2_extended_section` |
| PDF-03 | 06-01 | WeasyPrint рендерит PDF в фирменном стиле с Cyrillic-шрифтами | SATISFIED | `services.py:89-93` — `HTML(string=html_str, base_url=...).write_pdf()`; `styles.css:17` — `font-family: "Liberation Sans", "Roboto", "DejaVu Sans"` (Cyrillic-capable) |
| PDF-04 | 06-01 | Имя клиента и название компании на обложке | SATISFIED | `audit_report.html:17-18` — `{{ client.name }}`, `{{ client.company }}`; `services.py:78-85` — client в контексте шаблона |
| PDF-05 | 06-01 | PDF сохраняется в MinIO с presigned URL (TTL ≥ 7 дней) | SATISFIED | `services.py:122-129` — `ExpiresIn=settings.AWS_QUERYSTRING_EXPIRE`; `settings.base:AWS_QUERYSTRING_EXPIRE = 60*60*24*7` (7 дней) |
| PDF-06 | 06-01 | Celery worker `--pool=prefork --max-tasks-per-child=5` для PDF | SATISFIED | `docker/docker-compose.yml` — `celery -A baqsy worker -Q default --pool=prefork --concurrency=2 --max-tasks-per-child=5` |
| PDF-07 | 06-01 | Таск идемпотентен: проверка `AuditReport.pdf_url` | SATISFIED | `tasks.py:36-38` — `if report.pdf_url: return`; тест `test_generate_pdf_idempotent` |
| DLV-01 | 06-02 | Отправка PDF в Telegram (sendDocument через Bot API) | SATISFIED | `delivery/tasks.py:94-101` — `sendDocument` с файлом `audit_report.pdf`; тест `test_deliver_telegram_sends_document` |
| DLV-02 | 06-02 | Отправка PDF в WhatsApp через Wazzup24 v3 API | SATISFIED | `wazzup24.py:21-39` — POST `https://api.wazzup24.com/v3/message` с `contentUri`; тест `test_wazzup24_send_document_success` |
| DLV-03 | 06-02 | Абстракция `WhatsAppProvider` с интерфейсом `send_document(phone, url, caption)` | SATISFIED | `providers/base.py` — `class WhatsAppProvider(ABC)` с `@abstractmethod`; тест `test_abstract_provider_cannot_instantiate` |
| DLV-04 | 06-02 | `DeliveryLog` фиксирует `queued → delivered` для каждого канала | SATISFIED | `delivery/tasks.py` — `get_or_create(defaults={"status": QUEUED})` + обновление в `DELIVERED`; тесты log tracking |
| DLV-05 | 06-02 | Retry через Celery при временных ошибках (5xx, network) | SATISFIED | `delivery/tasks.py:50-57` — `autoretry_for=(RequestException,), max_retries=5, retry_backoff=True`; тест `test_deliver_telegram_retries_on_network_error` |
| DLV-06 | 06-02 | Сопроводительный текст «Спасибо за обращение» перед PDF | SATISFIED | `delivery/tasks.py:80-87` — `sendMessage` с текстом "Спасибо за обращение! Ваш аудит-отчёт готов." перед `sendDocument`; тест `test_deliver_telegram_sends_text_first` |

**Orphaned requirements:** Нет. Все 13 ID из планов покрыты и присутствуют в REQUIREMENTS.md.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `delivery/tasks.py` | 14 | `BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")` на уровне модуля | Info | Безопасно для чтения env на уровне модуля (не IO-операция), но переменная будет пустой если env не установлен в момент импорта модуля. В prod это решается через Docker env. Нет блокера. |

Других анти-паттернов (TODO, FIXME, stub без реализации, empty return, console.log) в файлах фазы не обнаружено.

---

### Human Verification Required

#### 1. Визуальное качество PDF

**Test:** Запустить `docker-compose up`, создать AuditReport через admin, POST `/api/v1/reports/{id}/approve/`, дождаться завершения Celery task, открыть presigned URL из `AuditReport.pdf_url` в браузере.

**Expected:** PDF формата A4 с обложкой (имя клиента, компания, отрасль, тариф, дата), разделом аудита с текстом администратора, ответами анкеты в карточках с amber-полосой. Шрифты (Liberation Sans / Roboto / DejaVu Sans) корректно отображают кириллицу.

**Why human:** WeasyPrint требует системные библиотеки (libgobject, pango), недоступные в dev-среде без Docker. Тесты мокируют WeasyPrint — визуальное качество не может быть верифицировано автоматически.

#### 2. End-to-end Telegram доставка

**Test:** Запустить полный стек с реальным `TELEGRAM_BOT_TOKEN`, утвердить отчёт через API, подождать 30 секунд.

**Expected:** Клиент в Telegram получает два сообщения: сначала текст "Спасибо за обращение! Ваш аудит-отчёт готов.", затем PDF-файл `audit_report.pdf`.

**Why human:** Требует реального Bot Token и активной Telegram-сессии.

#### 3. WhatsApp доставка через Wazzup24

**Test:** Установить `WAZZUP24_API_KEY` и `WAZZUP24_CHANNEL_ID`, заполнить `client.phone_wa`, утвердить отчёт.

**Expected:** Клиент получает PDF в WhatsApp с подписью "Спасибо за обращение! Ваш аудит-отчёт готов."

**Why human:** Требует реального Wazzup24 API ключа и активного WhatsApp канала.

---

### Gaps Summary

Пробелов нет. Все 11 observable truths подтверждены, все 16 артефактов существуют и содержательны, все 6 key links проверены как работающие. Все 13 requirements (PDF-01..07, DLV-01..06) имеют конкретные свидетельства реализации в коде.

Единственное замечание уровня Info: `BOT_TOKEN` читается на уровне модуля `delivery/tasks.py` — стандартная практика, не блокер.

---

_Verified: 2026-04-17T10:00:00Z_
_Verifier: Claude (gsd-verifier)_
