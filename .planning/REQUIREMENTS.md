# Requirements: Baqsy System

**Defined:** 2026-04-15
**Core Value:** Клиент платит за персональный PDF-аудит своего бизнеса и получает его автоматически после ручной проверки администратором — весь путь от первого контакта до доставки отчёта должен работать безотказно.

## v1 Requirements

### Infrastructure (INFRA)

- [x] **INFRA-01**: Docker Compose разворачивает полную стек (web, bot, worker, beat, db, redis, nginx, minio) одной командой
- [x] **INFRA-02**: Проект запускается в dev-окружении через `docker-compose up` без дополнительных шагов
- [x] **INFRA-03**: Все секреты (токены, ключи) читаются из `.env`, в репо только `.env.example`
- [x] **INFRA-04**: Django миграции автоматически применяются при старте web-контейнера
- [x] **INFRA-05**: Docker образ содержит системные шрифты для Cyrillic (Liberation Sans, Roboto) для WeasyPrint
- [x] **INFRA-06**: PostgreSQL бэкапится по cron в MinIO ежедневно
- [x] **INFRA-07**: README содержит инструкцию развёртывания на новом хостинге за ≤2 часа

### Data Model (DATA)

- [x] **DATA-01**: Модель `Industry` (список отраслей: Ритейл, IT, Производство, Услуги, F&B, …)
- [x] **DATA-02**: Модель `QuestionnaireTemplate` с полями `industry_id`, `version`, `is_active`, `name`
- [x] **DATA-03**: Модель `Question` с полями `template_id`, `order`, `text`, `field_type`, `options` (JSONB), `required`, `block`
- [x] **DATA-04**: Модель `ClientProfile` с `telegram_id`, `name`, `company`, `phone_wa`, `city`, `industry_id`
- [x] **DATA-05**: Модель `Submission` с `client_id`, `template_id` (FK на версию), `status`, `created_at`, `completed_at`
- [x] **DATA-06**: Модель `Answer` с `submission_id`, `question_id`, `value` (JSONB), `answered_at`
- [x] **DATA-07**: Модель `Tariff` с `code`, `title`, `price_kzt`, `description`, `is_active`
- [x] **DATA-08**: Модель `Payment` с `submission_id`, `tariff_id`, `transaction_id` (unique), `status`, `amount`, `raw_webhook` (JSONB)
- [x] **DATA-09**: Модель `AuditReport` с `submission_id`, `admin_text`, `pdf_url`, `status`, `approved_at`
- [x] **DATA-10**: Модель `DeliveryLog` с `report_id`, `channel`, `status`, `external_id`, `error`
- [x] **DATA-11**: Модель `ContentBlock` для текстов лендинга (key-value с HTML-контентом)
- [x] **DATA-12**: Версионирование `QuestionnaireTemplate`: любое редактирование создаёт новую версию, активная ровно одна
- [x] **DATA-13**: `Submission.template_id` не меняется после создания (проверка в `save()`)

### REST API (API)

- [x] **API-01**: JWT-аутентификация для клиента (SimpleJWT)
- [x] **API-02**: Django session-auth для админки
- [x] **API-03**: `POST /api/bot/onboarding/` — создаёт/обновляет `ClientProfile` по `telegram_id`
- [x] **API-04**: `GET /api/industries/` — список активных отраслей
- [x] **API-05**: `POST /api/submissions/` — создаёт `Submission` с выбранным тарифом и отраслью
- [x] **API-06**: `GET /api/submissions/{id}/next-question/` — возвращает следующий неотвеченный вопрос
- [x] **API-07**: `POST /api/submissions/{id}/answers/` — сохраняет ответ на конкретный вопрос
- [x] **API-08**: `POST /api/submissions/{id}/complete/` — помечает анкету завершённой
- [x] **API-09**: `GET /api/submissions/{id}/` — статус заказа для клиента
- [x] **API-10**: `POST /api/bot/deeplink/` — выдаёт одноразовый UUID-токен для перехода из бота на сайт
- [x] **API-11**: `POST /api/bot/deeplink/exchange/` — обменивает UUID-токен на JWT клиента (на сайте)

### Telegram Bot (BOT)

