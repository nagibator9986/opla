# Phase 4: Payments - Context

**Gathered:** 2026-04-17
**Status:** Ready for planning
**Mode:** auto (YOLO)

<domain>
## Phase Boundary

Реализовать интеграцию с CloudPayments KZ: webhook-эндпоинты (Check + Pay) с HMAC-валидацией, идемпотентную обработку платежей, FSM-переход Submission в статус `paid`, Celery-таск уведомления бота об оплате (отправка deep-link для начала анкеты), upsell-логику (доплата за апгрейд тарифа).

**Не делаем:** React-страницу с виджетом (Phase 5 PAY-01), админку для возвратов (ручной процесс), авто-возвраты.

Требования: PAY-01..PAY-09 (9 штук). PAY-01 (CloudPayments Widget на React) — только backend-часть (webhook), фронт в Phase 5.

</domain>

<decisions>
## Implementation Decisions

### CloudPayments Webhook архитектура
- Два эндпоинта:
  - `POST /api/v1/payments/cloudpayments/check/` — Check notification (предварительная проверка)
  - `POST /api/v1/payments/cloudpayments/pay/` — Pay notification (факт успешной оплаты)
- Оба принимают `application/x-www-form-urlencoded` (CloudPayments шлёт form data, не JSON)
- Оба возвращают `{"code": 0}` для успеха, `{"code": 13, "reason": "..."}` для отказа
- CSRF exempt (`@csrf_exempt` или DRF `authentication_classes=[]`)
- `AllowAny` permission (внешний webhook)

### HMAC-валидация
- CloudPayments отправляет `Content-HMAC` header = `base64(HMAC-SHA256(body, api_secret))`
- `api_secret` = `CLOUDPAYMENTS_API_SECRET` из env
- Валидация через `hmac.compare_digest()` (constant-time comparison)
- Невалидный HMAC → HTTP 400 (не `{"code": 13}` — CloudPayments не должен ретраить)
- Тело запроса для HMAC = raw body bytes, не parsed form data

### Идемпотентность
- `Payment.transaction_id` уже `unique=True` (Phase 1)
- `get_or_create(transaction_id=...)` — если уже существует, возвращаем `{"code": 0}` без повторной обработки
- Для гарантии атомарности: `select_for_update()` на Submission при смене статуса

### Обработка Pay webhook
1. Проверить HMAC
2. `Payment.objects.get_or_create(transaction_id=data["TransactionId"], defaults={...})`
3. Если created=False → `{"code": 0}` (идемпотент, уже обработан)
4. Если created=True:
   - `Payment.status = "succeeded"`
   - `Payment.amount = data["Amount"]`
   - `Payment.raw_webhook = data` (весь payload)
   - Найти Submission по `InvoiceId` (мы передаём `submission_id` как `InvoiceId` в CP Widget)
   - `Submission.objects.select_for_update().get(id=submission_id)`
   - Вызвать FSM-переход `submission.mark_paid()` + `submission.save()`
   - Запустить Celery-таск `notify_bot_payment_success.delay(submission_id)`
5. Вернуть `{"code": 0}`

### Обработка Check webhook
- Check — предварительная проверка перед списанием
- Проверить HMAC
- Проверить что `InvoiceId` соответствует реальной Submission
- Проверить что Submission в допустимом статусе (не уже оплачена)
- Проверить что сумма совпадает с ценой тарифа
- `{"code": 0}` если всё ОК, `{"code": 13, "reason": "..."}` если нет

### Celery-таск уведомления бота (PAY-06)
- `notify_bot_payment_success(submission_id)`:
  1. Найти Submission + ClientProfile
  2. Вызвать FSM `submission.start_questionnaire()` + save
  3. POST в Telegram Bot API: `sendMessage` с текстом + inline-кнопкой deep-link `tg://resolve?domain=BaqsyBot&start=questionnaire_{submission_id}`
  4. Retry при ошибке Telegram API (max 3 retries с exp backoff)

### Upsell (PAY-08)
- Upsell = доплата 90 000 ₸ для перехода с Ashide 1 на Ashide 2 без повторной анкеты
- Эндпоинт: `POST /api/v1/payments/upsell/` с `{submission_id}` (JWT-protected)
- Проверяет: submission принадлежит клиенту, текущий тариф = ashide_1, статус ≥ completed
- Создаёт новый Payment с tariff=upsell, возвращает данные для CP Widget (amount, InvoiceId, Description)
- После оплаты upsell webhook обновляет `submission.tariff` на ashide_2

