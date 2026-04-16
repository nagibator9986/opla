# Phase 2: Core REST API - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning
**Mode:** auto (YOLO)

<domain>
## Phase Boundary

Создать полный REST API через Django REST Framework для двух потребителей: Telegram-бот (aiogram) и React-фронтенд. API покрывает: онбординг клиента, список отраслей, CRUD-цикл Submission + Answers, deep-link токены (UUID ↔ JWT), JWT-аутентификацию для клиентов и session-auth для админки.

**Не делаем в этой фазе:** Telegram-бот (Phase 3), CloudPayments webhooks (Phase 4), React-фронтенд (Phase 5), PDF-генерацию (Phase 6), CRM-расширения (Phase 7). Эндпоинты только создаются и тестируются через pytest, не через реальных потребителей.

Требования: API-01..API-11 (11 штук).

</domain>

<decisions>
## Implementation Decisions

### URL-структура и версионирование
- Все API-эндпоинты под префиксом `/api/v1/`
- Каждое приложение включает свои urls через `include("apps.{app}.urls")`
- Корневой `backend/baqsy/urls.py` подключает `api/v1/` namespace
- Маршруты:
  ```
  POST   /api/v1/bot/onboarding/           → создать/обновить ClientProfile
  POST   /api/v1/bot/deeplink/             → получить UUID-токен
  POST   /api/v1/bot/deeplink/exchange/    → обменять UUID на JWT
  GET    /api/v1/industries/               → список активных отраслей
  POST   /api/v1/submissions/              → создать Submission
  GET    /api/v1/submissions/{id}/         → статус заказа
  GET    /api/v1/submissions/{id}/next-question/  → следующий неотвеченный вопрос
  POST   /api/v1/submissions/{id}/answers/ → сохранить ответ
  POST   /api/v1/submissions/{id}/complete/ → пометить анкету завершённой
  ```

### Аутентификация
- **JWT (SimpleJWT)** для клиентов бота/фронта
  - Клиент получает JWT через deep-link exchange (UUID → JWT)
  - Access token TTL: 1 час, Refresh token TTL: 7 дней
  - Header: `Authorization: Bearer <token>`
- **Django session auth** для админки — уже работает из Phase 1
- `rest_framework.permissions.IsAuthenticated` для клиентских эндпоинтов
- `AllowAny` для: `bot/onboarding/`, `bot/deeplink/exchange/`, `industries/`
- Онбординг-эндпоинт (`/bot/onboarding/`) — внутренний для бота, защищён API-ключом в заголовке (`X-Bot-Token`) а не JWT

### Deep-link токены
- **Redis db=2** для хранения (решено в Phase 1 CONTEXT.md)
- Формат: `deeplink:{uuid}` → `{client_profile_id}`, TTL 30 минут
- `POST /api/v1/bot/deeplink/` — бот вызывает с `telegram_id`, получает UUID
- `POST /api/v1/bot/deeplink/exchange/` — React вызывает с UUID, получает JWT-пару (access + refresh), UUID удаляется из Redis (одноразовый)
- Если UUID истёк или не найден → 404

### Serializer-подход
- **ModelSerializer** с явным списком `fields` (никакого `__all__`)
- Отдельные serializer'ы для input/output где нужно (e.g., `SubmissionCreateSerializer` vs `SubmissionDetailSerializer`)
- Вложенные serializer'ы только для чтения (ответы клиента в Submission detail)
- `Answer.value` — JSONField, валидация типа ответа vs `question.field_type` на уровне serializer'а

### Ответы и ошибки
- DRF default `{detail: "..."}` для ошибок
- Custom exception handler для единообразного формата: `{"error": "код", "detail": "текст на русском"}`
- HTTP-статусы строго: 200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found
- Validation errors: `{"field_name": ["Ошибка"]}`

### Пагинация
- `PageNumberPagination` с `page_size=20` по умолчанию
- Применяется только к list-эндпоинтам (`industries/`, будущие admin-списки)
- Submission-эндпоинты — без пагинации (клиент видит только свои, их мало)

### Жизненный цикл Submission через API
- Создание: `POST /submissions/` с `{industry_id, tariff_id}` → ищет активный шаблон для отрасли, создаёт Submission, возвращает `{id, status, template_name, total_questions}`
- Следующий вопрос: `GET /submissions/{id}/next-question/` → первый неотвеченный вопрос (`{question_id, order, text, field_type, options, block}`) или `204 No Content` если все ответы есть
- Сохранение ответа: `POST /submissions/{id}/answers/` с `{question_id, value}` → валидирует тип ответа, сохраняет Answer, возвращает `{progress: "7/27"}`
- Завершение: `POST /submissions/{id}/complete/` → проверяет что все required вопросы отвечены, вызывает FSM-переход `complete_questionnaire()`, возвращает `{status: "completed"}`
- Клиент видит ТОЛЬКО свои Submissions (фильтр по JWT → ClientProfile)