- [x] **BOT-01**: Бот стартует через `docker-compose up`, использует aiogram 3.27 + Redis FSM storage (db=1)
- [x] **BOT-02**: Команда `/start` запускает FSM-сценарий онбординга
- [x] **BOT-03**: Онбординг задаёт 5 вопросов: имя, компания, отрасль (выбор из inline-клавиатуры), WhatsApp-номер, город
- [x] **BOT-04**: После онбординга бот выдаёт deep-link на сайт с тарифами
- [x] **BOT-05**: Бот реагирует на сигнал об успешной оплате и начинает задавать вопросы из анкеты по одному
- [x] **BOT-06**: Каждый ответ сразу отправляется в Django API (нет локального кэша)
- [x] **BOT-07**: Прогресс-индикатор в каждом сообщении («Вопрос 7/27»)
- [x] **BOT-08**: Команда `/status` показывает текущий статус заказа
- [x] **BOT-09**: Команда `/help` показывает справку
- [x] **BOT-10**: При обрыве FSM бот восстанавливает прогресс из Django при следующем `/start`
- [x] **BOT-11**: Напоминание через 24 часа если анкета не завершена (Celery beat)

### Payments (PAY)

- [x] **PAY-01**: CloudPayments Widget встроен на странице тарифа (React)
- [x] **PAY-02**: `POST /api/payments/cloudpayments/webhook/check/` — Check webhook с HMAC-валидацией
- [x] **PAY-03**: `POST /api/payments/cloudpayments/webhook/pay/` — Pay webhook с HMAC-валидацией
- [x] **PAY-04**: Webhook идемпотентен: дубликаты по `TransactionId` не создают новый `Payment`
- [x] **PAY-05**: При успешной оплате `Submission.status` переходит в `paid` через `select_for_update`
- [x] **PAY-06**: Celery-таск уведомляет бота о начале анкеты после `paid`
- [x] **PAY-07**: Поддержка Kaspi Pay через CloudPayments Widget (проверить активацию в кабинете CP)
- [x] **PAY-08**: Upsell: кнопка доплаты 90 000 ₸ апгрейдит тариф без повторной анкеты
- [x] **PAY-09**: Цены тарифов редактируются в админке без деплоя

### Frontend (WEB)

- [x] **WEB-01**: Лендинг на React 18 + Vite + TypeScript + Tailwind
- [x] **WEB-02**: Секции лендинга: hero, метод, тарифы, кейсы, FAQ — тексты из `ContentBlock`
- [x] **WEB-03**: Страница тарифов с CloudPayments Widget и выбором Ashıde 1 / Ashıde 2
- [x] **WEB-04**: Страница клиентского кабинета со статусом заказа и ссылкой на PDF
- [x] **WEB-05**: Кнопка Upsell в кабинете клиентов с тарифом Ashıde 1
- [x] **WEB-06**: Deep-link landing: React обменивает UUID на JWT и логинит клиента
- [x] **WEB-07**: Адаптивная вёрстка (mobile-first)
- [x] **WEB-08**: TanStack Query для fetch, Zustand для клиентского state

### PDF Generation (PDF)

- [x] **PDF-01**: Jinja2-шаблон Ashıde 1 (7–9 параметров, короткий отчёт)
- [x] **PDF-02**: Jinja2-шаблон Ashıde 2 (18–24 параметра, расширенный отчёт)
- [x] **PDF-03**: WeasyPrint рендерит PDF в фирменном стиле с Cyrillic-шрифтами
- [x] **PDF-04**: Имя клиента и название компании подставляются в заголовок и на обложку
- [x] **PDF-05**: Сгенерированный PDF сохраняется в MinIO с presigned URL (TTL ≥ 7 дней)
- [x] **PDF-06**: Celery-воркер `--pool=prefork --max-tasks-per-child=5` для PDF (защита от memory leak)
- [x] **PDF-07**: Таск идемпотентен: проверка `AuditReport.pdf_url` перед генерацией

### Delivery (DLV)

- [x] **DLV-01**: Отправка PDF в Telegram после подтверждения админа (sendDocument через Bot API)
- [x] **DLV-02**: Отправка PDF в WhatsApp через Wazzup24 v3 API
- [x] **DLV-03**: Абстракция `WhatsAppProvider` с интерфейсом `send_document(phone, url, caption)`
- [x] **DLV-04**: `DeliveryLog` фиксирует `queued → delivered` для каждого канала
- [x] **DLV-05**: Retry через Celery при временных ошибках доставки (5xx, network)
- [x] **DLV-06**: Сопроводительный текст «Спасибо за обращение» отправляется перед PDF

### Admin CRM (CRM)

