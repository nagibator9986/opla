# Baqsy System — Project Guide for Claude

## 1. Что это

Платформа бизнес-аудита «Baqsy System». Клиент приходит через Telegram-бот, проходит базовую категоризацию, попадает на сайт с тарифами, оплачивает через CloudPayments KZ, заполняет отраслевую анкету (27 вопросов, разную для разных отраслей), администратор вручную пишет аудит, система генерирует именной PDF и отправляет клиенту в Telegram и WhatsApp.

Продукт из двух частей:
- **Платформа** (Django + DRF + React) — лендинг, оплата, анкета, CRM-админка, генерация PDF.
- **Telegram-бот** (aiogram 3.x) — точка входа, FSM-прохождение анкеты, доставка результата.

## 2. Архитектура

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Landing (React)│──│  Django API   │──│  PostgreSQL   │
└──────────────┘    │   + Admin CRM │    └──────────────┘
                    └───────┬───────┘
                            │
┌──────────────┐    ┌───────┴───────┐    ┌──────────────┐
│  TG Bot       │──│   REST API    │──│ Celery+Redis  │
│  (aiogram 3)  │    └───────┬───────┘    └──────┬───────┘
└──────────────┘            │                   │
                    ┌───────┴───────┐    ┌──────┴───────┐
                    │ CloudPayments │    │ WA Provider  │
                    │   Webhook     │    │ (Wazzup/GA)  │
                    └───────────────┘    └──────────────┘
```

**Процессы (docker-compose):**
- `web` — Django + gunicorn (API + админка)
- `frontend` — React (Vite) → статика через nginx
- `bot` — aiogram 3 воркер (long-polling в dev, webhook в prod)
- `worker` — Celery (PDF, WA-отправка, вебхуки оплаты)
- `beat` — Celery beat (напоминания, upsell)
- `db` — PostgreSQL 16
- `redis` — брокер Celery + FSM-хранилище aiogram
- `nginx` — реверс-прокси

## 3. Стек

| Слой | Технология | Зачем |
|---|---|---|
| Backend | Python 3.12, Django 5, DRF | стабильно, популярно, сильная админка |
| Bot | aiogram 3.x + Redis FSM | современный async API |
| DB | PostgreSQL 16 | JSONB для гибких ответов |
| Queue | Celery + Redis | PDF, webhooks, ретраи |
| Frontend | React 18 + Vite + TypeScript + TanStack Query + Tailwind | быстро, типизированно |
| PDF | WeasyPrint + Jinja2 | HTML→PDF в фирменном стиле |
| Storage | MinIO (S3-совместимое) | PDF, загрузки |
| Payments | CloudPayments KZ (Widget + webhook HMAC) | требование заказчика |
| WhatsApp | Wazzup24 / Green API (провайдер согласовать) | доставка итога |
| Auth | JWT (SimpleJWT) для API, Django session для админки | стандарт |
| CI | GitHub Actions + Docker | автоматизация |

## 4. Структура репозитория

```
baqsy-system/
├── backend/                 # Django-проект
│   ├── baqsy/               # settings, urls, celery
│   ├── apps/
│   │   ├── accounts/        # ClientProfile, auth
│   │   ├── industries/      # Industry, QuestionnaireTemplate, Question
│   │   ├── submissions/     # Submission, Answer
│   │   ├── payments/        # Tariff, Payment, CloudPayments webhook
│   │   ├── reports/         # AuditReport, PDF generation
│   │   ├── delivery/        # Telegram + WhatsApp delivery log
│   │   └── dashboard/       # admin stats
│   ├── templates/pdf/       # Jinja2 PDF templates
│   └── manage.py
├── bot/                     # aiogram 3 bot
│   ├── handlers/            # start, onboarding, questionnaire, delivery
│   ├── states/              # FSM states
│   ├── services/            # API client to Django
│   └── main.py
├── frontend/                # React + Vite + TS
│   ├── src/
│   │   ├── pages/           # Landing, Tariffs, Payment, Cabinet
│   │   ├── components/
│   │   └── api/
├── docker/
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   └── nginx.conf
├── .env.example
├── .github/workflows/ci.yml
└── README.md
```

## 5. Ключевые домены

### Industry + QuestionnaireTemplate
- `Industry` — Ритейл, IT, Производство, Услуги, F&B…
- `QuestionnaireTemplate` — привязан к индустрии, версионируется (`version` int, `is_active` bool). Старые Submission всегда держат ссылку на свою версию.
- `Question` — `template_id`, `order`, `text`, `field_type` (text/number/choice/multichoice), `options` JSONB, `required` bool, `block` (A/B/C).

**Инвариант:** при редактировании анкеты админом создаётся новая версия, активная — одна.

### Submission flow
```
created → paid → in_progress → completed → under_audit → delivered
```
- `created` — клиент вышел на тариф
- `paid` — CloudPayments webhook OK
- `in_progress` — бот задаёт вопросы, сохраняет Answer после каждого
- `completed` — все обязательные вопросы заполнены
- `under_audit` — админ видит в CRM
- `delivered` — PDF сгенерирован и отправлен

### Tariff
- `ashide_1` — $99 / ~45 000 ₸ — 7–9 параметров отчёта
- `ashide_2` — $299 / ~135 000 ₸ — 18–24 параметра
- `upsell` — $200 — апгрейд с 1 на 2 без повторной анкеты

Цены хранятся в БД (админ меняет без кода). В ₸ и $ одновременно, активная валюта = KZT.

### AuditReport
Админ вводит текст анализа в CRM → Celery-таск рендерит HTML-шаблон с данными клиента и компании → WeasyPrint → PDF → MinIO → отправка по каналам.

## 6. Интеграции

### CloudPayments KZ
- Widget на фронте, `publicId` из env
- Webhook endpoint: `POST /api/payments/cloudpayments/webhook/`
- Проверка HMAC (`Content-HMAC` header) обязательна
- Идемпотентность по `TransactionId`
- При успехе: `Payment.status=succeeded`, `Submission.status=paid`, триггер бота

### Telegram (aiogram 3)
- Long-polling в dev, webhook в prod
- Redis-стораджем для FSM
- Клиент идентифицируется по `telegram_id`, привязка к `ClientProfile`
- Команды: `/start`, `/status`, `/help`
- FSM-сценарии: onboarding (5 вопросов) → deep-link на оплату → questionnaire (N вопросов)

### WhatsApp (провайдер TBD)
- Абстракция `delivery.providers.WhatsAppProvider` с реализациями Wazzup/GreenAPI
- Отправка PDF как файл + сопроводительное сообщение

## 7. Принципы разработки

1. **Django-first для бизнес-логики.** Бот — тонкий клиент, дёргает REST API. Никакой бизнес-логики в `bot/`.
2. **Версионирование анкет.** Никогда не удалять Question из шаблона — только soft-delete в новой версии.
3. **JSONB для Answer.value.** Гибкие типы (text/number/array) в одном поле.
4. **Идемпотентность webhooks.** Всегда проверять дубли по внешнему ID.
5. **Celery для всего медленного.** PDF, WA-отправка, уведомления админу — только через очередь.
6. **Миграции Django — единственный способ менять схему.** Никаких ручных SQL.
7. **Секреты — только через env.** `.env.example` с пустыми ключами в репо.
8. **Логи структурированные.** `structlog` + JSON в prod.

## 8. Команды (после установки)

```bash
# Локалка
docker-compose up -d                    # поднять все сервисы
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py seed_industries

