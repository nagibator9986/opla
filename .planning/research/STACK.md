# Stack Research

**Domain:** Business audit SaaS — Django + aiogram + React + payments + async PDF + WhatsApp delivery
**Researched:** 2026-04-15
**Confidence:** HIGH (all core versions verified against PyPI/official docs)

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.12 | Runtime | LTS, latest stable, broad library support; 3.13 still too new for aiogram ecosystem |
| Django | 5.2 LTS | Web framework + ORM + Admin CRM | Released 2025-04-02, LTS until 2028-04. Strong Admin, migrations, JSONB support via postgres. Explicit client requirement: "популярный стек" |
| Django REST Framework | 3.17.1 | REST API layer | Released 2026-03-24, Django 5.2 compatible. Standard for Django APIs, supports ViewSets, serializers, permissions cleanly |
| PostgreSQL | 16 | Primary database | JSONB for `Answer.value`, indexable, mature Django support. Client requirement |
| Redis | 7.x | Celery broker + result backend + aiogram FSM storage | Single dependency serves three roles; no need for separate message broker |
| Celery | 5.6.3 | Async task queue | Released 2026-03-26. Handles PDF generation, WhatsApp delivery, payment webhook processing, upsell reminders |
| aiogram | 3.27.0 | Telegram bot framework | Released 2026-04-03, production-stable. Native async, built-in FSM, Redis storage included |
| React | 18.x | Frontend SPA | Client requirement. Concurrent features, stable ecosystem, TS support |
| Vite | 6.x | Frontend build tool | Faster HMR than CRA/webpack, native ESM, TS out of the box |
| TypeScript | 5.x | Frontend type safety | Standard for React in 2025+ |

### Backend Libraries

| Library | Version | Purpose | Notes |
|---------|---------|---------|-------|
| djangorestframework-simplejwt | 5.5.1 | JWT auth for API + bot calls | Released 2025-07-21. Bot authenticates as service account via API key or JWT. Admin uses Django session |
| django-storages[s3] | 1.14.6 | MinIO/S3 file storage for PDFs | Set `AWS_S3_ENDPOINT_URL` to MinIO URL; boto3 handles the rest |
| boto3 | latest (>=1.4.4) | AWS/S3 SDK used by django-storages | Pin to `>=1.35` for Python 3.12 compatibility |
| WeasyPrint | 68.1 | HTML+CSS → PDF generation | Released 2026-02-06. Best CSS support (flexbox/grid), pure Python rendering engine. See WeasyPrint section below |
| Jinja2 | 3.x | PDF template rendering | Use Jinja2 (not Django templates) for PDF templates — better whitespace control, filters, macros |
| Celery | 5.6.3 | Background tasks | `@shared_task` pattern; separate queues for pdf, delivery, webhooks |
| redis (py) | >=5.0 | Redis client for Celery + aiogram | `pip install redis` — aiogram 3 uses this directly (not aioredis) |
| django-celery-beat | 2.x | Periodic tasks (upsell reminders) | Stores beat schedule in DB, manageable from Admin |
| django-celery-results | 2.x | Task result storage in DB | Optional but useful for CRM visibility into task status |
| structlog | 25.x | Structured JSON logging | Production: JSON output. Dev: colorized console. See django-structlog |
| django-structlog | 10.0.0 | Django request context in logs | Auto-adds request_id, user, IP to every log line |
| psycopg2-binary | 2.9.x | PostgreSQL adapter | Use `-binary` for Docker simplicity; switch to `psycopg2` (compiled) only if C extension performance needed |
| gunicorn | 22.x | WSGI server for Django | Standard prod WSGI server; 4 workers × 2 threads for a VPS |
| django-cors-headers | 4.x | CORS for React frontend | Required when React dev server (port 5173) calls Django API (port 8000) |
| python-decouple | 3.x | `.env` config management | Cleaner than `os.environ.get()`, supports `.env` files with type casting |

### Telegram Bot Libraries

| Library | Version | Purpose | Notes |
|---------|---------|---------|-------|
| aiogram | 3.27.0 | Bot framework | FSM, middleware, filters, routers |
| redis (py) | >=5.0 | FSM state storage | `RedisStorage.from_url("redis://redis:6379/1", state_ttl=86400, data_ttl=604800)` |
| httpx | 0.27.x | Async HTTP client for Django API calls | Bot is thin client; all business logic calls go to Django REST API |

### Frontend Libraries

