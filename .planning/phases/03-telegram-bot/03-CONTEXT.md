# Phase 3: Telegram Bot - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning
**Mode:** auto (YOLO)

<domain>
## Phase Boundary

Реализовать Telegram-бот на aiogram 3.x как тонкий REST-клиент Django API. Бот покрывает: FSM-онбординг (5 базовых вопросов), выдачу deep-link на сайт с тарифами, прохождение отраслевой анкеты по одному вопросу, команды /status и /help, восстановление прогресса при обрыве, 24h-напоминание через Celery beat.

**Не делаем в этой фазе:** Оплату (Phase 4), React (Phase 5), PDF-генерацию (Phase 6), доставку отчёта через бота (Phase 6 DLV-01). Бот в этой фазе НЕ отправляет PDF — только проводит онбординг и анкету.

Требования: BOT-01..BOT-11 (11 штук).

</domain>

<decisions>
## Implementation Decisions

### Структура бота
- Директория `bot/handlers/` с модулями:
  - `start.py` — обработка `/start`, определение нового vs вернувшегося клиента
  - `onboarding.py` — FSM-сценарий 5 базовых вопросов
  - `questionnaire.py` — FSM-сценарий прохождения анкеты из N вопросов
  - `commands.py` — `/status`, `/help`
- `bot/states/` — FSM-состояния (StatesGroup для onboarding и questionnaire)
- `bot/services/api_client.py` — httpx-обёртка над Django REST API
- `bot/keyboards/` — InlineKeyboardMarkup-билдеры
- `bot/config.py` — чтение env через `python-decouple`
- `bot/main.py` — инициализация Bot, Dispatcher, RedisStorage, подключение handlers

### FSM-состояния (aiogram)
```
class OnboardingStates(StatesGroup):
    waiting_name = State()
    waiting_company = State()
    waiting_industry = State()    # inline keyboard
    waiting_phone = State()
    waiting_city = State()

class QuestionnaireStates(StatesGroup):
    answering = State()           # generic state, question data in FSM data
```
- FSM-состояния бота НЕ совпадают с Submission.status — бот управляет разговором, Django управляет бизнес-логикой
- FSM data хранит `submission_id`, `current_question_id`, `total_questions`, `answered_count`

### API-клиент (httpx)
- `bot/services/api_client.py` — async httpx.AsyncClient
- Base URL из env: `API_BASE_URL=http://web:8000/api/v1` (внутренний Docker URL)
- Заголовок `X-Bot-Token: {BOT_API_SECRET}` для bot-эндпоинтов
- Методы:
  - `onboard(telegram_id, name, company, industry_code, phone_wa, city)` → POST /bot/onboarding/
  - `create_deeplink(telegram_id)` → POST /bot/deeplink/
  - `get_industries()` → GET /industries/
  - `create_submission(industry_code, tariff_code, jwt_token)` → POST /submissions/
  - `get_next_question(submission_id, jwt_token)` → GET /submissions/{id}/next-question/
  - `save_answer(submission_id, question_id, value, jwt_token)` → POST /submissions/{id}/answers/
  - `complete_submission(submission_id, jwt_token)` → POST /submissions/{id}/complete/
  - `get_submission_status(submission_id, jwt_token)` → GET /submissions/{id}/
- Error handling: httpx.HTTPStatusError → пользователю «Ошибка, попробуйте позже»

### Онбординг (5 вопросов)
1. **Имя** → обычный текстовый ввод, валидация длины
2. **Название компании** → обычный текст
3. **Отрасль** → InlineKeyboardMarkup с кнопками из `GET /industries/`, CallbackQuery
4. **WhatsApp-номер** → текст, regex-валидация `+7...` или `8...`
5. **Город** → обычный текст
- После 5-го вопроса: вызов `POST /bot/onboarding/`, затем `POST /bot/deeplink/`
- Бот отправляет сообщение: «Спасибо! Для выбора тарифа перейдите на сайт:» + InlineKeyboardButton с URL

