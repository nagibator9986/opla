# Phase 5: React Frontend - Context

**Gathered:** 2026-04-17
**Status:** Ready for planning
**Mode:** auto (recommended defaults)

<domain>
## Phase Boundary

Создать React-приложение (лендинг + личный кабинет клиента): single-page лендинг с секциями hero/метод/тарифы/кейсы/FAQ, интеграция CloudPayments Widget для оплаты, deep-link авторизация (UUID → JWT), личный кабинет со статусом заказа и кнопкой Upsell.

**Не делаем в этой фазе:** CRM-админку (Phase 7), PDF-генерацию (Phase 6), доставку отчётов (Phase 6), Sentry/CI/TLS (Phase 8). Frontend-часть PAY-01 (CloudPayments Widget на странице) реализуется здесь.

Требования: WEB-01..WEB-08 (8 штук) + PAY-01 (CP Widget на React).

</domain>

<decisions>
## Implementation Decisions

### Структура приложения
- React 18 + Vite + TypeScript + Tailwind CSS
- TanStack Query (React Query) для серверного состояния (fetch, cache, mutations)
- Zustand для клиентского состояния (auth, UI state)
- React Router v6 для маршрутизации
- Директория `frontend/` в корне репозитория (рядом с `backend/` и `bot/`)

### Маршрутизация (4 маршрута)
- `/` — лендинг (single-page scroll: hero, метод, тарифы, кейсы, FAQ)
- `/tariffs` — страница тарифов с CloudPayments Widget (дублирует секцию тарифов лендинга, но как отдельная страница для deep-link из бота)
- `/auth/:uuid` — deep-link landing: обмен UUID на JWT, редирект в кабинет
- `/cabinet` — личный кабинет клиента (protected route, требует JWT)

### Лендинг (single-page scroll)
- Одностраничный скролл с якорными секциями
- Порядок секций: Hero → Метод → Тарифы → Кейсы → FAQ → CTA-футер
- Тексты всех секций загружаются из `ContentBlock` через API (один batch-запрос)
- Визуальный стиль: солидный/премиальный, тёмные акценты — заказчик требует «солидный» вид
- Mobile-first вёрстка (Tailwind responsive: sm/md/lg breakpoints)
- Навигация: fixed header с якорными ссылками на секции + кнопка «Выбрать тариф»

### Секция тарифов
- Две карточки: Ashıde 1 (45 000 ₸) и Ashıde 2 (135 000 ₸)
- Данные тарифов из API `GET /api/v1/payments/tariffs/` (цены в БД, не захардкожены)
- Кнопка «Оплатить» на каждой карточке открывает CloudPayments Widget в модальном окне
- Карточки показывают: название, цену, описание, количество параметров отчёта

### CloudPayments Widget интеграция (PAY-01)
- Подключение через `<script src="https://widget.cloudpayments.ru/bundles/cloudpayments.js">`
- `window.cp` — глобальный объект CloudPayments
- При клике «Оплатить»: `new cp.CloudPayments().pay('charge', {...options})`
- Options:
  - `publicId` из env (VITE_CLOUDPAYMENTS_PUBLIC_ID)
  - `amount` из тарифа
  - `currency: "KZT"`
  - `invoiceId` = submission_id (UUID)
  - `description` = "Бизнес-аудит {tariff.title}"
  - `accountId` = client_profile_id
  - `data.telegram_id` для корреляции
- Callback `onSuccess` → показать «Оплата прошла! Вернитесь в Telegram для прохождения анкеты»
- Callback `onFail` → показать ошибку, предложить повторить

### Deep-link авторизация (WEB-06)
- Маршрут `/auth/:uuid` — клиент переходит по ссылке из Telegram-бота
- React при загрузке страницы вызывает `POST /api/v1/bot/deeplink/exchange/` с UUID
- При успехе: сохраняет JWT (access + refresh) в localStorage, обновляет Zustand store, редиректит в `/cabinet`
- При ошибке (UUID невалидный/истёк): показывает сообщение «Ссылка истекла. Запросите новую в боте.»
- JWT refresh: автоматический через TanStack Query interceptor (axios или fetch wrapper)

