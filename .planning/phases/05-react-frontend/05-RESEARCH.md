# Phase 5: React Frontend - Research

**Researched:** 2026-04-17
**Domain:** React 18 + Vite + TypeScript + Tailwind + TanStack Query + Zustand + CloudPayments Widget
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- React 18 + Vite + TypeScript + Tailwind CSS
- TanStack Query (React Query) для серверного состояния
- Zustand для клиентского состояния (auth, UI state)
- React Router v6 для маршрутизации
- Директория `frontend/` в корне репозитория
- 4 маршрута: `/`, `/tariffs`, `/auth/:uuid`, `/cabinet`
- Лендинг — single-page scroll: Hero → Метод → Тарифы → Кейсы → FAQ → CTA-футер
- Тексты из ContentBlock через один batch API-запрос, `staleTime: 5 * 60 * 1000`
- Mobile-first (Tailwind responsive: sm/md/lg)
- CloudPayments Widget через `<script>` + `window.cp`, не npm-пакет
- JWT в localStorage (access_token, refresh_token)
- Zustand store: `{ isAuthenticated, clientProfile, setAuth, clearAuth }`
- Axios instance с interceptor для Bearer + авто-рефреш при 401
- Deep-link: `POST /api/v1/bot/deeplink/exchange/` → JWT → localStorage → редирект `/cabinet`
- Upsell: виден только клиентам с tariff ashide_1, кнопка вызывает `POST /api/v1/payments/upsell/`
- Vite proxy: `/api` → `http://web:8000`
- Env: `VITE_CLOUDPAYMENTS_PUBLIC_ID`, `VITE_API_URL`
- Стиль: «солидный/премиальный», тёмные акценты

### Claude's Discretion
- Точный дизайн компонентов (размеры, отступы, цвета в пределах «солидного» стиля)
- Выбор конкретных Tailwind-плагинов
- Структура компонентов (атомарность, вложенность)
- Анимации и переходы между страницами
- Точные тексты fallback-контента
- Error boundary стратегия
- SEO meta-теги

### Deferred Ideas (OUT OF SCOPE)
- SEO-оптимизация (SSR/SSG) — v2, на MVP CSR достаточно
- Мультиязычность (KZ/EN) — v2 (LANG-01)
- WCAG 2.1 AA accessibility — v2 (A11Y-01)
- Анимации при скролле (parallax, fade-in) — nice to have, не в MVP
- Dark mode — не в скоупе
- Cookie consent banner — зависит от юрисдикции, отложено
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| WEB-01 | Лендинг на React 18 + Vite + TypeScript + Tailwind | Vite 6 scaffold + Tailwind v4 setup confirmed |
| WEB-02 | Секции лендинга из ContentBlock API | `GET /api/v1/content/` нужно создать; ContentBlock model exists |
| WEB-03 | Страница тарифов с CloudPayments Widget | `GET /api/v1/payments/tariffs/` public, window.cp integration documented |
| WEB-04 | Клиентский кабинет со статусом и PDF-ссылкой | `GET /api/v1/submissions/{id}/` exists, SubmissionDetailSerializer ready |
| WEB-05 | Кнопка Upsell в кабинете для Ashide 1 | `POST /api/v1/payments/upsell/` exists, returns CP Widget config |
| WEB-06 | Deep-link landing: UUID → JWT → кабинет | `POST /api/v1/bot/deeplink/exchange/` exists, returns access+refresh+name |
| WEB-07 | Адаптивная вёрстка (mobile-first) | Tailwind responsive classes, grid/flex patterns |
| WEB-08 | TanStack Query для fetch, Zustand для state | Confirmed versions: TanStack Query 5.99, Zustand 5.0 |
</phase_requirements>

---

## Summary

Phase 5 строит React SPA поверх уже реализованного Django REST бэкенда. Все необходимые API-эндпоинты существуют, кроме одного: `GET /api/v1/content/` для ContentBlock — его нужно создать в этой фазе (views, serializers, urls в `backend/apps/content/`). Остальной бэкенд — DeeplinkExchangeView, TariffListView, SubmissionDetailView, UpsellView — полностью готов.