### Прохождение анкеты
- **Триггер:** после оплаты Celery-воркер вызывает `POST api.telegram.org/bot.../sendMessage` с текстом «Оплата прошла! Давайте заполним анкету.» + deep-link `tg://resolve?domain=BaqsyBot&start=questionnaire_{submission_id}`
- Бот при получении `/start questionnaire_{submission_id}`:
  1. Получает JWT через exchange (или использует сохранённый в FSM data)
  2. Вызывает `GET /submissions/{id}/next-question/`
  3. Показывает вопрос с прогрессом «Вопрос N/M»
  4. При ответе: `POST /submissions/{id}/answers/` → следующий вопрос
  5. Когда `204 No Content` → `POST /submissions/{id}/complete/`
  6. Сообщение: «Спасибо! Ваша анкета передана аудитору. Ожидайте результат.»
- **Представление вопросов по field_type:**
  - `text` → «Введите текстом:», обычный ввод
  - `number` → «Введите число:», валидация int/float
  - `choice` → InlineKeyboardMarkup с вариантами из `options.choices`
  - `multichoice` → InlineKeyboardMarkup с чекбоксами (toggle on callback), кнопка «Готово» для отправки

### Команды
- `/start` — entry point:
  - Новый пользователь → онбординг
  - Вернувшийся с незавершённой анкетой → «У вас есть незавершённая анкета. Продолжить?» (Да/Нет)
  - Вернувшийся без анкеты → «Добро пожаловать! Для новой анкеты перейдите на сайт:» + deep-link
  - `/start questionnaire_{submission_id}` → начать/продолжить анкету
- `/status` → показать статус последней Submission (или «У вас нет активных заказов»)
- `/help` → справочное сообщение: что делает бот, контакты поддержки

### Восстановление прогресса (BOT-10)
- При `/start` бот вызывает Django API, проверяет есть ли `Submission` в статусе `in_progress_full`
- Если есть → показывает следующий неотвеченный вопрос (resume)
- FSM-данные (submission_id, jwt) хранятся в RedisStorage(db=1) — если Redis перезапустился, бот восстанавливает контекст из Django API по telegram_id

### 24h-напоминание (BOT-11)
- Celery beat задача `remind_incomplete_submissions` запускается каждые 6 часов
- Находит Submissions с `status=in_progress_full` и `updated_at < now - 24h`
- Для каждой: вызывает Telegram Bot API `sendMessage` напрямую (sync requests из Celery)
- Текст: «У вас есть незавершённая анкета. Продолжите, чтобы получить аудит!» + deep-link на продолжение
- Не отправлять больше 1 напоминания в 24h (добавить `last_reminded_at` в Submission или отдельный timestamp)

### Уведомление об оплате (заготовка для Phase 4)
- В этой фазе: бот обрабатывает `/start questionnaire_{submission_id}` и начинает анкету
- В Phase 4: Celery-таск после оплаты отправит клиенту сообщение + deep-link
- Бот НЕ слушает webhook от CloudPayments — он просто реагирует на deep-link с submission_id

### Redis и Docker
- `RedisStorage.from_url(AIOGRAM_REDIS_URL)` где `AIOGRAM_REDIS_URL=redis://redis:6379/1`
- Long-polling в dev (Phase 1 docker-compose), webhook в prod (Phase 8)
- Bot container: `depends_on: web: condition: service_healthy` (бот не стартует без API)

### Claude's Discretion
- Точные тексты сообщений бота (в пределах русского языка)
- Обработка невалидного ввода (retry vs skip)
- Timeout для ответов пользователя (или без timeout)
- Emoji в сообщениях бота
- Порядок кнопок в inline-клавиатуре отраслей
- Точная структура `/help` текста

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project-level
- `CLAUDE.md` — бот = тонкий клиент, никакой бизнес-логики в bot/
- `.planning/PROJECT.md` — воронка, тарифы, Core Value
- `.planning/REQUIREMENTS.md` — BOT-01..BOT-11
- `.planning/ROADMAP.md` — Phase 3 success criteria

