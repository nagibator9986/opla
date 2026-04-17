# Roadmap: Baqsy System

## Overview

Восемь фаз с жёсткими зависимостями по порядку сборки. Фундамент (модели + инфраструктура) → API-слой → бот → оплата → веб → генерация и доставка PDF → CRM-админка → производственное укрепление. Каждая следующая фаза опирается на предыдущую; ни одна фаза не может начаться без завершения предшествующей.

## Phases

- [ ] **Phase 1: Infrastructure & Data Model** — Docker Compose + все Django-модели + миграции + инвариант версионирования шаблонов
- [x] **Phase 2: Core REST API** — все эндпоинты для бота и React; JWT; deep-link токены (completed 2026-04-16)
- [x] **Phase 3: Telegram Bot** — aiogram 3 FSM онбординг + прохождение анкеты; тонкий REST-клиент (completed 2026-04-16)
- [x] **Phase 4: Payments** — CloudPayments Widget + HMAC webhook + идемпотентность + sandbox-тест (completed 2026-04-17)
- [ ] **Phase 5: React Frontend** — лендинг, тарифы с CP виджетом, кабинет клиента, upsell
- [ ] **Phase 6: PDF Generation & Delivery** — WeasyPrint + Jinja2 + MinIO + Telegram sendDocument + Wazzup24
- [ ] **Phase 7: Admin CRM** — дашборд, карточка заказа с редактором аудита, редакторы контента/шаблонов/тарифов
- [ ] **Phase 8: Hardening & Production Readiness** — structlog, Sentry, CI, TLS, rate limiting, webhook mode, документация

## Phase Details

### Phase 1: Infrastructure & Data Model
**Goal**: Полная основа проекта запущена локально — все модели данных существуют, мигрированы и соблюдают инварианты версионирования
**Depends on**: Nothing (first phase)
**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04, INFRA-05, INFRA-06, INFRA-07, DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06, DATA-07, DATA-08, DATA-09, DATA-10, DATA-11, DATA-12, DATA-13
**Success Criteria** (what must be TRUE):
  1. `docker-compose up` поднимает все сервисы (web, bot, worker, beat, db, redis, nginx, minio) без ошибок и `docker-compose ps` показывает все контейнеры healthy
  2. `python manage.py migrate` проходит чисто; все 13 моделей (Industry, QuestionnaireTemplate, Question, ClientProfile, Submission, Answer, Tariff, Payment, AuditReport, DeliveryLog, ContentBlock и служебные) присутствуют в схеме БД
  3. Попытка изменить `Submission.template_id` после создания вызывает ошибку валидации (инвариант DATA-13 соблюдается)
  4. Редактирование `QuestionnaireTemplate` создаёт новую версию; активной остаётся ровно одна (инвариант DATA-12 соблюдается)
  5. Файл `.env.example` содержит все ключи; `README.md` описывает развёртывание — новый разработчик может поднять стек за ≤2 часа по инструкции
**Plans**: TBD

### Phase 2: Core REST API
**Goal**: Все бизнес-операции системы доступны через REST API с правильной аутентификацией — бот и React могут полностью работать с бэкендом
**Depends on**: Phase 1
**Requirements**: API-01, API-02, API-03, API-04, API-05, API-06, API-07, API-08, API-09, API-10, API-11
**Success Criteria** (what must be TRUE):
  1. `POST /api/bot/onboarding/` с `telegram_id` создаёт или обновляет `ClientProfile` и возвращает 200/201
  2. `POST /api/bot/deeplink/` возвращает одноразовый UUID-токен; `POST /api/bot/deeplink/exchange/` обменивает его на JWT и делает токен недействительным
  3. Полный цикл анкеты через API работает: создать Submission → получить следующий вопрос → сохранить ответ → завершить — каждый шаг возвращает ожидаемый HTTP-статус
  4. JWT-токен в заголовке `Authorization` даёт клиенту доступ к своим данным; запрос без токена возвращает 401
  5. Сессионная аутентификация Django работает для эндпоинтов `/admin/`; анонимный запрос к защищённой админке возвращает 302 на логин