# Тесты
docker-compose exec web pytest
docker-compose exec web pytest apps/submissions/

# Бот отдельно (dev)
cd bot && python main.py

# Фронт
cd frontend && npm run dev
```

## 9. Что НЕ делаем (скоуп)

- Не пилим свой платёжный шлюз — только CloudPayments
- Не делаем AI-генерацию аудита — админ пишет руками
- Не делаем mobile app — только web + TG
- Не делаем мультитенантность — один экземпляр на клиента
- Не делаем email-канал на первой итерации (только TG + WA)

## 10. Открытые вопросы (блокеры для точной оценки)

- [ ] WhatsApp-провайдер: Wazzup24 vs GreenAPI vs 360dialog
- [ ] Финальный список отраслей и тексты всех анкет
- [ ] Макеты лендинга и PDF («Вечный Иль»)
- [ ] Оплата ДО или ПОСЛЕ анкеты (ТЗ и устное описание расходятся)
- [ ] Валюта на чеке — KZT фиксированно или по курсу с $
- [ ] Мультиязычность (RU/KZ/EN?)
- [ ] SLA админа на проведение аудита

## 11. GSD Workflow

Проект ведём через GSD-плагин. Roadmap — `.planning/ROADMAP.md`. Каждая фаза — отдельная папка `.planning/phases/NN-name/` с `PLAN.md`, `RESEARCH.md`, `VERIFICATION.md`.

**Правила:**
- Перед каждой фазой — `/gsd:discuss-phase` → `/gsd:plan-phase` → `/gsd:execute-phase`
- Атомарные коммиты per task
- UI-фазы проходят через `/gsd:ui-phase` (UI-SPEC)
- Верификация через `/gsd:verify-work` (UAT conversational)

## 12. Тон работы с пользователем

- Язык общения: русский
- Пользователь — владелец продукта, не разработчик в команде. Объясняем решения простым языком, но без упрощений в коде.
- Перед рискованными действиями (миграции, деплой, изменение цен) — подтверждение.
- Коммиты на русском в императиве: «добавить модель Industry», «починить webhook CloudPayments».