### Prior phase decisions
- `.planning/phases/01-infrastructure-data-model/01-CONTEXT.md` — Redis db=1 для FSM, db=2 для deeplink, Submission FSM states
- `.planning/phases/02-core-rest-api/02-CONTEXT.md` — API URL structure, bot auth via X-Bot-Token, deep-link flow, answer validation by field_type
- `.planning/research/ARCHITECTURE.md` — bot↔Django REST only, Celery→Telegram Bot API for notifications

### Existing code (MUST read)
- `bot/main.py` — Phase 1 skeleton (replace with real bot)
- `bot/pyproject.toml` — aiogram 3.27, httpx 0.27, redis 5.3 already installed
- `bot/Dockerfile` — minimal image, ready for bot code
- `backend/apps/accounts/views.py` — OnboardingView, DeeplinkCreateView (API the bot calls)
- `backend/apps/submissions/views.py` — SubmissionCreate, NextQuestion, AnswerCreate, Complete views
- `backend/apps/accounts/bot_urls.py` — bot API routes
- `docker/docker-compose.yml` — bot service config, depends_on web

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **bot/pyproject.toml** — aiogram 3.27, httpx 0.27, redis 5.3, structlog уже установлены
- **bot/Dockerfile** — минимальный образ, готов к расширению
- **Django API endpoints** — полный набор для бота уже реализован в Phase 2:
  - `POST /api/v1/bot/onboarding/` (X-Bot-Token)
  - `POST /api/v1/bot/deeplink/` (X-Bot-Token)
  - `GET /api/v1/industries/` (public)
  - `POST /api/v1/submissions/` (JWT)
  - `GET /api/v1/submissions/{uuid}/next-question/` (JWT)
  - `POST /api/v1/submissions/{uuid}/answers/` (JWT)
  - `POST /api/v1/submissions/{uuid}/complete/` (JWT)
  - `GET /api/v1/submissions/{uuid}/` (JWT)

### Established Patterns
- **X-Bot-Token** header для bot-эндпоинтов (Phase 2)
- **Synthetic user** email `tg_{telegram_id}@baqsy.internal` для JWT (Phase 2)
- **UUID primary key** для Submission — URL patterns `<uuid:pk>`
- **FSM transitions** через django-fsm-2 методы (не прямое присваивание status)

### Integration Points
- `bot/main.py` — заменить skeleton на реальный aiogram Dispatcher
- `bot/handlers/` — новая директория, подключается к Dispatcher через `dp.include_router()`
- `docker/docker-compose.yml` — bot service уже настроен, только код меняется
- Celery beat в `backend/` — добавить periodic task для 24h-напоминания

</code_context>

<specifics>
## Specific Ideas

- Бот должен быть **разговорным**, а не механическим — фразы типа «Отлично! Теперь расскажите...» между вопросами
- При выборе отрасли показывать кнопки, а не просить набирать текст — удобнее на мобильном
- Multichoice: показать кнопки-toggles (✅/❌), плюс кнопка «Готово» внизу для отправки
- Deep-link URL на сайт: `https://baqsy.kz/auth/{uuid}` — React обменяет на JWT (реализован в Phase 2)
- `/start questionnaire_{submission_id}` — бот проверяет что этот submission принадлежит текущему telegram_id

</specifics>

<deferred>
## Deferred Ideas

- Webhook mode для production — Phase 8 (HARD-06)
- Отправка PDF через бота — Phase 6 (DLV-01)
- Inline-mode для поиска — не в скоупе
- Групповой чат поддержки — не в скоупе
- Мультиязычность бота — v2

</deferred>

---

*Phase: 03-telegram-bot*
*Context gathered: 2026-04-16*