**Plans**: TBD

### Phase 3: Telegram Bot
**Goal**: Клиент может пройти весь путь через Telegram-бот от первого `/start` до уведомления «ожидайте результат» — без потери прогресса при обрывах
**Depends on**: Phase 2
**Requirements**: BOT-01, BOT-02, BOT-03, BOT-04, BOT-05, BOT-06, BOT-07, BOT-08, BOT-09, BOT-10, BOT-11
**Success Criteria** (what must be TRUE):
  1. Новый пользователь пишет `/start` → проходит 5 вопросов онбординга → получает deep-link на сайт с тарифами
  2. После сигнала об оплате бот начинает задавать вопросы анкеты по одному с прогресс-индикатором «Вопрос N/27»; каждый ответ сразу виден в Django API
  3. При перезапуске бота (kill + start контейнера) в середине анкеты клиент набирает `/start` и продолжает с того же вопроса, на котором остановился
  4. `/status` возвращает текущий статус заказа клиента; `/help` возвращает справочное сообщение
  5. Клиент, не завершивший анкету за 24 часа, получает напоминание от бота (Celery beat)
**Plans**: TBD

### Phase 4: Payments
**Goal**: Клиент может оплатить тариф через CloudPayments; система надёжно обрабатывает webhook с идемпотентностью и переводит Submission в статус paid
**Depends on**: Phase 3
**Requirements**: PAY-01, PAY-02, PAY-03, PAY-04, PAY-05, PAY-06, PAY-07, PAY-08, PAY-09
**Success Criteria** (what must be TRUE):
  1. CloudPayments Widget открывается на странице тарифа; тестовый платёж в sandbox проходит и `Payment.status` становится `succeeded`
  2. Повторная отправка webhook с тем же `TransactionId` не создаёт второй объект `Payment` (идемпотентность)
  3. После успешной оплаты `Submission.status` меняется на `paid` и Celery-таск уведомляет бота о начале анкеты
  4. Webhook с неверной HMAC-подписью возвращает 403 и не изменяет данные
  5. Нажатие кнопки Upsell в кабинете клиента с тарифом Ashıde 1 инициирует доплату 90 000 ₸ и апгрейдит тариф без повторной анкеты
**Plans**: TBD

### Phase 5: React Frontend
**Goal**: Клиент видит полноценный лендинг, может выбрать и оплатить тариф, войти по deep-link и отслеживать статус заказа в личном кабинете
**Depends on**: Phase 4
**Requirements**: WEB-01, WEB-02, WEB-03, WEB-04, WEB-05, WEB-06, WEB-07, WEB-08
**Success Criteria** (what must be TRUE):
  1. Лендинг отображает секции hero, метод, тарифы, кейсы, FAQ — тексты загружаются из `ContentBlock` (изменение в БД мгновенно отражается без деплоя)
  2. Клиент переходит по deep-link из бота → React обменивает UUID на JWT → клиент залогинен и видит свой личный кабинет
  3. Личный кабинет показывает текущий статус заказа; после доставки PDF доступна ссылка для скачивания
  4. Кнопка Upsell видна клиентам с тарифом Ashıde 1 и инициирует виджет CloudPayments на 90 000 ₸
  5. Лендинг и кабинет корректно отображаются на мобильных устройствах (mobile-first)
**Plans**: TBD

