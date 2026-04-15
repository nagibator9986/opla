# Architecture Research

**Domain:** Telegram bot + Django REST API + React SPA + payment webhook + async delivery pipeline
**Researched:** 2026-04-15
**Confidence:** HIGH (patterns verified against official docs and established community templates)

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────┐
│                      CLIENT ENTRY POINTS                      │
│  ┌──────────────────┐          ┌─────────────────────────┐   │
│  │   Telegram Bot    │          │   React SPA (browser)    │   │
│  │   (aiogram 3)     │          │   Landing / Tariffs / LK │   │
│  └────────┬─────────┘          └────────────┬────────────┘   │
└───────────┼────────────────────────────────┼────────────────┘
            │ REST (httpx/aiohttp)            │ REST (fetch/axios)
            ▼                                ▼
┌──────────────────────────────────────────────────────────────┐
│                     NGINX REVERSE PROXY                       │
│   /api/*  → Django:8000   /tg-webhook → Django:8000          │
│   /*      → React static  /static/*   → Whitenoise/volume    │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│                    DJANGO 5 + DRF (web)                       │
│  ┌────────────┐ ┌────────────┐ ┌──────────┐ ┌─────────────┐ │
│  │ accounts/  │ │industries/ │ │payments/ │ │ reports/    │ │
│  │ ClientProf │ │ Template   │ │ Tariff   │ │ AuditReport │ │
│  │ Auth (JWT) │ │ Question   │ │ Payment  │ │ delivery/   │ │
│  └────────────┘ └────────────┘ └──────────┘ └─────────────┘ │
│  ┌────────────┐ ┌────────────┐ ┌────────────────────────────┐│
│  │submissions/│ │ dashboard/ │ │  Django Admin (CRM)        ││
│  │ Submission │ │  Stats API │ │  custom actions + views    ││
│  │ Answer     │ └────────────┘ └────────────────────────────┘│
│  └────────────┘                                               │
└──────────────────────────┬───────────────────────────────────┘
          ┌─────────────────┤ Celery tasks via Redis broker
          │                 │
┌─────────▼──────┐  ┌───────▼──────────────────────────────┐
│  PostgreSQL 16  │  │         Celery Worker (worker)        │
│  Source of truth│  │  generate_pdf | deliver_wa            │
│  JSONB answers  │  │  send_tg_notification | upsell_remind │
└────────────────┘  └───────────────┬──────────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          │                         │                          │
┌─────────▼──────┐  ┌───────────────▼────┐  ┌────────────────▼┐
│  Redis          │  │  MinIO (S3-compat.) │  │  External APIs  │
│  Celery broker  │  │  PDF storage        │  │  Telegram Bot   │
│  aiogram FSM    │  │  PG backup dumps    │  │  Wazzup24 WA    │
│  (key prefixes) │  └────────────────────┘  │  CloudPayments  │
└────────────────┘                           └─────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Protocol / Interface |
|-----------|----------------|----------------------|
| aiogram 3 bot process | Telegram FSM, user dialogue, deep-link generation, file delivery | Telegram Bot API (polling/webhook); calls Django REST |
| Django + DRF | All business logic: profiles, submissions, payments, templates, PDF queuing | HTTP REST API + Django Admin |
| Django Admin (CRM) | Operator views order queue, writes audit text, triggers delivery | Django session auth, custom views |
| Celery worker | Heavy/async tasks: PDF render, WA send, TG notify, upsell beat | Redis broker; calls Django ORM directly (same codebase) |
| Celery beat | Scheduled tasks: upsell reminders, PG backup cron | Celery periodic tasks |
| React SPA | Landing, tariff page with CP widget, client cabinet (order status, PDF link) | REST API with JWT |
| PostgreSQL 16 | Source of truth; JSONB for Answer.value and Question.options | Django ORM only — no direct external access |
| Redis | Celery broker (db=0) + aiogram FSM storage (db=1 or prefix namespace) | Redis protocol |
| MinIO | PDF blob storage, PG dump backups | S3-compatible; boto3/django-storages |
| CloudPayments | Payment collection; sends webhooks | HTTPS webhook POST to Django |
| Wazzup24 | WhatsApp delivery of PDF + message | REST API (POST /v3/message) |
| nginx | TLS termination, routing, static serving | Reverse proxy |

## Recommended Project Structure

```
baqsy-system/
├── backend/
│   ├── baqsy/
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── dev.py
│   │   │   └── prod.py
│   │   ├── celery.py
│   │   └── urls.py
│   ├── apps/
│   │   ├── accounts/        # ClientProfile, JWT auth endpoints
│   │   ├── industries/      # Industry, QuestionnaireTemplate, Question
│   │   ├── submissions/     # Submission, Answer, state machine
│   │   ├── payments/        # Tariff, Payment, CP webhook endpoint
│   │   ├── reports/         # AuditReport model, PDF task trigger
│   │   ├── delivery/        # DeliveryLog, TG+WA provider abstraction
│   │   └── dashboard/       # Aggregated stats for admin
│   ├── templates/
│   │   └── pdf/             # Jinja2 HTML templates for WeasyPrint
│   └── manage.py
├── bot/
│   ├── handlers/
│   │   ├── start.py         # /start, deep-link token decode
│   │   ├── onboarding.py    # 5-question FSM
│   │   ├── questionnaire.py # per-question FSM loop
│   │   └── delivery.py      # send PDF document
│   ├── states/
│   │   ├── onboarding.py    # OnboardingStates(StatesGroup)
│   │   └── questionnaire.py # QuestionnaireStates(StatesGroup)
│   ├── services/
│   │   └── api_client.py    # httpx AsyncClient → Django REST
│   ├── middlewares/
│   │   └── auth.py          # attach ClientProfile from telegram_id
│   └── main.py              # Dispatcher, RedisStorage, startup
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Landing.tsx
│   │   │   ├── Tariffs.tsx  # CP widget integration
│   │   │   └── Cabinet.tsx  # order status + PDF link
│   │   ├── api/             # axios/fetch wrappers
│   │   └── main.tsx
│   └── vite.config.ts
├── docker/
│   ├── docker-compose.yml        # dev
│   ├── docker-compose.prod.yml   # prod overrides
│   └── nginx.conf
├── .env.example
└── README.md
```

### Structure Rationale

- **bot/services/api_client.py:** All Django REST calls go through one module — single point to add auth headers, retries, and base URL config. Bot has no ORM imports.
- **apps split by domain:** Enables phased development; each app owns its models and serializers. CRM views live in the same Django process — no separate service needed for v1.
- **templates/pdf/:** Jinja2 (not Django templates) enables richer CSS layouts and WeasyPrint compatibility.
- **docker-compose.prod.yml** as override file (not replacement): shares service definitions, only overrides replicas, volumes, and image tags.

## Architectural Patterns

### Pattern 1: Bot as Thin REST Client (Django-First Logic)

**What:** The aiogram bot process contains zero business logic. Every state transition, data save, and validation happens via a call to Django REST. The bot is a pure dialogue layer — it asks questions, collects text, calls `/api/`, and reacts to responses.

**When to use:** Always. This is the founding invariant of the system.

**Why REST over shared ORM:**
- Bot runs in a separate Python process and Docker container. Importing Django ORM from outside the Django app creates initialization complexity (`django.setup()` in every module) and tight coupling.
- REST calls are versioned, testable with mock servers, and replaceable. If the bot framework changes (e.g., to python-telegram-bot), the API contract stays.
- Celery workers DO share the ORM (same codebase), because they run inside Django's app context. This is the correct exception: workers are co-located logic, not external clients.

**Confidence:** HIGH — confirmed by community patterns and the aiogram-django-template reference architecture.

```python
# bot/services/api_client.py
import httpx, os

BASE = os.environ["DJANGO_API_URL"]   # http://web:8000/api
BOT_SECRET = os.environ["BOT_API_SECRET"]  # shared secret header

class BaqsyAPIClient:
    def __init__(self):
        self._client = httpx.AsyncClient(
            base_url=BASE,
            headers={"X-Bot-Secret": BOT_SECRET},
            timeout=10.0,
        )

    async def create_profile(self, telegram_id: int, data: dict) -> dict:
        r = await self._client.post("/clients/", json={"telegram_id": telegram_id, **data})
        r.raise_for_status()
        return r.json()

    async def save_answer(self, submission_id: int, question_id: int, value) -> None:
        r = await self._client.post(
            f"/submissions/{submission_id}/answers/",
            json={"question_id": question_id, "value": value},
        )
        r.raise_for_status()
```

### Pattern 2: Redis Namespace Separation (FSM vs Celery)

**What:** Use the same Redis instance for both aiogram FSM storage and Celery broker, but isolate them by Redis database index (not just key prefix). Celery uses `db=0`, aiogram RedisStorage uses `db=1`. This gives hard isolation — a FLUSHDB on the FSM database cannot accidentally wipe Celery queues.

**When to use:** When running a single Redis container in Docker Compose (standard for this scale).

**Trade-offs:** Slightly more config lines; completely eliminates key collision risk. Alternative (key prefix only) is sufficient but harder to inspect with redis-cli.

```python
# bot/main.py
from aiogram.fsm.storage.redis import RedisStorage
import redis.asyncio as aioredis

redis_fsm = aioredis.Redis(host="redis", port=6379, db=1)
storage = RedisStorage(
    redis=redis_fsm,
    key_builder=DefaultKeyBuilder(prefix="fsm", with_bot_id=True),
    state_ttl=86400 * 7,   # 7 days — survives bot restarts
    data_ttl=86400 * 7,
)
```

```python
# backend/baqsy/settings/base.py
CELERY_BROKER_URL = "redis://redis:6379/0"
CELERY_RESULT_BACKEND = "redis://redis:6379/0"
```

### Pattern 3: Immutable Template Versioning

**What:** A `QuestionnaireTemplate` record is never edited in place. When an admin modifies an industry questionnaire, the system creates a new record with `version = old.version + 1` and sets `is_active = True` on the new record and `is_active = False` on the old one. `Submission.template` is a FK to a specific version row — it never changes after creation.

**Why:** This is the only approach that guarantees historical submissions render correctly in the CRM and in PDFs without data migration. Soft-delete or in-place edit both corrupt the audit trail.

**Invariant:** `Submission.template_id` is set at `status=created` and is immutable thereafter. Django's `save()` override must raise `ValidationError` if code tries to change it on an existing submission.

```python
# apps/industries/models.py
class QuestionnaireTemplate(models.Model):
    industry = models.ForeignKey(Industry, on_delete=models.PROTECT)
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("industry", "version")
        indexes = [models.Index(fields=["industry", "is_active"])]

    @classmethod
    def activate_new_version(cls, industry_id: int, questions_data: list) -> "QuestionnaireTemplate":
        """Create new version, deactivate old. Atomic."""
        with transaction.atomic():
            current = cls.objects.filter(industry_id=industry_id, is_active=True).first()
            new_version = (current.version + 1) if current else 1
            new_tmpl = cls.objects.create(industry_id=industry_id, version=new_version, is_active=True)
            if current:
                current.is_active = False
                current.save(update_fields=["is_active"])
            # create Question rows linked to new_tmpl
            return new_tmpl
```

### Pattern 4: Webhook Idempotency via DB Unique Constraint

**What:** The `Payment` model has a `unique=True` field `transaction_id` (CloudPayments `TransactionId`). The webhook endpoint does `Payment.objects.get_or_create(transaction_id=tx_id, defaults={...})`. If `created=False`, the payment already exists — return `{"code": 0}` immediately without side effects.

**Why not Redis dedup:** Redis TTL can expire before a retry arrives. Database unique constraint is durable and permanent.

**HMAC verification:** Must happen before any database read, in a dedicated DRF permission class or middleware. Reject non-matching requests with HTTP 400 (never 200) to prevent CloudPayments from thinking the webhook was delivered.

```python
# apps/payments/views.py
import base64, hashlib, hmac
from rest_framework.views import APIView
from rest_framework.response import Response

class CloudPaymentsWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    def _verify_hmac(self, request) -> bool:
        secret = settings.CLOUDPAYMENTS_API_SECRET.encode()
        body = request.body
        expected = base64.b64encode(
            hmac.new(secret, body, hashlib.sha256).digest()
        ).decode()
        received = request.headers.get("Content-Hmac", "")
        return hmac.compare_digest(expected, received)

    def post(self, request):
        if not self._verify_hmac(request):
            return Response({"code": 13}, status=400)   # CP: invalid HMAC

        data = request.data
        tx_id = str(data["TransactionId"])
        payment, created = Payment.objects.get_or_create(
            transaction_id=tx_id,
            defaults={
                "amount": data["Amount"],
                "status": "succeeded",
                "submission_id": data.get("InvoiceId"),
            },
        )
        if created:
            transaction_confirmed.delay(payment.id)   # Celery task
        return Response({"code": 0})
```

### Pattern 5: Deep-Link Token for Bot → Site → Bot Handoff

**What:** After the bot completes onboarding, it generates a short-lived token (UUID stored in Redis with 30-minute TTL) tied to the user's `telegram_id`. The deep link is `https://baqsy.kz/tariffs?ref=<token>`. The React page reads the token, calls `POST /api/auth/tg-token/` to exchange it for a JWT access token + `telegram_id`, and proceeds to the payment widget. After payment success, the React page redirects to `tg://resolve?domain=BaqsyBot&start=paid_<submission_id>` to return the user to the bot.

**Why not JWT directly in the deep link:** Telegram's `start` parameter is limited to 64 characters — too short for a proper JWT. A UUID token is 36 chars (fits) and is server-side revocable.

**Why not session cookie:** Bot users may open the link on a different device. Token exchange (UUID → JWT) is device-agnostic.

```python
# apps/accounts/views.py
class TelegramTokenExchangeView(APIView):
    def post(self, request):
        token = request.data.get("token")
        telegram_id = cache.get(f"tg_deep_link:{token}")   # Redis cache
        if not telegram_id:
            return Response({"error": "expired"}, status=400)
        cache.delete(f"tg_deep_link:{token}")
        profile = ClientProfile.objects.get(telegram_id=telegram_id)
        refresh = RefreshToken.for_user(profile.user)
        return Response({"access": str(refresh.access_token)})
```

## Data Flow

### Critical Path A: Onboarding + Questionnaire

```
User: /start in Telegram
    │
    ▼
[bot] OnboardingStates.name → collect 5 answers
    │
    ▼
[bot] POST /api/clients/  →  [Django] create ClientProfile + Submission(status=created)
    │  returns: {submission_id, deep_link_token}
    ▼
[bot] sends: "Выберите тариф: https://baqsy.kz/tariffs?ref=<token>"
    │
    ▼ (user opens browser)
[React] GET /api/auth/tg-token/  →  exchange token → JWT
[React] shows tariff cards + CloudPayments widget (publicId from /api/tariffs/)
    │
    ▼
[CloudPayments widget] charge → success callback
[React] POST /api/payments/create-intent/  →  [Django] Payment(status=pending)
    │
    ▼ (CP sends webhook to Django)
[Django] POST /api/payments/cloudpayments/webhook/
    → verify HMAC
    → Payment.get_or_create(transaction_id=...)
    → Submission.status = paid
    → Celery: notify_bot_payment_success.delay(submission_id)
    │
    ▼
[Celery worker] calls Telegram Bot API directly:
    POST https://api.telegram.org/bot<TOKEN>/sendMessage
    {chat_id: telegram_id, text: "Оплата получена! Начинаем анкету..."}
    (Note: outbound HTTP call, not via aiogram process — simpler, no IPC needed)
    │
    ▼
[bot] receives /start paid_<submission_id>  (React redirected user back)
  OR [bot] user simply continues — bot polls Submission status on next interaction
    │
    ▼
[bot] QuestionnaireStates — loads questions from /api/submissions/<id>/questions/
    loop: ask question → user answers → POST /api/submissions/<id>/answers/
    (each answer saved immediately — crash-safe)
    │
    ▼
Last answer saved → [Django] Submission.status = completed
    → Celery: notify_admin_new_submission.delay(submission_id)
    │
    ▼
[bot/React] "Спасибо! Ожидайте результат"
```

### Critical Path B: Payment Webhook (Idempotency Detail)

```
CloudPayments sends POST /api/payments/cloudpayments/webhook/
    │
    ├─ Step 1: HMAC check (Content-Hmac header vs HMAC-SHA256(body, API_SECRET))
    │          FAIL → return {code: 13}, HTTP 400
    │
    ├─ Step 2: Parse TransactionId from body
    │
    ├─ Step 3: Payment.objects.get_or_create(transaction_id=tx_id)
    │          ALREADY EXISTS (created=False)
    │          └─ return {code: 0} immediately — no side effects
    │
    ├─ Step 4 (first delivery only):
    │   a. Payment.status = succeeded
    │   b. Submission.status = paid  (atomic with payment update)
    │   c. Celery task enqueued: notify_bot_payment_success.delay()
    │
    └─ return {code: 0}   ← CP considers webhook delivered

CloudPayments retries up to 100 times if it doesn't get {code:0} — idempotency is critical.
```

### Critical Path C: Admin Confirms → PDF → Delivery

```
[Admin in Django CRM] opens Submission card
    → reads client answers
    → types audit text into AuditReport.content field
    → clicks "Подтвердить и отправить"
    │
    ▼
[Django Admin action] Submission.status = under_audit
    → AuditReport.save()
    → Celery: generate_and_deliver_report.delay(submission_id)
    │
    ▼
[Celery worker: generate_and_deliver_report]
    Step 1: Load Submission + AuditReport + ClientProfile + Template version
    Step 2: Render Jinja2 HTML template (tariff-specific: ashide1 or ashide2 layout)
    Step 3: WeasyPrint HTML → PDF bytes
    Step 4: boto3 PUT to MinIO → returns s3_key
    Step 5: AuditReport.pdf_url = presigned URL or permanent path
    Step 6: Chain delivery tasks:
      ├─ deliver_telegram.delay(submission_id)
      └─ deliver_whatsapp.delay(submission_id)
    │
    ▼
[deliver_telegram]
    POST https://api.telegram.org/bot<TOKEN>/sendDocument
    {chat_id: telegram_id, document: <MinIO presigned URL or file bytes>}
    DeliveryLog(channel=tg, status=sent)
    Submission.status = delivered (if both channels succeed)
    │
    ▼
[deliver_whatsapp]
    POST https://api.wazzup24.com/v3/message
    {channelId: ..., chatId: client_phone, type: "file", fileUrl: <MinIO presigned URL>}
    DeliveryLog(channel=wa, status=sent)
```

## Suggested Build Order

Dependencies flow from bottom to top. Each phase can only begin when items below it are complete.

```
Phase 1 — Infrastructure & Data Model
  ├─ Docker Compose (web, db, redis, worker, nginx, minio, bot)
  ├─ Django project skeleton + settings (base/dev/prod)
  ├─ All Django models + migrations (accounts, industries, submissions, payments, reports, delivery)
  └─ Django Admin basic registration
  GATE: All models migrate cleanly; admin shows all entities.

Phase 2 — Core API
  ├─ ClientProfile create/read endpoints
  ├─ QuestionnaireTemplate + Question endpoints (with version logic)
  ├─ Submission CRUD + Answer save endpoint
  └─ Tariff read endpoint
  GATE: Postman/pytest can walk the full submission lifecycle without bot.

Phase 3 — Bot (depends on Phase 2)
  ├─ aiogram skeleton + RedisStorage setup
  ├─ /start + OnboardingStates FSM
  ├─ Deep-link token generation + token exchange endpoint
  └─ QuestionnaireStates FSM (loads questions from API, saves answers)
  GATE: Bot can onboard user and complete all questionnaire answers, stored in DB.

Phase 4 — Payments (depends on Phase 2)
  ├─ CloudPayments widget integration in React (tariffs page)
  ├─ Webhook endpoint with HMAC + idempotency
  ├─ Celery task: notify bot after payment
  └─ Submission status transitions: created → paid → in_progress
  GATE: Test payment flows through; duplicate webhook replays safely.

Phase 5 — React SPA (depends on Phases 2 + 4)
  ├─ Landing page (static content from CMS fields)
  ├─ Tariffs page + CP widget
  ├─ Client cabinet (JWT auth, order status, PDF link)
  └─ Upsell flow (upgrade tariff without re-answering)
  GATE: Full user journey: land → select tariff → pay → see status in cabinet.

Phase 6 — PDF Generation + Delivery (depends on Phases 1 + 4)
  ├─ WeasyPrint + Jinja2 PDF templates (ashide1, ashide2)
  ├─ MinIO upload via boto3/django-storages
  ├─ Celery generate_and_deliver_report task chain
  ├─ Telegram document delivery (direct Bot API call)
  └─ Wazzup24 WhatsApp delivery
  GATE: Admin confirms → PDF appears in MinIO → user receives file in TG and WA.

Phase 7 — CRM Admin Enhancement (depends on Phase 6)
  ├─ Custom Django Admin: submission queue, filters, order card
  ├─ AuditReport inline with "Confirm & Send" action
  ├─ Dashboard stats (by industry, tariff, revenue)
  └─ Template management (create/edit questionnaire triggers new version)
  GATE: Admin can manage full lifecycle without touching code.

Phase 8 — Hardening
  ├─ Celery task retries with exponential backoff
  ├─ structlog JSON logging
  ├─ PG backup cron to MinIO via Celery beat
  ├─ nginx TLS (certbot/Let's Encrypt)
  ├─ GitHub Actions CI (pytest + docker build)
  └─ README deployment runbook (≤2hr target)
  GATE: Deployment on fresh VPS in under 2 hours; pytest suite passes.
```

## Key Invariants

### 1. Submission State Machine (transitions only forward)

```
created → paid → in_progress → completed → under_audit → delivered
```

- `created`: set when bot calls POST /api/submissions/
- `paid`: set atomically with Payment.status=succeeded inside webhook handler (DB transaction)
- `in_progress`: set when first Answer is saved (or when bot receives payment notification)
- `completed`: set when all required Questions have Answers (counted server-side)
- `under_audit`: set when Admin saves AuditReport
- `delivered`: set when both delivery channels report success

**Invariant:** State never moves backward. Django model's `save()` override enforces allowed transitions.

### 2. Template Version Lock on Submission

`Submission.template` FK is assigned at `status=created` and is write-protected thereafter. Any attempt to change it raises `ValidationError`. This guarantees that the questionnaire a client answered is exactly the questionnaire shown in the CRM and used for PDF rendering — regardless of later template edits.

### 3. Webhook Idempotency

CloudPayments delivers webhooks with retries up to 100 times. The system must return `{"code": 0}` for any repeat delivery. The `unique=True` DB constraint on `Payment.transaction_id` (backed by PostgreSQL unique index) is the single source of idempotency truth. `get_or_create` makes the check-and-insert atomic under concurrent deliveries.

### 4. HMAC Verification Before Any Business Logic

CloudPayments provides `Content-Hmac` header: `base64(HMAC-SHA256(body, api_secret))`. The webhook view verifies this before reading `request.data`. Failed HMAC returns HTTP 400 with `{"code": 13}` — CP will not retry on 400.

### 5. Answer Persistence Per-Question (Crash Safety)

The bot saves `Answer` to the API after each user response, not at end of questionnaire. If the user's Telegram session drops mid-questionnaire, all completed answers survive. The bot reconstructs position by calling `GET /api/submissions/<id>/progress/` which returns answered vs unanswered question IDs.

### 6. Celery → Telegram Delivery (Direct HTTP, Not Bot Process)

Celery workers send Telegram messages by calling the Telegram Bot API directly via `httpx` (synchronous) or `requests`. They do NOT communicate with the aiogram bot process. The aiogram process is stateless from Django's perspective — it only reads incoming messages. Outbound notifications originate from Celery. This eliminates IPC complexity between bot and worker containers.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| CloudPayments | JS Widget (frontend) + HMAC webhook (backend) | `publicId` in React env; `apiSecret` in Django env. Never expose apiSecret to frontend. |
| Telegram Bot API | aiogram 3 (polling dev / webhook prod) + direct httpx for outbound from Celery | Single `BOT_TOKEN`. In prod, set webhook URL to `https://domain.tld/tg-webhook/`. |
| Wazzup24 | REST POST `/v3/message` with Bearer token | Phone number normalization required (KZ format: +7...). File delivery uses `fileUrl` (presigned MinIO URL). |
| MinIO | boto3 + django-storages S3 backend | `AWS_S3_ENDPOINT_URL=http://minio:9000`. Presigned URLs for client downloads (expire in 24h). |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| bot ↔ Django | REST (httpx async) | Bot uses `X-Bot-Secret` header auth. Django has a dedicated permission class for bot-only endpoints. |
| Celery ↔ Django ORM | Direct import (same Python package) | Workers run `django.setup()` via `celery.py`. No REST needed. |
| Celery ↔ Telegram | Direct HTTPS (requests/httpx) | Workers call `api.telegram.org` directly — no aiogram process involved. |
| Celery ↔ MinIO | boto3 | S3-compatible PUT; presigned GET URLs passed to delivery endpoints. |
| React ↔ Django | REST + JWT | SimpleJWT access tokens (15min) + refresh tokens (7 days) in httpOnly cookies. |
| Django Admin ↔ Django | Django internal (same process) | Admin views call service layer functions, not REST. |

## Deployment Topology

### Dev (docker-compose.yml)

```yaml
services:
  web:      # Django gunicorn, port 8000 exposed
  bot:      # aiogram long-polling
  worker:   # Celery worker (concurrency=4)
  beat:     # Celery beat
  db:       # PostgreSQL 16
  redis:    # Redis 7 (db=0 Celery, db=1 FSM)
  minio:    # MinIO latest
  nginx:    # port 80 only (no TLS in dev)
  frontend: # Vite dev server, port 5173 exposed direct (HMR)
```

Dev-specific:
- Bot uses `long-polling` (no public URL needed)
- `DEBUG=True`, no TLS
- Frontend connects to API at `http://localhost:8000/api/`
- MinIO console at `:9001`

### Prod (docker-compose.prod.yml overlay)

```yaml
services:
  web:
    command: gunicorn baqsy.wsgi:application --workers 4 --bind 0.0.0.0:8000
    restart: unless-stopped
  bot:
    command: python main.py --mode webhook   # registers webhook URL with Telegram
    restart: unless-stopped
  worker:
    command: celery -A baqsy worker -c 4 -Q default,pdf,delivery
    restart: unless-stopped
  beat:
    restart: unless-stopped
  nginx:
    volumes:
      - ./ssl:/etc/nginx/ssl:ro   # Let's Encrypt certs
    ports: ["80:80", "443:443"]
  # No frontend container in prod — Vite build artifacts served by nginx as static files
```

Prod-specific:
- React SPA is built (`npm run build`) and served by nginx from `/app/dist/`
- Bot uses webhook mode (`/tg-webhook/` endpoint behind nginx → Django)
- TLS via Let's Encrypt certbot container or pre-provisioned certs
- MinIO behind nginx, not publicly exposed (presigned URLs only)
- Separate `.env.prod` file, never committed

### Environment Variables Split

| Variable | Used by | Secret? |
|----------|---------|---------|
| `DATABASE_URL` | Django, Celery | Yes |
| `REDIS_URL` | Django (Celery broker), bot (FSM) | No |
| `BOT_TOKEN` | bot, Celery (direct API calls) | Yes |
| `BOT_API_SECRET` | bot → Django auth header; Django verification | Yes |
| `CLOUDPAYMENTS_PUBLIC_ID` | React (widget) | No (public) |
| `CLOUDPAYMENTS_API_SECRET` | Django webhook HMAC | Yes |
| `WAZZUP_API_KEY` | Celery worker | Yes |
| `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` | MinIO, boto3 | Yes |
| `DJANGO_SECRET_KEY` | Django | Yes |

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0–500 users | Single VPS (2 vCPU, 4GB RAM). All services in one Docker Compose. No changes needed. |
| 500–5,000 users | Add read replica for PG (analytics queries). Increase Celery concurrency. Consider separate queues: `pdf`, `delivery`, `default`. |
| 5,000+ users | Separate bot into its own VPS. Replace single Celery worker with auto-scaled worker pool. Move MinIO to managed object storage (e.g., Yandex Object Storage KZ). |

First bottleneck: WeasyPrint is CPU-intensive. At high load, PDF generation will queue behind each other. Mitigation: dedicated `pdf` queue with its own worker pool, separate from `delivery` tasks.

Second bottleneck: CloudPayments webhook throughput. The Django webhook endpoint is synchronous (by design — idempotency DB check requires a transaction). At extreme concurrency, PG connection pool becomes the limit. Mitigation: PgBouncer or `max_connections` tuning.

## Anti-Patterns

### Anti-Pattern 1: Business Logic in the Bot

**What people do:** Put `Submission.save()` or `Payment.create()` calls directly in aiogram handlers by importing Django models into `bot/`.

**Why it's wrong:** Requires `django.setup()` in bot process, creates tight coupling to ORM schema, duplicates validation logic, and makes it impossible to test bot handlers without a live DB.

**Do this instead:** Bot calls REST API. All model mutations happen inside Django views/services. Bot only handles dialogue state.

### Anti-Pattern 2: Mutable Questionnaire Templates

**What people do:** Edit `Question.text` or reorder questions in place to fix a typo. Old `Submission` records now show the new text when rendered in the CRM or PDF.

**Why it's wrong:** The audit report was generated from different questions than what's now shown. Legal/quality risk.

**Do this instead:** Always call `QuestionnaireTemplate.activate_new_version()`. Old submissions retain FK to old version. New submissions get the new version.

### Anti-Pattern 3: Firing Celery Tasks Without Idempotency Guards

**What people do:** In the webhook handler: `if payment.status == 'succeeded': send_delivery_task.delay(id)`. On retry, this fires the delivery task again.

**Why it's wrong:** User receives the PDF twice in Telegram and WhatsApp. Or, worse, the PDF is re-generated and overwritten in MinIO mid-delivery.

**Do this instead:** Inside each Celery task, check `AuditReport.delivered_at` or `DeliveryLog` status before acting. Use Celery's `task_acks_late=True` + `acks_on_failure_or_timeout=False` for at-least-once delivery with guarded re-entry.

### Anti-Pattern 4: Storing Bot Token in Frontend Environment

**What people do:** Put `VITE_BOT_TOKEN=...` in the React .env to construct deep links client-side.

**Why it's wrong:** Bot Token is exposed in the browser, enabling anyone to impersonate the bot or read all bot updates.

**Do this instead:** Django generates the deep link URL (including the UUID token) and returns it via API. The React page only displays it. The Bot Token never leaves the server.

### Anti-Pattern 5: Synchronous WeasyPrint in Django View

**What people do:** Call `weasyprint.HTML(string=html).write_pdf()` directly inside a DRF view as part of the admin confirm action.

**Why it's wrong:** WeasyPrint renders in ~2–5 seconds for complex templates. This blocks the gunicorn worker thread, exhausts the thread pool under concurrent admin actions, and risks timeout errors.

**Do this instead:** The admin action enqueues `generate_and_deliver_report.delay(submission_id)` and returns immediately. Celery worker does the heavy lifting. Admin sees async feedback via submission status refresh.

## Sources

- aiogram 3 official docs — FSM storages and RedisStorage: https://docs.aiogram.dev/en/latest/dispatcher/finite_state_machine/storages.html
- aiogram-django-template reference architecture: https://github.com/MaksimZayats/aiogram-django-template
- CloudPayments developer docs — webhook HMAC (Content-Hmac, HMAC-SHA256 base64): https://developers.cloudpayments.ru/en/
- Celery docs — idempotent tasks and acks_late: https://docs.celeryq.dev/en/stable/userguide/tasks.html
- Vinta Software — Celery idempotency patterns: https://www.vintasoftware.com/blog/celery-wild-tips-and-tricks-run-async-tasks-real-world
- Wazzup24 API docs — sending messages/files: https://wazzup24.com/help/api-en/sending-messages/
- Hookdeck — webhook idempotency implementation guide: https://hookdeck.com/webhooks/guides/implement-webhook-idempotency
- django-weasyprint package (Celery integration): https://github.com/fdemmer/django-weasyprint
- Webhook HMAC verification patterns (Python): https://www.bindbee.dev/blog/how-hmac-secures-your-webhooks-a-comprehensive-guide

---
*Architecture research for: Baqsy System — Django + aiogram 3 + React + Celery + CloudPayments + WhatsApp*
*Researched: 2026-04-15*