| Library | Version | Purpose | Notes |
|---------|---------|---------|-------|
| TanStack Query (React Query) | v5 | Server state management | Replaces Redux for all API data. Handles caching, loading states, refetch. Perfect fit for cabinet/tariff pages |
| Zustand | 4.x | Client state (UI state only) | Cart step, modal open/close, current user object. Lighter than Redux for this scope |
| Tailwind CSS | 4.x | Styling | Utility-first, no CSS files to maintain; Vite plugin available |
| React Router | 6.x | Client-side routing | Standard. Use `createBrowserRouter` (v6 data API) |
| React Hook Form | 7.x | Form handling | Lightweight, integrates with Zod for validation |
| Zod | 3.x | Schema validation | API response validation + form schemas; pairs with RHF |
| axios | 1.x | HTTP client | Interceptors for JWT inject/refresh; TanStack Query fetcher |
| CloudPayments Widget | CDN | Payment UI | Official JS widget loaded via `<script>` tag; no npm package |

### Infrastructure

| Technology | Version | Purpose | Notes |
|------------|---------|---------|-------|
| Docker | 26.x | Containerization | Required for "2-hour deploy on new host" requirement |
| Docker Compose | 2.x | Local dev + prod orchestration | Single `docker-compose.yml` with `override` for dev |
| nginx | 1.27.x | Reverse proxy + static files | Routes `/api/` → gunicorn, `/` → React static, `/bot/webhook/` → bot |
| MinIO | RELEASE.2025+ | S3-compatible object storage | PDF storage, PG backup dumps |

### Testing

| Library | Version | Purpose | Notes |
|---------|---------|---------|-------|
| pytest | 8.x | Test runner (Python) | Standard |
| pytest-django | 4.x | Django fixtures, DB, client | `@pytest.mark.django_db` for model tests |
| pytest-asyncio | 0.23.x | Async test support for aiogram handlers | Required for testing bot handlers |
| factory-boy | 3.x | Test data factories | `ClientProfileFactory`, `SubmissionFactory` etc. |
| pytest-mock | 3.x | Mocking in pytest | For mocking CloudPayments, Wazzup24, WeasyPrint calls |
| vitest | 2.x | Frontend unit tests | Native Vite integration, Jest-compatible API, fast |
| React Testing Library | 14.x | Component testing | Behavior-driven component tests with vitest |
| Playwright | 1.x | E2E tests | Browser automation; use `pytest-playwright` for Python integration |
| coverage | 7.x | Coverage reporting | `--cov=apps --cov-report=html` |

---

## Integration-Specific Notes

### CloudPayments KZ — HMAC Webhook Validation

**Status:** No official Python SDK that is actively maintained for KZ. The `antidasoftware/cloudpayments-python-client` exists but requires Python 2.7/3.4+, last active in 2020s, last Python 2 era. **Do NOT use it.**

**Recommended approach:** Custom implementation using Python stdlib `hmac` module.

CloudPayments sends both `Content-HMAC` and `X-Content-HMAC` headers on webhook notifications:
- `Content-HMAC` — HMAC of URL-encoded request body
- `X-Content-HMAC` — HMAC of URL-decoded request body (raw body)

Algorithm: HMAC-SHA256, key = API Secret from CloudPayments merchant account, base64-encoded digest.

```python
import hmac
import hashlib
import base64
from django.conf import settings

def verify_cloudpayments_hmac(request) -> bool:
    body = request.body  # raw bytes
    secret = settings.CLOUDPAYMENTS_API_SECRET.encode("utf-8")
    expected = base64.b64encode(
        hmac.new(secret, body, hashlib.sha256).digest()
    ).decode()
    received = request.headers.get("Content-HMAC", "")
    return hmac.compare_digest(expected, received)
```

Use `hmac.compare_digest()` (constant-time comparison) to prevent timing attacks.

Idempotency: store `TransactionId` in `Payment` model with `unique=True` constraint; catch `IntegrityError` on duplicate webhook delivery.

**Confidence:** MEDIUM — header names verified from CloudPayments developer docs snippets; HMAC algorithm confirmed from multiple integration sources. Recommend testing against sandbox before production.

---

### aiogram 3 — Redis FSM Storage Setup

Built-in. No external package needed beyond `redis` (pure Python client).

```python
from aiogram.fsm.storage.redis import RedisStorage

storage = RedisStorage.from_url(
    url="redis://redis:6379/1",   # DB 1 — separate from Celery on DB 0
    state_ttl=86400,              # 24h — user session doesn't expire during questionnaire
    data_ttl=604800,              # 7d  — keep FSM data for re-entry
)

dp = Dispatcher(storage=storage)
```

Key points:
- Use DB index `1` for FSM, `0` for Celery broker, `2` for Celery results — avoids key collisions
- `state_ttl` and `data_ttl` accept `int` (seconds) or `datetime.timedelta`
- In production (webhook mode), bot runs as a separate Docker service (`bot`) pointing to same Redis

**Confidence:** HIGH — verified from official aiogram 3.25+ docs.