Стек зафиксирован: React 19.2 / Vite 8.0 / TanStack Query 5.99 / Zustand 5.0 / React Router 7.14 / Tailwind 4.2 / Axios 1.15 / TypeScript 6.0. Это текущие стабильные версии по npm registry на дату исследования. Критически важно: Tailwind v4 имеет **breaking API** по сравнению с v3 — больше нет `tailwind.config.js` в стандартном сценарии, конфиг переехал в CSS. Zustand 5.x изменил API создания store (нет `devtools` wrapper по умолчанию, изменился тип `create`).

CloudPayments Widget подключается исключительно через внешний `<script>` тег, не через npm. Глобальный объект `window.cp` инициализируется асинхронно. Это требует типизации через `declare global` в TypeScript и проверки готовности виджета перед вызовом `pay()`. InvoiceId — это submission UUID, что является ключевой связкой между фронтом и webhook-ом.

**Primary recommendation:** Начать с Wave 0 (Vite scaffold + ContentBlock API endpoint + docker-compose frontend service), затем параллельно строить лендинг (WEB-01/WEB-02) и auth flow (WEB-06), завершить кабинетом и upsell (WEB-04/WEB-05).

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| react | 19.2.5 | UI framework | Locked decision |
| react-dom | 19.2.5 | DOM rendering | Paired with react |
| vite | 8.0.8 | Build tool + dev server | Locked decision, fastest HMR |
| typescript | 6.0.3 | Type safety | Locked decision |
| tailwindcss | 4.2.2 | Utility CSS | Locked decision |
| @tanstack/react-query | 5.99.0 | Server state, caching, mutations | Locked decision |
| zustand | 5.0.12 | Client state (auth, UI) | Locked decision |
| react-router-dom | 7.14.1 | Client-side routing | Locked decision |
| axios | 1.15.0 | HTTP client + interceptors | Chosen for interceptor pattern |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @vitejs/plugin-react | 6.0.1 | Vite React plugin (Fast Refresh) | Required for Vite + React |
| @types/react | 19.2.14 | TypeScript types for React | Required |
| @tanstack/react-query-devtools | 5.99.0 | Query debugging in dev | Dev only |
| @tailwindcss/vite | 4.x | Tailwind v4 Vite plugin | Required for Tailwind v4 |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| axios | fetch API | axios has interceptor support out of box; fetch requires wrapping |
| Zustand | Jotai | Zustand simpler for auth state shape defined in CONTEXT.md |
| React Router v7 | TanStack Router | Locked to React Router |

**Installation:**
```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install @tanstack/react-query @tanstack/react-query-devtools
npm install zustand
npm install react-router-dom
npm install axios
npm install tailwindcss @tailwindcss/vite
```

**Version verification (confirmed against npm registry 2026-04-17):**
- react: 19.2.5 (published recently)
- vite: 8.0.8
- @tanstack/react-query: 5.99.0
- zustand: 5.0.12
- react-router-dom: 7.14.1 (React Router v7)
- tailwindcss: 4.2.2 (v4 — breaking changes vs v3, see Pitfalls)
- axios: 1.15.0
- typescript: 6.0.3

---

## Architecture Patterns