### Phase 6: PDF Generation & Delivery
**Goal**: После подтверждения аудита администратором система автоматически генерирует именной PDF и доставляет его клиенту в Telegram и WhatsApp
**Depends on**: Phase 5
**Requirements**: PDF-01, PDF-02, PDF-03, PDF-04, PDF-05, PDF-06, PDF-07, DLV-01, DLV-02, DLV-03, DLV-04, DLV-05, DLV-06
**Success Criteria** (what must be TRUE):
  1. Нажатие «Подтвердить и отправить» в CRM запускает Celery-таск; через несколько секунд в MinIO появляется PDF с именем клиента и названием компании на обложке
  2. Клиент получает PDF-файл в Telegram-боте; `DeliveryLog` фиксирует статус `delivered` для канала `telegram`
  3. Клиент получает PDF в WhatsApp через Wazzup24 с сопроводительным текстом; `DeliveryLog` фиксирует `delivered` для канала `whatsapp`
  4. Повторный запуск таска генерации для уже сгенерированного отчёта не создаёт новый PDF (идемпотентность через `AuditReport.pdf_url`)
  5. Временные ошибки доставки (5xx) автоматически повторяются через Celery retry; после успеха `DeliveryLog.status` = `delivered`
**Plans**: TBD

### Phase 7: Admin CRM
**Goal**: Администратор может управлять всем жизненным циклом заказа, контентом и конфигурацией системы через веб-интерфейс без правки кода
**Depends on**: Phase 6
**Requirements**: CRM-01, CRM-02, CRM-03, CRM-04, CRM-05, CRM-06, CRM-07, CRM-08, CRM-09, CRM-10
**Success Criteria** (what must be TRUE):
  1. Dashboard отображает счётчики (всего заказов, в работе, завершённых, выручка) и фильтруется по отрасли, региону, тарифу и дате без перезагрузки страницы
  2. Карточка заказа показывает все ответы клиента слева и содержит поле для ввода аудита справа; кнопка «Подтвердить и отправить» запускает генерацию и доставку PDF
  3. Администратор меняет цену тарифа в редакторе тарифов → новая цена немедленно отображается на лендинге без деплоя
  4. Редактирование шаблона анкеты создаёт новую версию; исторические заказы по-прежнему ссылаются на старую версию и отображают корректные вопросы
  5. Вход по email+пароль работает; 10 неверных попыток подряд блокируют IP (django-axes)
**Plans**: TBD

### Phase 8: Hardening & Production Readiness
**Goal**: Система готова к production-развёртыванию: мониторинг ошибок, CI, TLS, защита от злоупотреблений, webhook-режим бота и полная документация
**Depends on**: Phase 7
**Requirements**: HARD-01, HARD-02, HARD-03, HARD-04, HARD-05, HARD-06, HARD-07, HARD-08, HARD-09
**Success Criteria** (what must be TRUE):
  1. Все ошибки бэкенда, бота и фронтенда появляются в Sentry; структурированные JSON-логи пишутся в stdout в production-режиме
  2. GitHub Actions CI проходит на каждый push: pytest + ruff + mypy для бэкенда, npm test + npm build для фронтенда
  3. Бот работает через webhook (не long-polling) в production; nginx проксирует HTTPS с валидным TLS-сертификатом Let's Encrypt
  4. `seed_industries` загружает минимум 3 отрасли с демо-шаблонами; новый разработчик может развернуть систему с нуля за ≤2 часа по `DEPLOYMENT.md`
  5. Публичные эндпоинты (webhook оплаты, onboarding) возвращают 429 при превышении лимита запросов; health-check эндпоинты отвечают 200 для всех сервисов
**Plans**: TBD

## Progress

**Execution Order:** 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Infrastructure & Data Model | 4/4 | Complete | 2026-04-16 |
| 2. Core REST API | 4/4 | Complete   | 2026-04-16 |
| 3. Telegram Bot | 3/3 | Complete   | 2026-04-16 |
| 4. Payments | 2/2 | Complete   | 2026-04-17 |
| 5. React Frontend | 0/? | Not started | - |
| 6. PDF Generation & Delivery | 0/? | Not started | - |
| 7. Admin CRM | 0/? | Not started | - |
| 8. Hardening & Production Readiness | 0/? | Not started | - |