### Личный кабинет (WEB-04, WEB-05)
- Protected route: если нет JWT → редирект на лендинг с сообщением
- Показывает текущий статус заказа в виде step progress bar:
  - Оплачено → Анкета → На аудите → Готово
  - Текущий шаг подсвечен
- Информация: название компании, тариф, дата создания
- Когда `status=delivered` → кнопка «Скачать PDF» (ссылка из `AuditReport.pdf_url`)
- Когда `status < delivered` → PDF-кнопка неактивна/скрыта

### Upsell (WEB-05)
- Кнопка «Расширить до Ashıde 2» видна только клиентам с тарифом Ashıde 1
- При клике: `POST /api/v1/payments/upsell/` → получить данные для CP Widget → открыть Widget на 90 000 ₸
- После успешной оплаты: обновить статус в кабинете, показать «Тариф обновлён!»

### Авторизация и состояние
- JWT хранится в localStorage (access_token, refresh_token)
- Zustand store: `{ isAuthenticated, clientProfile, setAuth, clearAuth }`
- TanStack Query: `useQuery` для GET-запросов, `useMutation` для POST
- Axios instance с interceptor для:
  - Автоматической подстановки `Authorization: Bearer` из localStorage
  - Авто-рефреша при 401 (используя refresh_token)
  - Редиректа на лендинг при невалидном refresh

### Content из ContentBlock (WEB-02)
- API-эндпоинт для загрузки контент-блоков (нужно создать в этой фазе или использовать существующий)
- TanStack Query с `staleTime: 5 * 60 * 1000` (5 минут) — контент меняется редко
- Ключи ContentBlock для лендинга:
  - `hero_title`, `hero_subtitle`, `hero_cta`
  - `method_title`, `method_text`
  - `tariff_section_title`
  - `cases_title`, `case_1_title`, `case_1_text`, `case_2_title`, `case_2_text`, ...
  - `faq_1_q`, `faq_1_a`, `faq_2_q`, `faq_2_a`, ...
- Fallback: захардкоженные тексты, если API недоступен (graceful degradation)

### Docker и dev-сервер
- `frontend/` с Vite dev server на порту 5173
- В docker-compose: сервис `frontend` с `npm run dev` (hot reload)
- В prod: `npm run build` → статика → nginx раздаёт
- Vite proxy: `/api` → `http://web:8000` (для dev без CORS)
- Env переменные через `VITE_` prefix: `VITE_API_URL`, `VITE_CLOUDPAYMENTS_PUBLIC_ID`

### Claude's Discretion
- Точный дизайн компонентов (размеры, отступы, цвета в пределах «солидного» стиля)
- Выбор конкретных Tailwind-плагинов
- Структура компонентов (атомарность, вложенность)
- Анимации и переходы между страницами
- Точные тексты fallback-контента
- Error boundary стратегия
- SEO meta-теги

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project-level
- `CLAUDE.md` — архитектура, стек (React 18 + Vite + TS + Tailwind + TanStack Query), принципы
- `.planning/PROJECT.md` — Core Value, тарифы (45000/135000/90000 ₸), «солидный» стиль, автономная админка
- `.planning/REQUIREMENTS.md` — WEB-01..WEB-08, PAY-01
- `.planning/ROADMAP.md` — Phase 5 success criteria

### Prior phase decisions
- `.planning/phases/01-infrastructure-data-model/01-CONTEXT.md` — ContentBlock model, Redis layout, Docker Compose structure, frontend/ placeholder
- `.planning/phases/02-core-rest-api/02-CONTEXT.md` — API URL structure `/api/v1/`, JWT auth (SimpleJWT), deep-link exchange flow, submission lifecycle
- `.planning/phases/03-telegram-bot/03-CONTEXT.md` — deep-link URL pattern `https://baqsy.kz/auth/{uuid}`, bot deep-link triggers
- `.planning/phases/04-payments/04-CONTEXT.md` — CloudPayments Widget config (publicId, InvoiceId=submission_id, Currency=KZT), upsell endpoint, tariff list endpoint

