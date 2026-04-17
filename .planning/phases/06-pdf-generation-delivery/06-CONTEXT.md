# Phase 6: PDF Generation & Delivery - Context

**Gathered:** 2026-04-17
**Status:** Ready for planning
**Mode:** auto (recommended defaults)

<domain>
## Phase Boundary

После подтверждения аудита администратором система автоматически генерирует именной PDF-отчёт через WeasyPrint и доставляет его клиенту в Telegram (sendDocument) и WhatsApp (Wazzup24). PDF сохраняется в MinIO с presigned URL. DeliveryLog фиксирует статус для каждого канала.

**Не делаем в этой фазе:** CRM-интерфейс для админа (Phase 7 — здесь только backend-логику генерации и доставки), CI/Sentry/rate limiting (Phase 8). «Подтвердить и отправить» — это API-эндпоинт, UI для него будет в Phase 7.

Требования: PDF-01..PDF-07 (7 штук) + DLV-01..DLV-06 (6 штук) = 13 требований.

</domain>

<decisions>
## Implementation Decisions

### PDF-шаблон (PDF-01, PDF-02, PDF-03, PDF-04)
- Один Jinja2 HTML-шаблон с условными секциями для Ashıde 1 и Ashıde 2
  - Ashıde 1: 7–9 параметров — короткий отчёт
  - Ashıde 2: 18–24 параметра — расширенный отчёт
  - Условие: `{% if tariff_code == 'ashide_2' %}` для дополнительных секций
- Обложка: имя клиента, название компании, отрасль, дата аудита, уровень тарифа
- Фирменный стиль: Cyrillic-шрифты (Liberation Sans, Roboto — уже в Docker), тёмные акценты (slate-900, amber-500)
- WeasyPrint рендерит HTML → PDF
- Шаблон в `backend/templates/pdf/audit_report.html`
- CSS в отдельном файле `backend/templates/pdf/styles.css` (или inline в шаблоне)

### Генерация PDF (PDF-05, PDF-06, PDF-07)
- Celery-таск `generate_pdf(report_id)`:
  1. Загрузить AuditReport + Submission + ClientProfile + Answers
  2. Проверить идемпотентность: если `report.pdf_url` уже установлен — пропустить (PDF-07)
  3. Рендерить Jinja2-шаблон с данными клиента
  4. WeasyPrint HTML → PDF (в памяти, BytesIO)
  5. Загрузить PDF в MinIO: `pdfs/{submission_id}/{timestamp}.pdf`
  6. Получить presigned URL (TTL ≥ 7 дней) (PDF-05)
  7. Обновить `report.pdf_url` и `report.status = 'approved'`
- Worker config: `--pool=prefork --max-tasks-per-child=5` для защиты от memory leak WeasyPrint (PDF-06)
- Jinja2 Environment: отдельный от Django templates (не {% load %}, а чистый Jinja2)

### Доставка в Telegram (DLV-01, DLV-04, DLV-05, DLV-06)
- Celery-таск `deliver_telegram(report_id)`:
  1. Загрузить AuditReport + Submission + ClientProfile
  2. Создать DeliveryLog(report=report, channel='telegram', status='queued')
  3. Отправить сопроводительный текст: «Спасибо за обращение! Ваш аудит-отчёт готов.» (DLV-06)
  4. Скачать PDF из MinIO (presigned URL → requests.get → bytes)
  5. Отправить через Telegram Bot API `sendDocument` (multipart/form-data с bytes)
  6. При успехе: `DeliveryLog.status = 'delivered'`, `DeliveryLog.external_id = message_id`
  7. Вызвать FSM `submission.mark_delivered()` + save (если оба канала доставлены)
- Retry: `autoretry_for=(RequestException,)`, `max_retries=5`, `retry_backoff=True` (DLV-05)

### Доставка в WhatsApp через Wazzup24 (DLV-02, DLV-03, DLV-05, DLV-06)
- Абстракция `WhatsAppProvider` с методом `send_document(phone, file_url, caption)` (DLV-03)
- Реализация `Wazzup24Provider`:
  - API: `POST https://api.wazzup24.com/v3/message` с `channelId`, `chatId` (phone), `file_url`, `text`
  - Авторизация: `Bearer {WAZZUP24_API_KEY}` header
  - `chatId` = `client.phone_wa` (WhatsApp номер из онбординга)
  - Ответ: `messageId` → сохранить в `DeliveryLog.external_id`
- Celery-таск `deliver_whatsapp(report_id)`:
  1. Создать DeliveryLog(report=report, channel='whatsapp', status='queued')
  2. Отправить сопроводительный текст + PDF через Wazzup24Provider
  3. При успехе: `DeliveryLog.status = 'delivered'`
  4. Retry аналогично Telegram (DLV-05)

### Оркестрация задач
- Триггер: API-эндпоинт `POST /api/v1/reports/{report_id}/approve/` (admin-only, session auth)
  - Устанавливает `report.status = 'approved'`, `report.approved_at = now()`
  - Вызывает FSM `submission.start_audit()` если ещё не вызван
  - Запускает Celery chain: `generate_pdf.s(report_id) | group(deliver_telegram.s(report_id), deliver_whatsapp.s(report_id))`
- Альтернатива chain: три отдельных таска, `deliver_*` проверяют наличие `pdf_url` перед доставкой и retry если нет
- Выбор: chain (рекомендуется — гарантирует порядок)

### FSM-переход mark_delivered
- `mark_delivered()` вызывается после ОБОИХ каналов доставки
- Проверка: оба DeliveryLog (telegram + whatsapp) имеют `status = 'delivered'`
- Каждый deliver-таск проверяет после своего успеха: если оба канала delivered → `mark_delivered()`
- Race condition: `select_for_update()` на Submission при вызове `mark_delivered()`