---

### Wazzup24 — WhatsApp PDF Delivery

The `wazzup-api-python` package on PyPI (v0.1.0, released 2024-03-23) is too immature — single version, minimal maintenance signal.

**Recommended approach:** Direct HTTP calls via `httpx` (async) or `requests` in a Celery task. Wrap in an abstraction class for future provider swap (Green API, 360dialog).

```python
# delivery/providers/wazzup.py
import httpx

class WazzupProvider:
    BASE = "https://api.wazzup24.com/v3"

    def __init__(self, api_key: str, channel_id: str):
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.channel_id = channel_id

    def send_file(self, phone: str, file_url: str, caption: str) -> dict:
        payload = {
            "channelId": self.channel_id,
            "chatType": "whatsapp",
            "chatId": phone,
            "text": caption,
            "contentUri": file_url,
        }
        r = httpx.post(f"{self.BASE}/message", json=payload, headers=self.headers)
        r.raise_for_status()
        return r.json()
```

The abstraction `delivery.providers.WhatsAppProvider` (mentioned in CLAUDE.md) allows switching to Green API without changing Celery task code.

**Confidence:** MEDIUM — Wazzup24 API docs confirmed REST endpoint at `/v3/message`; exact payload field names should be validated against current docs before implementation.

---

### WeasyPrint — PDF Generation Decision

**Verdict: Keep WeasyPrint. It is the right choice for this project.**

Comparison for this use case (branded HTML reports with CSS layout):

| Library | CSS Support | Complexity | Docker deps | Verdict |
|---------|-------------|------------|-------------|---------|
| WeasyPrint 68.1 | Full (flexbox, grid, CSS3) | Low | libpango, libharfbuzz | **Use this** |
| xhtml2pdf | CSS 2.1 only, no flex/grid | Low | Pure Python | Rejected — can't do branded layouts |
| ReportLab | Programmatic only, no HTML | High | None | Rejected — requires rebuilding templates as Python code |
| Puppeteer/Chrome | Full CSS | High | Full Chromium (~300MB) | Overkill for a background task |

WeasyPrint Docker dependencies (Debian-based image):
```dockerfile
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz-subset0 \
    libharfbuzz0b \
    && rm -rf /var/lib/apt/lists/*
```