### Existing backend code (MUST read)
- `backend/apps/core/api_urls.py` — API v1 URL router (bot/, industries/, submissions/, payments/)
- `backend/apps/payments/views.py` — TariffListView (public), CloudPayments webhook views, UpsellView
- `backend/apps/payments/serializers.py` — TariffSerializer
- `backend/apps/submissions/views.py` — SubmissionCreate, NextQuestion, AnswerCreate, Complete views
- `backend/apps/accounts/views.py` — OnboardingView, DeeplinkCreateView, DeeplinkExchangeView
- `backend/apps/content/models.py` — ContentBlock model (key, title, content, content_type, is_active)
- `backend/baqsy/urls.py` — root URL config (admin, health, api/v1/)
- `docker/docker-compose.yml` — existing services (web, bot, worker, beat, db, redis, minio, nginx)

### Research
- `.planning/research/STACK.md` — React 18, Vite, TanStack Query versions
- `.planning/research/ARCHITECTURE.md` — frontend ↔ Django REST communication

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **ContentBlock model** — key/content/content_type/is_active — готова для лендинга, нужен только API endpoint для чтения
- **TariffListView** — `GET /api/v1/payments/tariffs/` — публичный, возвращает активные тарифы
- **DeeplinkExchangeView** — `POST /api/v1/bot/deeplink/exchange/` — обменивает UUID на JWT
- **UpsellView** — `POST /api/v1/payments/upsell/` — JWT-protected, возвращает данные для CP Widget
- **Docker Compose** — уже настроен, нужно добавить frontend-сервис
- **nginx.conf** — уже настроен для web, нужно добавить проксирование фронта

### Established Patterns
- **JWT auth** через SimpleJWT — access 4h, refresh 7d, rotate_refresh_tokens=True
- **API errors** в формате `{"error": "код", "detail": "текст на русском"}`
- **UUID primary keys** для Submission — URL patterns `<uuid:pk>`
- **ContentBlock keys** — slug-формат (hero_title, method_text и т.д.)

### Integration Points
- `frontend/` — новая директория, Vite проект с нуля
- `docker/docker-compose.yml` — добавить сервис `frontend`
- `docker/nginx.conf` — добавить location для фронта и проксирование /api
- `backend/apps/content/` — добавить views.py, serializers.py, urls.py для ContentBlock API
- `backend/apps/core/api_urls.py` — добавить `path("content/", include("apps.content.urls"))`
- `.env.example` — добавить VITE_CLOUDPAYMENTS_PUBLIC_ID, VITE_API_URL

</code_context>

<specifics>
## Specific Ideas

- CloudPayments Widget подключается через external script, не npm-пакет — `window.cp` глобально
- `InvoiceId` = submission UUID — это ключ связки между фронтом и webhook'ом
- Лендинг должен выглядеть «солидно» — это прямое требование заказчика (книга «Вечный Иль»)
- Тексты из ContentBlock — админ может менять без деплоя, это ключевое требование
- Deep-link из бота: клиент НЕ регистрируется на сайте, он приходит уже идентифицированным через UUID

</specifics>

<deferred>
## Deferred Ideas

- SEO-оптимизация (SSR/SSG) — v2, на MVP CSR достаточно
- Мультиязычность (KZ/EN) — v2 (LANG-01)
- WCAG 2.1 AA accessibility — v2 (A11Y-01)
- Анимации при скролле (parallax, fade-in) — nice to have, не в MVP
- Dark mode — не в скоупе
- Cookie consent banner — зависит от юрисдикции, отложено

</deferred>

---

*Phase: 05-react-frontend*
*Context gathered: 2026-04-17*