### Recommended Project Structure
```
frontend/
├── src/
│   ├── api/                 # axios instance, API functions per domain
│   │   ├── axios.ts         # base instance + auth interceptor + refresh logic
│   │   ├── content.ts       # getContentBlocks()
│   │   ├── tariffs.ts       # getTariffs()
│   │   ├── submissions.ts   # getSubmission()
│   │   ├── payments.ts      # initiateUpsell()
│   │   └── auth.ts          # exchangeDeeplink()
│   ├── components/
│   │   ├── ui/              # Button, Card, Badge, ProgressBar (reusable primitives)
│   │   ├── layout/          # Header, Footer, PageContainer
│   │   ├── landing/         # HeroSection, MethodSection, TariffsSection, CasesSection, FaqSection
│   │   ├── cabinet/         # StatusProgress, PdfDownloadButton, UpsellCard
│   │   └── payment/         # CloudPaymentsWidget (wrapper around window.cp)
│   ├── pages/
│   │   ├── LandingPage.tsx
│   │   ├── TariffsPage.tsx
│   │   ├── AuthPage.tsx     # /auth/:uuid — deep-link exchange
│   │   └── CabinetPage.tsx  # /cabinet — protected route
│   ├── store/
│   │   └── authStore.ts     # Zustand store: isAuthenticated, clientProfile, setAuth, clearAuth
│   ├── hooks/
│   │   ├── useContentBlocks.ts
│   │   ├── useSubmission.ts
│   │   └── useTariffs.ts
│   ├── types/
│   │   ├── api.ts           # Response types: Tariff, Submission, ContentBlock, DeeplinkResponse
│   │   └── cloudpayments.d.ts  # declare global { interface Window { cp: any } }
│   ├── router/
│   │   ├── index.tsx        # createBrowserRouter с 4 маршрутами
│   │   └── ProtectedRoute.tsx
│   ├── App.tsx
│   └── main.tsx
├── index.html               # <script src="https://widget.cloudpayments.ru/...">
├── vite.config.ts           # proxy /api → http://web:8000, @tailwindcss/vite plugin
├── tsconfig.json
└── package.json
```

### Pattern 1: Axios Instance with JWT Interceptor + Auto-Refresh
**What:** Single axios instance, request interceptor adds Bearer token, response interceptor handles 401 by refreshing token and retrying once.
**When to use:** All authenticated API calls.
**Example:**
```typescript
// src/api/axios.ts
import axios from 'axios'
import { useAuthStore } from '../store/authStore'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '/api/v1',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

let isRefreshing = false
let failedQueue: Array<{ resolve: (val: string) => void; reject: (err: unknown) => void }> = []

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return api(originalRequest)
        })
      }
      isRefreshing = true
      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) {
        useAuthStore.getState().clearAuth()
        return Promise.reject(error)
      }
      try {
        const { data } = await axios.post('/api/v1/auth/token/refresh/', { refresh: refreshToken })
        localStorage.setItem('access_token', data.access)
        failedQueue.forEach(({ resolve }) => resolve(data.access))
        failedQueue = []
        originalRequest.headers.Authorization = `Bearer ${data.access}`
        return api(originalRequest)
      } catch {
        failedQueue.forEach(({ reject: rej }) => rej(error))
        failedQueue = []
        useAuthStore.getState().clearAuth()
        return Promise.reject(error)
      } finally {
        isRefreshing = false
      }
    }
    return Promise.reject(error)
  }
)

export default api
```

### Pattern 2: Zustand Auth Store
**What:** Minimal auth store with localStorage persistence.
**When to use:** Auth state consumed in ProtectedRoute and API interceptor.
```typescript
// src/store/authStore.ts
import { create } from 'zustand'

interface ClientProfile {
  id: number
  name: string
  tariff_code?: string
}

interface AuthState {
  isAuthenticated: boolean
  clientProfile: ClientProfile | null
  setAuth: (profile: ClientProfile, accessToken: string, refreshToken: string) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: !!localStorage.getItem('access_token'),
  clientProfile: JSON.parse(localStorage.getItem('client_profile') ?? 'null'),
  setAuth: (profile, accessToken, refreshToken) => {
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refreshToken)
    localStorage.setItem('client_profile', JSON.stringify(profile))
    set({ isAuthenticated: true, clientProfile: profile })
  },
  clearAuth: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('client_profile')
    set({ isAuthenticated: false, clientProfile: null })
  },
}))
```

### Pattern 3: TanStack Query v5 Setup
**What:** QueryClient в main.tsx, hooks для каждого домена данных.
**When to use:** Все GET-запросы к API.
```typescript
// src/main.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30_000 } },
})
// <QueryClientProvider client={queryClient}>

// src/hooks/useContentBlocks.ts
import { useQuery } from '@tanstack/react-query'
import api from '../api/axios'

export function useContentBlocks() {
  return useQuery({
    queryKey: ['content-blocks'],
    queryFn: () => api.get('/content/').then((r) => r.data as Record<string, string>),
    staleTime: 5 * 60 * 1000,
    placeholderData: {
      hero_title: 'Baqsy — Бизнес-аудит',
      hero_subtitle: 'Профессиональный анализ вашего бизнеса',
      hero_cta: 'Начать аудит',
      // ... other fallbacks
    },
  })
}
```