Use Jinja2 for template rendering (not Django's template engine) — gives more control over whitespace, macros for repeated blocks, and avoids Django template auto-escaping issues with HTML.

**Confidence:** HIGH — version verified from PyPI; system deps verified from official docs.

---

### React State Management Decision

**Use TanStack Query v5 for server state + Zustand for client state. Do NOT use Redux.**

Rationale for this project:
- 90%+ of frontend state is server state (tariff list, submission status, payment status, cabinet data)
- TanStack Query v5 handles all API fetching with automatic caching, background refresh, loading/error states
- Redux would add 200+ lines of boilerplate for no benefit in a project this size
- Zustand handles the small amount of true client state: current user object after login, modals, CloudPayments widget open/close state

Redux Toolkit would only make sense if: (a) complex shared UI state across many disconnected components, or (b) team already uses Redux heavily. Neither applies here.

**Confidence:** HIGH — consensus across multiple 2025 sources, TanStack Query v5 API stable since 2023.

---

## Alternatives Considered

| Recommended | Alternative | Why Not |
|-------------|-------------|---------|
| aiogram 3.x | python-telegram-bot 21.x | aiogram is fully async, better FSM, more active for production bots in RU/KZ ecosystem |
| WeasyPrint | Puppeteer/headless Chrome | Chrome adds ~300MB to Docker image; overkill when WeasyPrint handles CSS3 fully |
| WeasyPrint | xhtml2pdf | xhtml2pdf has CSS 2.1 only; can't do modern branded layouts |
| Celery + Redis | Django-Q2 / Huey | Celery 5.x is standard; better monitoring tooling (Flower); team familiarity |
| TanStack Query + Zustand | Redux Toolkit | RTK is 3x more boilerplate for server state; no benefit at this project scale |
| Custom HMAC (CloudPayments) | antidasoftware/cloudpayments-python-client | Library targets Python 2 era, not maintained, doesn't explicitly handle HMAC validation |
| Direct httpx (Wazzup24) | wazzup-api-python | PyPI package at v0.1.0 from 2024; minimal maintenance; direct HTTP more transparent |
| psycopg2-binary | asyncpg | Django ORM is synchronous; asyncpg only useful with Django async views or raw async queries |
| Gunicorn | uvicorn | Django's async support is partial; gunicorn is simpler and stable for sync Django |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| aiogram 2.x | EOL, synchronous, different API entirely | aiogram 3.27.0 |
| aioredis | Deprecated; aiogram 3 switched to `redis` package directly | `redis` (pip install redis) |
| django-channels | WebSocket complexity not needed; all delivery is async via Celery+bot | Celery + aiogram polling/webhook |
| Redux (alone) | Excessive boilerplate for server-state-heavy SPA | TanStack Query v5 + Zustand |
| wkhtmltopdf | Abandoned project (no updates since 2023), large binary, Qt dependency | WeasyPrint 68.x |
| python-telegram-bot (sync) | Synchronous, blocking; doesn't fit async architecture | aiogram 3.x |
| CRA (create-react-app) | Abandoned by Meta, no Vite HMR, outdated toolchain | Vite 6.x |
| Django 4.x | Not LTS, overlapping with 5.2 LTS release | Django 5.2 LTS |

---

## Version Compatibility Matrix

| Package | Requires | Compatible With | Notes |
|---------|----------|-----------------|-------|
| Django 5.2 | Python 3.10–3.14 | DRF 3.17.x, psycopg2 2.9.x | LTS — prefer for this project |
| DRF 3.17.1 | Django 4.2–6.0 | Django 5.2 | Confirmed compatible |
| aiogram 3.27.0 | Python 3.9+ | redis>=5.0 | Uses `redis` not `aioredis` |
| WeasyPrint 68.1 | Python 3.10+ | Pango >=1.44 | Requires system libs in Docker |
| Celery 5.6.3 | Python 3.8+ | Redis 7.x, Django 5.x | Use `django-celery-beat` for Beat |
| simplejwt 5.5.1 | Django 4.2–5.2 | DRF 3.14+ | Works with Django 5.2 |
| TanStack Query | React 18+ | React Router 6.x | v5 API (useQuery, not deprecated useQuery from v4) |

---

## Installation

### Backend (requirements.txt)

```
Django==5.2
djangorestframework==3.17.1
djangorestframework-simplejwt==5.5.1
psycopg2-binary==2.9.10
redis==5.3.0
celery==5.6.3
django-celery-beat==2.7.0
django-celery-results==2.5.1
django-storages[s3]==1.14.6
boto3>=1.35
WeasyPrint==68.1
Jinja2==3.1.6
django-cors-headers==4.6.0
python-decouple==3.8
structlog==25.5.0
django-structlog==10.0.0
gunicorn==23.0.0
httpx==0.27.0
```

### Bot (bot/requirements.txt)

```
aiogram==3.27.0
redis==5.3.0
httpx==0.27.0
python-decouple==3.8
structlog==25.5.0
```

### Frontend

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install \
  @tanstack/react-query \
  zustand \
  react-router-dom \
  react-hook-form \
  @hookform/resolvers \
  zod \
  axios \
  tailwindcss \
  @tailwindcss/vite

npm install -D \
  vitest \
  @vitest/ui \
  @testing-library/react \
  @testing-library/jest-dom \
  @playwright/test \
  @types/node
```

---

## Sources

- [aiogram 3.27.0 PyPI](https://pypi.org/project/aiogram/) — version confirmed
- [aiogram FSM Redis Storage docs 3.25+](https://docs.aiogram.dev/en/latest/dispatcher/finite_state_machine/storages.html) — RedisStorage.from_url, TTL params
- [Django 5.2 release](https://www.djangoproject.com/weblog/2025/apr/02/django-52-released/) — LTS status, Python compatibility
- [DRF 3.17.1 PyPI](https://pypi.org/project/djangorestframework/) — version, Django 5.2 compatibility
- [simplejwt 5.5.1 PyPI](https://pypi.org/project/djangorestframework-simplejwt/) — version confirmed
- [Celery 5.6.3 PyPI](https://pypi.org/project/celery/) — version confirmed
- [WeasyPrint 68.1 PyPI](https://pypi.org/project/weasyprint/) — version confirmed
- [WeasyPrint First Steps docs](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html) — Linux system deps
- [django-storages S3 docs 1.14.6](https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html) — MinIO config
- [CloudPayments developers (EN)](https://developers.cloudpayments.ru/en/) — webhook HMAC headers
- [wazzup-api-python PyPI](https://pypi.org/project/wazzup-api-python/) — v0.1.0, 2024, immature
- [Wazzup24 API docs](https://wazzup24.com/help/api-en/) — REST endpoint structure
- [TanStack Query vs Redux 2025 — IT Labs](https://www.it-labs.com/stop-using-redux-for-server-state-why-tanstack-query-is-the-better-choice-in-2025/) — state management recommendation
- [django-structlog 10.0.0 docs](https://django-structlog.readthedocs.io/en/latest/) — structured logging Django integration

---
*Stack research for: Baqsy System — Business audit SaaS (Django + aiogram + React)*
*Researched: 2026-04-15*