### Уведомление бота после оплаты (заготовка)
- В Phase 2 создаём Celery-таск `notify_bot_payment_success(submission_id)` как **заглушку** (логирует в stdout)
- Реальная реализация (POST в Telegram Bot API) — Phase 4 (PAY-06)
- Таск вызывается из payment webhook handler'а, который тоже в Phase 4

### DRF конфигурация в settings
- `DEFAULT_AUTHENTICATION_CLASSES`: SimpleJWT + SessionAuthentication
- `DEFAULT_PERMISSION_CLASSES`: IsAuthenticated
- `DEFAULT_PAGINATION_CLASS`: PageNumberPagination, `PAGE_SIZE`: 20
- `DEFAULT_RENDERER_CLASSES`: JSONRenderer (без BrowsableAPIRenderer в prod)
- `SIMPLE_JWT`: access_lifetime=1h, refresh_lifetime=7d, rotate_refresh_tokens=True

### Claude's Discretion
- Точные имена ViewSet/APIView классов
- Структура test fixtures (factory-boy factories vs raw creation)
- Порядок полей в serializer'ах
- Точный формат progress-ответа (процент vs "N/M")
- Throttle rates для API (можно отложить до Phase 8)
- Swagger/OpenAPI документация (если нужна — Phase 8)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project-level
- `CLAUDE.md` — архитектура, принципы (Django-first, бот — тонкий клиент)
- `.planning/PROJECT.md` — Core Value, скоуп, Key Decisions
- `.planning/REQUIREMENTS.md` — требования API-01..API-11 с описанием каждого эндпоинта
- `.planning/ROADMAP.md` — Phase 2 success criteria

### Phase 1 context (prior decisions)
- `.planning/phases/01-infrastructure-data-model/01-CONTEXT.md` — Redis DB split (db=2 для deeplink), Custom User model, JWT для клиентов, session для админов
- `.planning/research/ARCHITECTURE.md` — deep-link UUID pattern, bot ↔ Django communication (REST only)
- `.planning/research/STACK.md` — SimpleJWT 5.5.1, DRF 3.17.1 versions

### Existing code (must read before implementing)
- `backend/apps/accounts/models.py` — BaseUser (email login) + ClientProfile (telegram_id, industry FK)
- `backend/apps/industries/models.py` — Industry, QuestionnaireTemplate, Question (field_type, options, block)
- `backend/apps/submissions/models.py` — Submission (FSM states, template FK immutable) + Answer (value JSONField, unique_together submission+question)
- `backend/apps/payments/models.py` — Tariff, Payment (transaction_id unique)
- `backend/baqsy/urls.py` — текущий urlconf (admin + health only)
- `backend/baqsy/settings/base.py` — INSTALLED_APPS, AUTH_USER_MODEL

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **TimestampedModel, UUIDModel** (apps/core/models.py) — все модели уже наследуют
- **BaseUser with email login** (apps/accounts) — готовый AUTH_USER_MODEL
- **FSM transitions** (apps/submissions/models.py) — `start_onboarding()`, `mark_paid()`, `start_questionnaire()`, `complete_questionnaire()`, `start_audit()`, `mark_delivered()` — API должен вызывать эти методы, не менять status напрямую
- **conftest.py** с `db_empty`, `frozen_now` fixtures
- **seed_initial** — 5 industries, 3 tariffs, demo templates — можно использовать в тестах

### Established Patterns
- **Django-fsm-2** для state transitions — API-эндпоинты вызывают transition-методы
- **JSONB для Answer.value** — serializer должен валидировать по `question.field_type`
- **unique_together на (submission, question)** — duplicate answer → 400, не 500
- **get_or_create** паттерн из seed — использовать в onboarding (ClientProfile по telegram_id)

### Integration Points
- `backend/baqsy/urls.py` — добавить `path("api/v1/", include(api_urls))`
- `backend/baqsy/settings/base.py` — добавить `rest_framework`, `rest_framework_simplejwt` в INSTALLED_APPS, DRF настройки
- Каждый app получает `urls.py`, `serializers.py`, `views.py`

</code_context>

<specifics>
## Specific Ideas

- Бот-эндпоинты (`/api/v1/bot/*`) защищены API-ключом (`X-Bot-Token`), а не JWT — бот сам не «клиент», он представляет клиента
- Deep-link flow: бот создаёт UUID → отправляет клиенту ссылку `https://baqsy.kz/auth/{uuid}` → React обменивает UUID на JWT → React логинит клиента
- `next-question` возвращает `204 No Content` когда все вопросы отвечены — это сигнал боту/фронту показать кнопку «Завершить»
- Answer validation по field_type: text → string, number → numeric, choice → one of options, multichoice → subset of options

</specifics>

<deferred>
## Deferred Ideas

- WebSocket для real-time уведомлений — не в скоупе, polling достаточно
- Swagger/OpenAPI автодокументация — Phase 8 (HARD-09)
- Throttle/rate limiting API — Phase 8 (HARD-05)
- Файловые загрузки в ответах (фото, документы) — v2

</deferred>

---

*Phase: 02-core-rest-api*
*Context gathered: 2026-04-16*