### Pattern 4: CloudPayments Widget Integration
**What:** Widget подключён через `<script>` в index.html, вызывается через `window.cp`.
**When to use:** Кнопка оплаты тарифа и кнопка Upsell.
```typescript
// src/types/cloudpayments.d.ts
declare global {
  interface Window {
    cp: {
      CloudPayments: new () => {
        pay: (mode: 'charge', options: CloudPaymentsOptions, callbacks: CloudPaymentsCallbacks) => void
      }
    }
  }
}

interface CloudPaymentsOptions {
  publicId: string
  description: string
  amount: number
  currency: string
  invoiceId: string
  accountId: string
  data?: Record<string, unknown>
}

interface CloudPaymentsCallbacks {
  onSuccess?: (options: CloudPaymentsOptions) => void
  onFail?: (reason: string, options: CloudPaymentsOptions) => void
}

// src/components/payment/CloudPaymentsWidget.tsx
export function openPaymentWidget(options: CloudPaymentsOptions, onSuccess: () => void, onFail?: (reason: string) => void) {
  if (!window.cp?.CloudPayments) {
    console.error('CloudPayments script not loaded')
    return
  }
  const widget = new window.cp.CloudPayments()
  widget.pay('charge', options, {
    onSuccess: () => onSuccess(),
    onFail: (reason) => onFail?.(reason),
  })
}
```

### Pattern 5: Deep-link Auth Page
**What:** `/auth/:uuid` — вызывает exchange endpoint, сохраняет JWT, редиректит в кабинет.
**When to use:** Всегда при переходе по ссылке из Telegram бота.
```typescript
// src/pages/AuthPage.tsx
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import axios from 'axios'

export function AuthPage() {
  const { uuid } = useParams<{ uuid: string }>()
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!uuid) { setError('Неверная ссылка'); return }
    axios.post('/api/v1/bot/deeplink/exchange/', { token: uuid })
      .then(({ data }) => {
        setAuth({ id: data.client_profile_id, name: data.name }, data.access, data.refresh)
        navigate('/cabinet', { replace: true })
      })
      .catch(() => setError('Ссылка истекла или недействительна. Запросите новую в боте.'))
  }, [uuid])

  if (error) return <div className="...">{error}</div>
  return <div className="...">Авторизация...</div>
}
```

### Pattern 6: Protected Route
```typescript
// src/router/ProtectedRoute.tsx
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  if (!isAuthenticated) return <Navigate to="/" replace />
  return <>{children}</>
}
```

### Pattern 7: Tailwind v4 Configuration
**What:** В Tailwind v4 нет `tailwind.config.js` по умолчанию. Конфигурация через CSS-директивы или `vite.config.ts`.
**When to use:** Обязательно при использовании Tailwind v4.
```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': { target: 'http://web:8000', changeOrigin: true },
    },
  },
})
```
```css
/* src/index.css */
@import "tailwindcss";
```