### Env-переменные
- `WAZZUP24_API_KEY` — уже в `.env.example`
- `WAZZUP24_CHANNEL_ID` — уже в `.env.example`
- `TELEGRAM_BOT_TOKEN` — уже используется в tasks.py
- MinIO: `MINIO_ENDPOINT_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` — уже настроены

### Claude's Discretion
- Точный дизайн PDF-шаблона (отступы, шрифты, размер текста)
- Формат presigned URL (path vs query params)
- Точные тексты сопроводительных сообщений
- Структура Jinja2 контекста (какие поля передать в шаблон)
- Обработка edge case: клиент без WhatsApp-номера (skip WA delivery)
- Exact retry timing (backoff factor)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project-level
- `CLAUDE.md` — WeasyPrint + Jinja2, MinIO, Celery для медленного, Wazzup24
- `.planning/PROJECT.md` — Core Value (путь до доставки), тарифы, дубль-доставка TG+WA
- `.planning/REQUIREMENTS.md` — PDF-01..PDF-07, DLV-01..DLV-06
- `.planning/ROADMAP.md` — Phase 6 success criteria

### Prior phase decisions
- `.planning/phases/01-infrastructure-data-model/01-CONTEXT.md` — AuditReport model, DeliveryLog model, MinIO bucket layout (`pdfs/{submission_id}/{timestamp}.pdf`), Celery worker config, WeasyPrint Docker setup
- `.planning/phases/02-core-rest-api/02-CONTEXT.md` — DRF config, session auth for admin
- `.planning/phases/03-telegram-bot/03-CONTEXT.md` — Telegram Bot API sendMessage pattern (existing in tasks.py)
- `.planning/phases/04-payments/04-CONTEXT.md` — Celery task pattern with retry, select_for_update for FSM

### Existing code (MUST read)
- `backend/apps/reports/models.py` — AuditReport (submission OneToOne, admin_text, pdf_url, status, approved_at)
- `backend/apps/delivery/models.py` — DeliveryLog (report FK, channel, status, external_id, error)
- `backend/apps/submissions/models.py` — Submission FSM (start_audit, mark_delivered transitions)
- `backend/apps/submissions/tasks.py` — notify_bot_payment_success (Celery + Telegram pattern to reuse)
- `backend/baqsy/settings/base.py` — S3/MinIO config (AWS_S3_ENDPOINT_URL, boto3)
- `backend/baqsy/celery.py` — Celery app config
- `docker/docker-compose.yml` — worker service with `--pool=prefork --max-tasks-per-child=5`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **AuditReport model** — OneToOne to Submission, `admin_text`, `pdf_url`, `status` (draft/approved/sent) — ready for PDF generation
- **DeliveryLog model** — FK to AuditReport, `channel` (telegram/whatsapp), `status` (queued/sent/delivered/failed), `external_id` — ready for delivery tracking
- **Submission FSM** — `start_audit()` (completed→under_audit), `mark_delivered()` (under_audit→delivered) — transitions ready
- **Celery task pattern** — `notify_bot_payment_success` in `submissions/tasks.py` — same structure (retry, Telegram API, error handling)
- **MinIO + django-storages** — S3-compatible config in settings.py, boto3 ready
- **WeasyPrint + fonts** — already in Docker image (Liberation Sans, DejaVu, Roboto + Pango)
- **Telegram Bot API** — already used for sendMessage, need to add sendDocument

### Established Patterns
- **Celery retry** — `autoretry_for`, `max_retries`, `retry_backoff` from payments tasks
- **select_for_update** — used in payment webhook for FSM transitions
- **Env vars** — django-environ, all MINIO/WAZZUP24/TELEGRAM vars already in `.env.example`
- **Requests library** — already used for Telegram API in tasks.py

### Integration Points
- `backend/apps/reports/` — add `views.py`, `serializers.py`, `urls.py`, `services.py` (PDF generation)
- `backend/apps/delivery/` — add `providers/` (WhatsAppProvider, Wazzup24Provider), `tasks.py`
- `backend/apps/reports/tasks.py` — add `generate_pdf` task
- `backend/apps/core/api_urls.py` — add `path("reports/", include("apps.reports.urls"))`
- `backend/templates/pdf/` — create directory, add `audit_report.html` + `styles.css`

</code_context>

<specifics>
## Specific Ideas

- PDF сохраняется в MinIO по пути `pdfs/{submission_id}/{timestamp}.pdf` (решение из Phase 1)
- Presigned URL с TTL ≥ 7 дней — клиент может скачивать PDF из кабинета (Phase 5 CabinetPage уже показывает кнопку)
- Wazzup24 API v3 — POST /v3/message с Bearer token, отправка файла по URL (не upload)
- Дубль-доставка TG+WA — явное требование заказчика, оба канала обязательны
- Сопроводительный текст перед PDF — «Спасибо за обращение!» (DLV-06)
- Worker с `--max-tasks-per-child=5` — WeasyPrint может течь памятью (из Phase 1 pitfalls research)

</specifics>

<deferred>
## Deferred Ideas

- Email-канал доставки — v2 (EMAIL-01)
- Автоматические возвраты — out of scope
- AI-предварительный анализ ответов — v2 (AI-01)
- Watermark на PDF — не обсуждалось
- PDF preview в браузере — Phase 7 CRM мог бы показывать preview

</deferred>

---

*Phase: 06-pdf-generation-delivery*
*Context gathered: 2026-04-17*