- [x] **CRM-01**: Dashboard со счётчиками: всего заказов, в работе, завершённых, выручка за период
- [x] **CRM-02**: Фильтры дашборда: отрасль, регион, тариф, оборот, дата
- [ ] **CRM-03**: Список заказов с поиском и сортировкой по статусу
- [ ] **CRM-04**: Карточка заказа: слева все ответы клиента, справа поле для аудита, снизу кнопка «Подтвердить и отправить»
- [ ] **CRM-05**: Редактор отраслей (CRUD)
- [ ] **CRM-06**: Редактор шаблонов анкет: создание новой версии при изменении, просмотр истории
- [ ] **CRM-07**: Редактор вопросов внутри шаблона (порядок drag-n-drop, типы полей, обязательность)
- [ ] **CRM-08**: Редактор тарифов (цена, описание, активность)
- [ ] **CRM-09**: Редактор контент-блоков лендинга (WYSIWYG)
- [x] **CRM-10**: Вход админа по email+пароль с защитой от брутфорса (django-axes)

### Hardening (HARD)

- [ ] **HARD-01**: Structured logging через structlog (JSON в prod)
- [ ] **HARD-02**: Sentry интеграция для ошибок (бэкенд + бот + фронт)
- [ ] **HARD-03**: GitHub Actions CI: pytest + ruff + mypy + npm test + npm build
- [ ] **HARD-04**: nginx с TLS (Let's Encrypt через certbot)
- [ ] **HARD-05**: Rate limiting на публичных эндпоинтах (django-ratelimit)
- [ ] **HARD-06**: Бот в production работает через webhook, не long-polling
- [ ] **HARD-07**: Health-check endpoints для каждого сервиса
- [ ] **HARD-08**: Seed-скрипт с минимум 3 отраслями и демо-шаблонами
- [ ] **HARD-09**: Документация: ARCHITECTURE.md (модель данных + потоки) и DEPLOYMENT.md

## v2 Requirements

### Future Features

- **LANG-01**: Мультиязычность KZ/EN
- **AI-01**: AI-помощник для предварительного анализа ответов
- **EMAIL-01**: Email-канал доставки
- **REFUND-01**: Автоматические возвраты
- **SEGMENT-01**: Сегментированные email-рассылки клиентам
- **ANALYTICS-01**: Экспорт статистики в CSV/Excel
- **A11Y-01**: Полный WCAG 2.1 AA для лендинга
- **SSO-01**: OAuth-вход для админов (Google Workspace)

## Out of Scope

| Feature | Reason |
|---------|--------|
| AI-генерация аудита | Требование заказчика — аудит пишет человек |
| Мобильное приложение | Web + Telegram покрывают канал |
| Оплата в USD напрямую | CloudPayments KZ работает только в KZT |
| Мультитенантность / white-label | Один экземпляр системы |
| Реал-тайм чат с аудитором | Коммуникация асинхронная через бота |
| Свой платёжный шлюз | CloudPayments достаточно |
| Email-рассылки | v2, на MVP только TG + WA |
| OAuth для клиентов | Идентификация по telegram_id достаточна |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFRA-01 | Phase 1: Infrastructure & Data Model | Complete |
| INFRA-02 | Phase 1: Infrastructure & Data Model | Complete |
| INFRA-03 | Phase 1: Infrastructure & Data Model | Complete |
| INFRA-04 | Phase 1: Infrastructure & Data Model | Complete |
| INFRA-05 | Phase 1: Infrastructure & Data Model | Complete |
| INFRA-06 | Phase 1: Infrastructure & Data Model | Complete |
| INFRA-07 | Phase 1: Infrastructure & Data Model | Complete |
| DATA-01 | Phase 1: Infrastructure & Data Model | Complete |
| DATA-02 | Phase 1: Infrastructure & Data Model | Complete |
| DATA-03 | Phase 1: Infrastructure & Data Model | Complete |
| DATA-04 | Phase 1: Infrastructure & Data Model | Complete |
| DATA-05 | Phase 1: Infrastructure & Data Model | Complete |
| DATA-06 | Phase 1: Infrastructure & Data Model | Complete |
| DATA-07 | Phase 1: Infrastructure & Data Model | Complete |
| DATA-08 | Phase 1: Infrastructure & Data Model | Complete |
| DATA-09 | Phase 1: Infrastructure & Data Model | Complete |
| DATA-10 | Phase 1: Infrastructure & Data Model | Complete |
| DATA-11 | Phase 1: Infrastructure & Data Model | Complete |
| DATA-12 | Phase 1: Infrastructure & Data Model | Complete |
| DATA-13 | Phase 1: Infrastructure & Data Model | Complete |
| API-01 | Phase 2: Core REST API | Complete |
| API-02 | Phase 2: Core REST API | Complete |
| API-03 | Phase 2: Core REST API | Complete |
| API-04 | Phase 2: Core REST API | Complete |
| API-05 | Phase 2: Core REST API | Complete |
| API-06 | Phase 2: Core REST API | Complete |
| API-07 | Phase 2: Core REST API | Complete |
| API-08 | Phase 2: Core REST API | Complete |
| API-09 | Phase 2: Core REST API | Complete |
| API-10 | Phase 2: Core REST API | Complete |
| API-11 | Phase 2: Core REST API | Complete |
| BOT-01 | Phase 3: Telegram Bot | Complete |
| BOT-02 | Phase 3: Telegram Bot | Complete |
| BOT-03 | Phase 3: Telegram Bot | Complete |
| BOT-04 | Phase 3: Telegram Bot | Complete |
| BOT-05 | Phase 3: Telegram Bot | Complete |
| BOT-06 | Phase 3: Telegram Bot | Complete |
| BOT-07 | Phase 3: Telegram Bot | Complete |
| BOT-08 | Phase 3: Telegram Bot | Complete |
| BOT-09 | Phase 3: Telegram Bot | Complete |
| BOT-10 | Phase 3: Telegram Bot | Complete |
| BOT-11 | Phase 3: Telegram Bot | Complete |
| PAY-01 | Phase 4: Payments | Complete |
| PAY-02 | Phase 4: Payments | Complete |
| PAY-03 | Phase 4: Payments | Complete |
| PAY-04 | Phase 4: Payments | Complete |
| PAY-05 | Phase 4: Payments | Complete |
| PAY-06 | Phase 4: Payments | Complete |
| PAY-07 | Phase 4: Payments | Complete |
| PAY-08 | Phase 4: Payments | Complete |
| PAY-09 | Phase 4: Payments | Complete |
| WEB-01 | Phase 5: React Frontend | Complete |
| WEB-02 | Phase 5: React Frontend | Complete |
| WEB-03 | Phase 5: React Frontend | Complete |
| WEB-04 | Phase 5: React Frontend | Complete |
| WEB-05 | Phase 5: React Frontend | Complete |
| WEB-06 | Phase 5: React Frontend | Complete |
| WEB-07 | Phase 5: React Frontend | Complete |
| WEB-08 | Phase 5: React Frontend | Complete |
| PDF-01 | Phase 6: PDF Generation & Delivery | Complete |
| PDF-02 | Phase 6: PDF Generation & Delivery | Complete |
| PDF-03 | Phase 6: PDF Generation & Delivery | Complete |
| PDF-04 | Phase 6: PDF Generation & Delivery | Complete |
| PDF-05 | Phase 6: PDF Generation & Delivery | Complete |
| PDF-06 | Phase 6: PDF Generation & Delivery | Complete |
| PDF-07 | Phase 6: PDF Generation & Delivery | Complete |
| DLV-01 | Phase 6: PDF Generation & Delivery | Complete |
| DLV-02 | Phase 6: PDF Generation & Delivery | Complete |
| DLV-03 | Phase 6: PDF Generation & Delivery | Complete |
| DLV-04 | Phase 6: PDF Generation & Delivery | Complete |
| DLV-05 | Phase 6: PDF Generation & Delivery | Complete |
| DLV-06 | Phase 6: PDF Generation & Delivery | Complete |
| CRM-01 | Phase 7: Admin CRM | Complete |
| CRM-02 | Phase 7: Admin CRM | Complete |
| CRM-03 | Phase 7: Admin CRM | Pending |
| CRM-04 | Phase 7: Admin CRM | Pending |
| CRM-05 | Phase 7: Admin CRM | Pending |
| CRM-06 | Phase 7: Admin CRM | Pending |
| CRM-07 | Phase 7: Admin CRM | Pending |
| CRM-08 | Phase 7: Admin CRM | Pending |
| CRM-09 | Phase 7: Admin CRM | Pending |
| CRM-10 | Phase 7: Admin CRM | Complete |
| HARD-01 | Phase 8: Hardening & Production Readiness | Pending |
| HARD-02 | Phase 8: Hardening & Production Readiness | Pending |
| HARD-03 | Phase 8: Hardening & Production Readiness | Pending |
| HARD-04 | Phase 8: Hardening & Production Readiness | Pending |
| HARD-05 | Phase 8: Hardening & Production Readiness | Pending |
| HARD-06 | Phase 8: Hardening & Production Readiness | Pending |
| HARD-07 | Phase 8: Hardening & Production Readiness | Pending |
| HARD-08 | Phase 8: Hardening & Production Readiness | Pending |
| HARD-09 | Phase 8: Hardening & Production Readiness | Pending |

**Coverage:**
- v1 requirements: 80 total
- Mapped to phases: 80
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-15*
*Last updated: 2026-04-15 — traceability updated with phase names after roadmap creation*