### Управление ценами (PAY-09)
- Цены уже в БД (Tariff model из Phase 1)
- Админ меняет через Django Admin (Phase 1)
- API-эндпоинт `GET /api/v1/tariffs/` — публичный список активных тарифов (для React)

### CloudPayments поля
- `InvoiceId` → `submission_id` (UUID)
- `Amount` → `tariff.price_kzt`
- `Currency` → `"KZT"`
- `Description` → `"Бизнес-аудит {tariff.title}: {client.company}"`
- `AccountId` → `client_profile_id`
- `Data.telegram_id` → для корреляции с ботом

### Claude's Discretion
- Точный формат логов для webhook-событий
- Структура тестовых webhook payload'ов
- Обработка edge case: Payment с Amount ≠ Tariff.price_kzt
- Тексты Telegram-сообщений об оплате
- Retry стратегия для Celery-таска (backoff timing)

</decisions>

<canonical_refs>
## Canonical References

### Project-level
- `CLAUDE.md` — идемпотентность webhooks, Celery для медленного
- `.planning/PROJECT.md` — тарифы (45000/135000/90000 ₸), CloudPayments KZ
- `.planning/REQUIREMENTS.md` — PAY-01..PAY-09
- `.planning/ROADMAP.md` — Phase 4 success criteria

### Prior phase decisions
- `.planning/phases/01-infrastructure-data-model/01-CONTEXT.md` — Payment model с unique transaction_id, Tariff model, Redis layout
- `.planning/phases/02-core-rest-api/02-CONTEXT.md` — DRF config, custom exception handler
- `.planning/phases/03-telegram-bot/03-CONTEXT.md` — bot deep-link pattern `questionnaire_{uuid}`, Celery → Telegram Bot API

### Research
- `.planning/research/ARCHITECTURE.md` — CloudPayments HMAC pattern, webhook idempotency
- `.planning/research/PITFALLS.md` — webhook race conditions, select_for_update
- `.planning/research/STACK.md` — no official CloudPayments Python SDK, custom HMAC

### Existing code
- `backend/apps/payments/models.py` — Tariff + Payment (transaction_id unique)
- `backend/apps/submissions/models.py` — Submission FSM (mark_paid, start_questionnaire transitions)
- `backend/apps/submissions/tasks.py` — remind_incomplete_submissions (pattern for new task)
- `backend/baqsy/settings/base.py` — CLOUDPAYMENTS_PUBLIC_ID, CLOUDPAYMENTS_API_SECRET in .env.example

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Payment model** — transaction_id unique, raw_webhook JSONField, Status choices — ready for webhook data
- **Submission FSM** — `mark_paid()` and `start_questionnaire()` transitions already defined
- **Tariff model** — price_kzt, code, is_active — ready for amount validation
- **Celery task pattern** — `remind_incomplete_submissions` in tasks.py — same structure for payment notification
- **IsBotAuthenticated** — NOT for webhooks (webhooks use HMAC, not bot token)

### Established Patterns
- DRF exception handler (`apps/core/exceptions.py`) — BUT webhooks return CP-specific format
- `select_for_update()` — recommended in PITFALLS.md for Payment creation
- Env vars via `django-environ` — CLOUDPAYMENTS_API_SECRET already in .env.example

### Integration Points
- `backend/apps/payments/` — add `views.py`, `urls.py`, `services.py` (HMAC validation)
- `backend/apps/core/api_urls.py` — add `path("payments/", include("apps.payments.urls"))`
- `backend/apps/submissions/tasks.py` — add `notify_bot_payment_success` task
- `.env.example` — verify CLOUDPAYMENTS vars present

</code_context>

<specifics>
## Specific Ideas

- CloudPayments шлёт form-encoded данные, не JSON — нужен `request.POST` или DRF parser
- `InvoiceId` = submission UUID — это связка между платёжным виджетом и нашей системой
- Webhook может прилететь многократно (CP ретраит до 100 раз) — идемпотентность критична
- Upsell НЕ требует повторной анкеты — только смена тарифа на submission

</specifics>

<deferred>
## Deferred Ideas

- React-страница с CloudPayments Widget — Phase 5 (WEB-03)
- Автоматические возвраты — out of scope
- Kaspi Pay отдельная интеграция — проверить в CP Dashboard, может работать через тот же Widget
- Webhook retry monitoring/alerting — Phase 8

</deferred>

---

*Phase: 04-payments*
*Context gathered: 2026-04-17*