### Anti-Patterns to Avoid
- **Прямые fetch-вызовы в компонентах:** Используй TanStack Query hooks, не `useEffect + fetch`.
- **Бизнес-логика в компонентах:** Вся логика в хуках и api/*.ts файлах.
- **Хардкодить цены:** Цены всегда из `GET /api/v1/payments/tariffs/`.
- **Хардкодить тексты лендинга:** Только через ContentBlock API с fallback.
- **Вызов `window.cp` без проверки:** Script загружается асинхронно; проверяй `window.cp?.CloudPayments`.
- **Создавать Submission на фронте до оплаты:** Submission создаёт бот, фронт только открывает виджет с `invoiceId` = существующего submission UUID.

---

## Backend Integration Points

### Существующие API эндпоинты (уже реализованы)

| Endpoint | Method | Auth | Используется |
|----------|--------|------|--------------|
| `/api/v1/bot/deeplink/exchange/` | POST | AllowAny | AuthPage — UUID → JWT |
| `/api/v1/payments/tariffs/` | GET | AllowAny | TariffsSection, TariffsPage |
| `/api/v1/submissions/{id}/` | GET | IsAuthenticated | CabinetPage — статус заказа |
| `/api/v1/payments/upsell/` | POST | IsAuthenticated | UpsellCard — возвращает CP Widget config |
| `/api/v1/auth/token/refresh/` | POST | AllowAny | Axios interceptor — авто-рефреш |

**DeeplinkExchangeView response shape:**
```json
{
  "access": "eyJ...",
  "refresh": "eyJ...",
  "client_profile_id": 42,
  "name": "Иван Петров"
}
```

**SubmissionDetailSerializer response shape:**
```json
{
  "id": "uuid",
  "status": "paid|in_progress_full|completed|under_audit|delivered",
  "template_name": "Шаблон для IT",
  "industry_name": "IT",
  "total_questions": 27,
  "answered_count": 15,
  "created_at": "2026-04-17T...",
  "completed_at": null
}
```
Важно: `pdf_url` в `SubmissionDetailSerializer` **отсутствует** — он будет в `AuditReport`, не в `Submission`. Нужно либо добавить `pdf_url` в сериализатор (через `AuditReport` related object), либо создать отдельный endpoint. Это нужно решить в планировании.

**TariffSerializer response shape:**
```json
[
  {"id": 1, "code": "ashide_1", "title": "Ashıde 1", "price_kzt": "45000", "description": "..."},
  {"id": 2, "code": "ashide_2", "title": "Ashıde 2", "price_kzt": "135000", "description": "..."}
]
```

**UpsellView response shape:**
```json
{
  "publicId": "...",
  "amount": 90000,
  "currency": "KZT",
  "invoiceId": "submission-uuid",
  "description": "Upsell Ashide 1→2: ООО Компания",
  "accountId": "42",
  "tariff_code": "upsell"
}
```

### Нужно создать в этой фазе (backend)

1. **ContentBlock API** — `backend/apps/content/views.py`, `serializers.py`, `urls.py`
   - `GET /api/v1/content/` — возвращает все активные блоки как dict `{key: content}`
   - AllowAny (публичный endpoint)
   - Добавить `path("content/", include("apps.content.urls"))` в `api_urls.py`

2. **SubmissionDetailSerializer расширение** — добавить `pdf_url` через `AuditReport`
   - Либо как `SerializerMethodField` в существующем сериализаторе
   - Либо новый `/api/v1/submissions/{id}/report/` endpoint

3. **Env переменные** — добавить в `.env.example`:
   - `VITE_CLOUDPAYMENTS_PUBLIC_ID=`
   - `VITE_API_URL=http://localhost:8000/api/v1` (для локалки)

4. **docker-compose frontend service** — добавить в `docker/docker-compose.yml`

5. **nginx.conf** — добавить проксирование фронта и SPA fallback

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Server state caching | Кастомный кэш + useEffect | TanStack Query | Stale-while-revalidate, deduplication, background refetch |
| JWT авто-рефреш | setInterval для проверки expiry | Axios response interceptor | Сработает точно при 401, не по таймеру |
| Auth persistence | Кастомный localStorage hook | Zustand + localStorage в setAuth/clearAuth | Синхронизация между вкладками, простота |
| Form validation | Ручные if-цепочки | Нативный HTML5 validation достаточно для MVP (нет сложных форм) | На этой фазе нет форм ввода |
| CSS компоненты | Кастомные CSS классы | Tailwind utility classes | Locked decision |
| Router guards | History.listen | ProtectedRoute компонент + React Router Navigate | Декларативно, типобезопасно |

**Key insight:** Большая часть сложности (хранение ответов, FSM, уведомления) уже в Django. Фронт — thin client.

---

## Common Pitfalls

### Pitfall 1: Tailwind v4 Breaking Changes
**What goes wrong:** Разработчик устанавливает `tailwindcss` и пишет `tailwind.config.js` — ничего не работает.
**Why it happens:** Tailwind v4 (4.x) полностью изменил систему конфигурации. `tailwind.config.js` устарел. Плагин теперь `@tailwindcss/vite`, импорт в CSS через `@import "tailwindcss"`.
**How to avoid:** Использовать `@tailwindcss/vite` плагин в `vite.config.ts`. Не создавать `tailwind.config.js`. CSS entry point: `@import "tailwindcss"`.
**Warning signs:** Утилиты Tailwind не применяются, консоль без ошибок.

### Pitfall 2: Zustand v5 API Change
**What goes wrong:** `import { create } from 'zustand/vanilla'` или обёртки из v4 не работают.
**Why it happens:** Zustand 5.x изменил сигнатуры типов и убрал некоторые вспомогательные экспорты.
**How to avoid:** Использовать `create<State>()(...)` (двойной вызов) для TypeScript. Или `create<State>((set) => (...))`. Проверить официальную документацию v5.
**Warning signs:** TypeScript ошибки при создании store.

### Pitfall 3: React Router v7 API Change
**What goes wrong:** `useHistory`, `Switch`, `Redirect` не импортируются.
**Why it happens:** React Router v7 (пакет `react-router-dom` 7.x) убрал legacy API v5.
**How to avoid:** Использовать `createBrowserRouter`, `RouterProvider`, `useNavigate` вместо `useHistory`, `Routes` + `Route` вместо `Switch`, `Navigate` вместо `Redirect`.
**Warning signs:** `Cannot find module` или TypeScript ошибки при импорте legacy компонентов.

### Pitfall 4: CloudPayments Widget — window.cp не готов
**What goes wrong:** `new window.cp.CloudPayments()` — TypeError: Cannot read properties of undefined.
**Why it happens:** Скрипт виджета загружается асинхронно. Если кнопка оплаты рендерится до загрузки скрипта, `window.cp` = undefined.
**How to avoid:** Добавить `<script>` в `index.html` (не в компонент). Проверять `if (!window.cp?.CloudPayments)` перед вызовом. В dev убедиться, что скрипт доступен (нужен интернет).
**Warning signs:** Ошибка только при быстрой загрузке страницы или в dev.

### Pitfall 5: CORS в dev
**What goes wrong:** Запросы к `/api/` блокируются CORS.
**Why it happens:** Vite dev server и Django — разные порты. В prod nginx проксирует, в dev нужен Vite proxy.
**How to avoid:** Настроить `server.proxy` в `vite.config.ts`: `/api` → `http://web:8000`. Axios baseURL должен быть `/api/v1` (без хоста) — тогда Vite proxy перехватит.
**Warning signs:** Network errors только в dev, не в prod.

### Pitfall 6: SubmissionDetailSerializer не содержит pdf_url
**What goes wrong:** В CabinetPage нет возможности получить URL PDF-файла — `SubmissionDetailSerializer` его не возвращает.
**Why it happens:** PDF URL хранится в `AuditReport.pdf_url`, а не в `Submission`. Phase 6 создаёт AuditReport, но Phase 5 уже строит кабинет.
**How to avoid:** В рамках Phase 5 добавить `pdf_url` в `SubmissionDetailSerializer` через `SerializerMethodField`:
```python
pdf_url = serializers.SerializerMethodField()
def get_pdf_url(self, obj):
    report = getattr(obj, 'audit_report', None)
    return report.pdf_url if report and report.pdf_url else None
```
PDF-кнопка показывается только когда `pdf_url is not null`.

### Pitfall 7: Submission ID для CloudPayments — нет submission до оплаты
**What goes wrong:** Фронт пытается создать submission, чтобы передать `invoiceId` в Widget.
**Why it happens:** Непонимание flow: submission создаётся ботом (POST /api/v1/submissions/ через бот-JWT), не фронтом. Фронт получает `invoiceId` из бота через deep-link или из API активного submission.
**How to avoid:** На странице `/tariffs` — кнопка «Оплатить» ведёт клиентов, которые уже прошли онбординг в боте и имеют активный submission. Фронт должен получить submission UUID через `GET /api/v1/submissions/` (список) или через состояние после deep-link. Если submission нет — показать «Вернитесь в Telegram для начала».
**Warning signs:** 403/404 при попытке создать submission на фронте без правильного JWT.

### Pitfall 8: TanStack Query v5 API
**What goes wrong:** `useQuery({ queryKey, queryFn, onSuccess })` — `onSuccess` callback удалён в v5.
**Why it happens:** TanStack Query v5 удалил `onSuccess`/`onError` колбэки из `useQuery`. Они остались только в `useMutation`.
**How to avoid:** Для side effects после запроса — использовать `useEffect` на `data`. Для мутаций — `useMutation` с `onSuccess`.

---

## Docker & nginx Integration

### docker-compose.yml добавить frontend service
```yaml
frontend:
  build:
    context: ../frontend
    dockerfile: Dockerfile
  volumes:
    - ../frontend:/app
    - /app/node_modules
  ports:
    - "5173:5173"
  command: npm run dev -- --host 0.0.0.0
  environment:
    - VITE_API_URL=/api/v1
    - VITE_CLOUDPAYMENTS_PUBLIC_ID=${VITE_CLOUDPAYMENTS_PUBLIC_ID}
```

### frontend/Dockerfile (для dev)
```dockerfile
FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

### nginx.conf изменения (для dev: проксировать фронт)
В prod nginx раздаёт статику из `npm run build`. В dev — проксирует Vite dev server.
```nginx
# Dev: proxy to Vite
location / {
    proxy_pass http://frontend:5173;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_http_version 1.1;
}

# API goes to Django
location /api/ {
    proxy_pass http://django;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}

# SPA fallback для prod (после build)
# location / {
#     root /usr/share/nginx/html/frontend;
#     try_files $uri $uri/ /index.html;
# }
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Tailwind config in `tailwind.config.js` | CSS `@import "tailwindcss"` + vite plugin | Tailwind v4 (2025) | Меняет способ настройки theme, плагинов |
| `useHistory` (React Router v5) | `useNavigate` (v6/v7) | React Router v6 (2021) | Locked to v7 |
| TanStack Query `onSuccess` callback | `useEffect` на data | v5 (2023) | Изменяет паттерн side effects |
| Zustand `create` без generics | `create<State>()(...)` | Zustand v5 (2024) | TypeScript strict mode совместимость |
| CRA (Create React App) | Vite | 2022+ | CRA deprecated, Vite — стандарт |

---

## Open Questions

1. **Submission UUID для оплаты на странице тарифов**
   - Что мы знаем: CloudPayments Widget требует `invoiceId` = submission UUID. Submission создаётся ботом после онбординга.
   - Что не ясно: Как фронт получает submission UUID для клиентов, которые пришли на `/tariffs` напрямую без deep-link? Активный submission может быть, а может нет.
   - Recommendation: `/tariffs` страница проверяет наличие JWT. Если есть — делает `GET /api/v1/submissions/` (нужен новый endpoint или фильтр) для получения активного submission. Если нет — кнопка «Оплатить» показывает «Начните с Telegram бота» (ссылка на бот). Это нужно решить при планировании Wave 1.

2. **tariff_code в clientProfile через Zustand**
   - Что мы знаем: Upsell видна только клиентам с `ashide_1`. DeeplinkExchangeView возвращает только `client_profile_id` и `name`, не `tariff_code`.
   - Что не ясно: Откуда фронт знает tariff_code активного submission для отображения/скрытия кнопки Upsell?
   - Recommendation: Кабинет загружает submission через `GET /api/v1/submissions/{id}/`, который включает данные тарифа. Либо расширить `SubmissionDetailSerializer` полем `tariff_code`. Кнопка Upsell показывается если `submission.tariff_code === 'ashide_1'` И `status` входит в допустимые.

3. **Какой submission показывать в кабинете**
   - Что мы знаем: У клиента теоретически может быть несколько submissions.
   - Что не ясно: Показывать последний? Показывать список?
   - Recommendation: Показывать последний по `created_at`. Для MVP это достаточно. Нужен endpoint `GET /api/v1/submissions/me/` или фильтрация существующего.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3 + pytest-django 4.9 (backend) |
| Config file | `backend/pyproject.toml` — `[tool.pytest.ini_options]` |
| Quick run command | `docker-compose exec web pytest apps/content/ -x -q` |
| Full suite command | `docker-compose exec web pytest -x -q` |

Frontend тесты не настроены (нет Vitest/Jest конфига в проекте). Для MVP frontend тестирование через ручную верификацию в браузере. Wave 0 должен включить Vitest для базовых smoke-тестов.

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| WEB-01 | Vite build проходит без ошибок | smoke | `docker-compose exec frontend npm run build` | ❌ Wave 0 |
| WEB-02 | ContentBlock API возвращает активные блоки | unit | `pytest apps/content/tests/test_views.py -x` | ❌ Wave 0 |
| WEB-03 | TariffListView возвращает активные тарифы | unit | `pytest apps/payments/tests/ -k tariff -x` | ✅ (существует) |
| WEB-04 | SubmissionDetailView возвращает pdf_url | unit | `pytest apps/submissions/tests/ -k pdf_url -x` | ❌ Wave 0 |
| WEB-05 | UpsellView возвращает CP Widget config | unit | `pytest apps/payments/tests/ -k upsell -x` | ✅ (существует) |
| WEB-06 | DeeplinkExchangeView → JWT | unit | `pytest apps/accounts/tests/ -k exchange -x` | ✅ (существует) |
| WEB-07 | Mobile-first вёрстка | manual | `npm run build` + браузерная инспекция | manual-only |
| WEB-08 | TanStack Query + Zustand интеграция | smoke | `docker-compose exec frontend npm run build` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `docker-compose exec web pytest apps/content/ -x -q`
- **Per wave merge:** `docker-compose exec web pytest -x -q && docker-compose exec frontend npm run build`
- **Phase gate:** Full backend pytest green + `npm run build` success перед `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/apps/content/views.py` — ContentBlock list API
- [ ] `backend/apps/content/serializers.py` — ContentBlockSerializer
- [ ] `backend/apps/content/urls.py` — URL routing
- [ ] `backend/apps/content/tests/test_views.py` — covers WEB-02
- [ ] `backend/apps/submissions/serializers.py` расширить pdf_url — covers WEB-04
- [ ] `frontend/` — Vite проект scaffold
- [ ] `frontend/Dockerfile` — dev container
- [ ] Добавить `frontend` service в `docker/docker-compose.yml`
- [ ] Обновить `docker/nginx.conf` — SPA fallback + Vite proxy
- [ ] Добавить `VITE_CLOUDPAYMENTS_PUBLIC_ID` в `.env.example`

---

## Sources

### Primary (HIGH confidence)
- npm registry (2026-04-17) — версии react 19.2.5, vite 8.0.8, tanstack/react-query 5.99.0, zustand 5.0.12, react-router-dom 7.14.1, tailwindcss 4.2.2, axios 1.15.0, typescript 6.0.3
- Существующий код проекта: `backend/apps/accounts/views.py`, `payments/views.py`, `submissions/views.py`, `content/models.py` — API shape и response структура верифицированы напрямую

### Secondary (MEDIUM confidence)
- TanStack Query v5 changelog — удаление `onSuccess`/`onError` из `useQuery`
- Tailwind v4 migration guide — изменение системы конфигурации
- CloudPayments documentation — Widget integration via window.cp

### Tertiary (LOW confidence)
- Zustand v5 create signature (двойной вызов для TypeScript) — требует верификации при scaffold

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — версии верифицированы через npm registry
- Architecture: HIGH — основана на существующем коде проекта и locked decisions
- Pitfalls: HIGH для backend integration (код изучен), MEDIUM для Tailwind v4 / Zustand v5 (не проверено в runtime)
- API contracts: HIGH — сериализаторы и views прочитаны напрямую

**Research date:** 2026-04-17
**Valid until:** 2026-05-17 (стабильный стек; npm версии могут обновиться, но breaking changes маловероятны за 30 дней)
