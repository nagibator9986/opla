# Pitfalls Research

**Domain:** Telegram bot + Django + payments + PDF + WhatsApp SaaS (Baqsy System)
**Researched:** 2026-04-15
**Confidence:** HIGH (critical pitfalls verified against official docs and confirmed GitHub issues)

---

## Critical Pitfalls

### Pitfall 1: CloudPayments Webhook Duplicate Processing Without DB-Level Lock

**What goes wrong:**
CloudPayments retries webhook delivery up to 100 times if your server returns a non-200 or fails to respond. If two retries arrive within milliseconds of each other, a naive `if not Payment.objects.filter(transaction_id=X).exists(): create()` check runs in both requests simultaneously — both pass the check, and you create two Payment records. The order goes `paid` twice, the questionnaire might trigger twice, and the client gets invoiced twice in your records.

**Why it happens:**
Developers check for duplicates at the application level before writing to the DB. Without a DB-level unique constraint AND `select_for_update`, two concurrent requests can both pass the "does it exist?" check before either has written.

**How to avoid:**
1. Add `unique=True` on `Payment.transaction_id` — this is the single most important safeguard.
2. Use `Payment.objects.get_or_create(transaction_id=..., defaults={...})` wrapped in `transaction.atomic()` — the DB unique constraint makes the second concurrent call raise `IntegrityError`, which you catch and return 200.
3. For the state machine transition (`Submission.status = paid`), wrap in `select_for_update()`:
   ```python
   with transaction.atomic():
       sub = Submission.objects.select_for_update().get(pk=submission_id)
       if sub.status != 'created':
           return  # already processed
       sub.status = 'paid'
       sub.save()
   ```
4. Always validate `Content-HMAC` header **before** touching the DB. Use `hmac.compare_digest()`, never `==`.

**Warning signs:**
- Duplicate `Payment` rows in DB with same `TransactionId`
- `Submission` stuck in `paid` status after already reaching `in_progress`
- Celery tasks for questionnaire start firing twice per payment event

**Phase to address:** Phase: Payments & Webhook Integration

---

### Pitfall 2: FSM State Eviction — User Loses Mid-Questionnaire Progress

**What goes wrong:**
aiogram 3 FSM with `RedisStorage` uses Redis keys with a default TTL. If Redis runs out of memory and evicts keys (default eviction policy is often `allkeys-lru`), or if you flush Redis during a deployment, users who are mid-questionnaire lose their state entirely. They can re-send any message and get confused bot responses (no active state handler matches), potentially sending answers to a now-dead state.

**Why it happens:**
Redis is configured as both the Celery broker and FSM storage. Under memory pressure, Redis can evict FSM keys. Additionally, deployments that restart the Redis container without persistence wipe all state.

**How to avoid:**
1. Configure Redis with `maxmemory-policy noeviction` (not LRU) for the FSM database, OR use a dedicated Redis DB index (e.g., DB 0 for Celery, DB 1 for FSM) with separate memory limits.
2. Enable Redis persistence: `appendonly yes` + AOF in the Docker Compose Redis service. This survives restarts.
3. Set explicit FSM TTLs in `RedisStorage(state_ttl=timedelta(days=7), data_ttl=timedelta(days=7))` so stale states expire gracefully rather than being randomly evicted.
4. Store questionnaire progress in Django DB (`Answer` records) after **every single response** — the FSM state only needs to track "which question index we're on". If state is lost, the bot can re-derive current position from the DB.
5. Add a `/status` command that shows the user where they are and offers to resume.

**Warning signs:**
- Users reporting "the bot stopped responding" mid-questionnaire
- Redis `MEMORY DOCTOR` reporting fragmentation or near-limit
- Bot logs showing `StateNotFound` or handlers falling through to unhandled states

**Phase to address:** Phase: Bot FSM + Questionnaire Flow

---

### Pitfall 3: QuestionnaireTemplate Versioning Breaks Historical Submissions

**What goes wrong:**
Admin edits an existing `QuestionnaireTemplate` in-place (changes question text, reorders questions, deletes a question). All historical `Submission` records that reference this template now show wrong questions next to their answers. The CRM audit card becomes unreadable — answer 7 appears under question 8's text.

**Why it happens:**
The simplest implementation is to have `Question.template` as a FK, and admins just edit questions. The relationship between a historical Answer and the question it answered is broken the moment the question is modified.

**How to avoid:**
1. **Never mutate live templates.** Enforce this at the model level: when an admin saves changes to a template, always create a new `QuestionnaireTemplate` with `version = old.version + 1`, clone all `Question` objects to the new template, apply edits, then set `new.is_active = True` and `old.is_active = False`.
2. `Submission.template_version` FK points to a specific `QuestionnaireTemplate` instance — never just to Industry.
3. `Answer.question` FK points to a specific `Question` instance (not question type/name). Questions must never be deleted, only soft-deleted in new template versions.
4. In the CRM admin, render the audit card by joining `Answer → Question` (using the Answer's FK, not the currently active template).
5. Write a migration validator that enforces: if `QuestionnaireTemplate` has any `Submission` with `status != 'created'`, it is frozen — it cannot be edited in-place.

**Warning signs:**
- Admin edits a question text and realizes historical CRM cards now show wrong question labels
- Answer count on old submissions doesn't match the current active template's question count
- Reports generated for old orders contain wrong question–answer pairs

**Phase to address:** Phase: Industries & Questionnaire Templates (before any real orders exist)

---

### Pitfall 4: WeasyPrint Cyrillic Rendering Fails in Docker (Missing Fonts)

**What goes wrong:**
Locally WeasyPrint renders Cyrillic text perfectly. In Docker, the PDF is generated but Cyrillic characters appear as empty boxes or are replaced by `.notdef` glyphs. The client receives a beautifully styled PDF that is completely unreadable.

**Why it happens:**
WeasyPrint uses the system's Fontconfig to find fonts. A minimal Docker image (e.g., `python:3.12-slim`) does not include any fonts with Cyrillic coverage. The CSS `font-family` specification may resolve to a fallback that has no Cyrillic glyphs. WeasyPrint logs warnings about missing glyphs but still generates the file.

**How to avoid:**
1. In the Dockerfile for the `worker` service, explicitly install fonts with full Cyrillic coverage:
   ```dockerfile
   RUN apt-get install -y fonts-liberation fonts-dejavu fonts-freefont-ttf \
       libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b
   ```
2. Alternatively (recommended for branded PDFs), bundle the exact brand fonts in `backend/static/fonts/` and reference them via absolute path in CSS `@font-face`. This guarantees pixel-identical rendering regardless of the server environment.
3. Add a smoke test to the CI pipeline that renders a PDF with a known Cyrillic string and asserts the output byte-size is above a threshold (an empty-glyph PDF is significantly smaller).
4. Pin WeasyPrint to a specific version in `requirements.txt`. WeasyPrint has had multiple font-handling regressions across minor versions (v57, v62).

**Warning signs:**
- PDF file generated in CI but visually unreadable (check with `pdftotext` in CI)
- WeasyPrint logs: "No glyph for character U+0410 in font X"
- PDF byte size is unexpectedly small (font subsetting produced a near-empty subset)

**Phase to address:** Phase: PDF Generation & Delivery

---

### Pitfall 5: WeasyPrint Memory Growth Kills the Celery Worker

**What goes wrong:**
Each call to `weasyprint.HTML(...).write_pdf()` increases the worker process RSS by 20–40 MB. The memory is not released back to the OS (known WeasyPrint/Python memory leak, multiple open GitHub issues since v53). After generating 10–15 PDFs, a worker with 512 MB Docker memory limit is OOM-killed. The PDF task is re-queued but the worker is dead — no one processes it.

**Why it happens:**
WeasyPrint holds the entire rendered document layout tree in Python memory until the write is complete. Combined with Python's allocator not returning memory to the OS promptly, RSS accumulates per generation.

**How to avoid:**
1. Run PDF generation in a **dedicated Celery queue** (`queue='pdf'`) with a single dedicated worker (`--concurrency=1`).
2. Configure the Celery worker with `--max-tasks-per-child=5` — after 5 PDF generations, the worker process restarts, flushing accumulated memory.
3. Set a generous Docker memory limit on the `worker` service (at least 1 GB) and monitor RSS with Prometheus/Grafana or simple cron health checks.
4. Test PDF generation memory profile in CI using a Python memory profiler before going to production.

**Warning signs:**
- Worker container exits with code 137 (OOM kill)
- Celery task appears in `PENDING` state indefinitely after worker restart
- PDF tasks taking progressively longer over time before failure

**Phase to address:** Phase: PDF Generation & Delivery

---

### Pitfall 6: Wazzup24 WhatsApp Delivery Is Fire-and-Forget Without Delivery Confirmation

**What goes wrong:**
The code calls the Wazzup24 API to send a PDF, receives a 200 OK from Wazzup's API, marks delivery as `sent`, and moves on. The message is actually never delivered to the client — the WhatsApp number was invalid, the client had not accepted the WhatsApp Terms recently, or Wazzup's outbound queue was overloaded. The admin assumes delivery succeeded; the client never receives their paid report.

**Why it happens:**
Wazzup24 (and most WhatsApp Business API gateways) use an asynchronous two-stage delivery: your API call queues the message on their side; actual delivery to WhatsApp happens later, with status delivered separately via webhook or polling.

**How to avoid:**
1. Distinguish between `queued` (Wazzup API accepted) and `delivered` (WhatsApp confirmed) in the `DeliveryLog` model. Never mark the Submission as fully `delivered` until WhatsApp confirms.
2. Implement a Wazzup24 incoming webhook endpoint that updates `DeliveryLog.status` when Wazzup reports delivery/read/failure.
3. Add a Celery Beat task that runs every 30 minutes querying for `DeliveryLog` records stuck in `queued` for more than 1 hour — alert the admin to manually verify.
4. Always send the Telegram delivery first (more reliable), mark `Submission.status = delivered` only after TG success. Treat WhatsApp as a secondary channel — log failures but don't block the primary flow.
5. PDF files must be under 51 MB (Wazzup24 limit via API). WeasyPrint PDFs should be well under this, but validate during generation.

**Warning signs:**
- `DeliveryLog` rows showing `status=sent` but no delivery confirmation after hours
- Client contacts admin complaining they didn't receive the PDF
- Wazzup24 dashboard shows message in "pending" or "failed" status

**Phase to address:** Phase: PDF Generation & Delivery

---

### Pitfall 7: Deep Link Token Replay — Different User Claims Another's Order

**What goes wrong:**
The bot generates a deep-link URL like `https://baqsy.kz/pay?token=<uuid>` and sends it to the client. This URL opens the tariff page with the client's `telegram_id` pre-filled. If the token has no expiry and no binding to a session, the client can share the link and someone else can complete payment under the original client's identity. More practically: if the client re-opens the link after already paying, the system creates a second `Submission`.

**Why it happens:**
Deep-link tokens are often generated as simple UUIDs stored in the DB, but without expiry, single-use enforcement, or binding to a specific browser session.

**How to avoid:**
1. Token must be single-use: after the payment page loads and the `Submission` is created, invalidate the token (`used=True` in DB).
2. Token must expire: set TTL of 24–48 hours. A Celery Beat job purges expired tokens.
3. Before creating a new `Submission`, check if the client already has an active `Submission` in status `created` or `paid` — if so, redirect to existing one, do not create a duplicate.
4. Bind the token to the `telegram_id` that generated it. On the payment page, validate that the token's `telegram_id` matches the session context (or, since the client is not authenticated on the web, at minimum log discrepancies and require re-confirmation).
5. The upsell flow (Ashide 1 → Ashide 2) needs special protection: validate that the `Submission` being upgraded is owned by the currently identified client before accepting an upsell payment.

**Warning signs:**
- Multiple `Submission` records for the same `telegram_id` in `created` status
- Payment received but no matching `telegram_id` can be resolved
- Token in URL matches a `Submission` that already has `status=paid`

**Phase to address:** Phase: Web Platform + Payment Integration

---

### Pitfall 8: Celery Visibility Timeout Causes PDF Task Duplication

**What goes wrong:**
PDF generation is slow (5–30 seconds). The default Celery + Redis `visibility_timeout` is 3600 seconds (1 hour), which sounds safe — but if `acks_late=True` is set (recommended for reliability), and the worker crashes mid-task, the task is re-queued after the visibility timeout. However, if you also use `retry()` inside the task, Celery with Redis broker can create exponential task duplication: the original task is still in the Redis unacked set AND a new retry task is enqueued. After the visibility timeout, both execute.

**Why it happens:**
The interaction between `acks_late`, `retry()`, and Redis visibility timeout is a well-documented Celery bug/gotcha. Unlike RabbitMQ, Redis does not support proper per-task acknowledgment semantics.

**How to avoid:**
1. Set `visibility_timeout` in `CELERY_BROKER_TRANSPORT_OPTIONS` to a value significantly larger than your longest task (e.g., `3600 * 4 = 14400` for tasks that could take up to 30 minutes worst-case).
2. For PDF generation tasks: make the task idempotent by checking if `AuditReport.pdf_url` is already set before starting generation. If set, return immediately.
3. Use `bind=True` + `self.request.id` as a unique lock key in Redis (e.g., `SET task_lock:{task_id} 1 EX 300 NX`) before starting heavy work.
4. Prefer `acks_late=False` (default) for tasks where you cannot guarantee idempotency, and instead focus on making the task's side effects idempotent.
5. Monitor Celery with Flower or a simple custom health endpoint that counts tasks in each state.

**Warning signs:**
- Client receives two PDF emails/messages
- `AuditReport` has two PDF files in MinIO for the same `Submission`
- Celery logs show the same task ID starting twice

**Phase to address:** Phase: PDF Generation & Delivery (Celery infrastructure)

---

### Pitfall 9: Django Migration Race During Docker Compose Deployment

**What goes wrong:**
`docker-compose up` starts both the `web` (gunicorn) and `worker` (Celery) containers simultaneously. The `web` container runs `manage.py migrate` in its entrypoint. The `worker` container also starts and tries to use the DB before migrations complete. In the worst case, both containers run `migrate` concurrently, causing the `django_migrations` lock table to deadlock or apply migrations out of order.

**Why it happens:**
Docker Compose `depends_on` only waits for container start, not for service readiness. Without proper coordination, two processes running `migrate` simultaneously will conflict.

**How to avoid:**
1. Only one service should run migrations: the `web` service entrypoint. All other services (`worker`, `beat`, `bot`) must use `depends_on: web: condition: service_healthy` with a proper health check on the `web` container that returns healthy only after migrations complete.
2. Or use a dedicated `migrate` one-shot service that other services depend on.
3. The `web` entrypoint pattern:
   ```bash
   python manage.py migrate --noinput
   python manage.py collectstatic --noinput
   exec gunicorn baqsy.wsgi:application
   ```
4. For zero-downtime future deployments: never add `NOT NULL` columns without a default in a single migration. Split into: add nullable column → deploy → backfill → add constraint.

**Warning signs:**
- Container startup fails with `django.db.utils.OperationalError: table already exists`
- `django_migrations` lock errors in logs
- Workers processing tasks against an un-migrated schema

**Phase to address:** Phase: Infrastructure & Docker Setup (first phase)

---

### Pitfall 10: Admin CRM Lost Update — Two Admins Submit Audit Simultaneously

**What goes wrong:**
Admin A opens the audit card for Submission #42 at 10:00. Admin B also opens the same card at 10:01. Admin A completes the audit text and clicks "Confirm & Send" at 10:05. Admin B, unaware, finishes their version and clicks "Confirm & Send" at 10:06. Admin B's save silently overwrites Admin A's audit. The PDF generated is Admin B's version, but Admin A believes their version was sent.

**Why it happens:**
Django's admin (and most custom form-based CRM views) does a blind `instance.save()` without checking if the record was modified since it was loaded. This is the classic "lost update" problem.

**How to avoid:**
1. Add an `updated_at` timestamp to `AuditReport`. When saving, compare the `updated_at` from the form (a hidden field) against the current DB value. If they differ, reject the save with "This record was modified since you opened it — please refresh."
2. Add an `audited_by` field: when Admin A opens the card, set a soft-lock (`locked_by`, `locked_at`). Admin B sees a "Currently being edited by Admin A" warning. Locks expire after 30 minutes (in case Admin A closes the browser).
3. The "Confirm & Send" action should use `select_for_update()` within a transaction to prevent two concurrent submits.
4. Since this is an MVP with likely one active admin, this is a moderate-priority pitfall. However, the `updated_at` check is trivially cheap insurance and should be in Phase 1 of CRM development.

**Warning signs:**
- Two admins both report "confirming" the same order
- `DeliveryLog` shows two send events for the same `Submission`
- Audit text doesn't match what the admin remembers writing

**Phase to address:** Phase: CRM Admin Dashboard

---

### Pitfall 11: Bot Sends PDF via Telegram Before File Is Fully Uploaded to MinIO

**What goes wrong:**
The Celery task generates the PDF, uploads to MinIO, then immediately triggers the bot to send the file. The bot tries to send `bot.send_document(file=minio_url)` but the URL is not yet publicly accessible (MinIO replication lag, or the presigned URL is generated before the upload fully flushes). The Telegram API call fails, the task retries, but by then the URL is valid — except now the retry generates a second PDF (if not idempotent) or sends the same file twice.

**Why it happens:**
Object storage uploads are eventually consistent in some configurations. Presigned URLs can be generated before the object exists. The upload confirmation from MinIO client doesn't guarantee immediate read-after-write in all configurations.

**How to avoid:**
1. Verify the object exists in MinIO (via `stat_object()`) before returning from the upload function. This adds a small round-trip but eliminates the race.
2. Generate the presigned URL only after confirming the object exists.
3. Structure the Celery task as an explicit pipeline: `generate_pdf → upload_to_minio → send_telegram → send_whatsapp`, with each step as a separate Celery task in a `chain()`. Each step checks for the previous step's result before proceeding.
4. The Telegram send step should set `AuditReport.telegram_sent=True` before the WhatsApp step, enabling idempotent retry.

**Warning signs:**
- `NoSuchKey` errors in Celery logs from the MinIO client
- Telegram API `400 Bad Request: wrong file identifier` errors
- Client receives PDF twice (retry without idempotency guard)

**Phase to address:** Phase: PDF Generation & Delivery

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Business logic in bot handlers (aiogram) instead of Django API | Faster initial coding | Bot becomes a second business logic layer; bugs in two places; untestable | Never — bot must be a thin client |
| Storing questionnaire answers only in FSM Redis state, not in Django DB after each answer | Simpler bot code | One Redis crash = lost partial questionnaire; user must restart | Never — always persist answers to DB immediately |
| Editing `QuestionnaireTemplate` questions in-place (no versioning) | Simpler admin UI | Historical CRM cards become unreadable; audit PDF shows wrong Q&A pairs | Never — versioning must be in place before first real order |
| Skipping HMAC verification on webhooks in dev, enabling it only in prod | Faster dev iteration | Dev habits carry to prod; one deploy without verification = fraud exposure | Never — HMAC check should be ON from day 1, just with a test secret |
| Using MemoryStorage for aiogram FSM in production | Simplest setup | All user states lost on every bot restart | Never — always use RedisStorage in production |
| Generating PDF synchronously in the Django request cycle | Simpler architecture | Request timeout kills long PDFs; gunicorn worker held; 504 to user | Never — always use Celery |
| Single Redis instance for both Celery broker and FSM storage | Simpler infra | Memory pressure on Celery tasks evicts FSM keys | Acceptable at MVP scale; separate DBs (DB 0/DB 1) is low-cost mitigation |
| Hardcoding tariff prices in code | Fast shipping | Admin cannot change prices without code deployment; violates key requirement | Never — prices in DB from day 1 |
| Skipping WhatsApp delivery status confirmation | Simpler code | False `delivered` status; client never receives PDF; admin doesn't know | Unacceptable post-MVP; delivery status tracking should be in Phase: Delivery |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| CloudPayments webhook | Comparing `Content-HMAC` using `==` (timing attack vulnerable) | Use `hmac.compare_digest(computed, received)` — constant-time comparison |
| CloudPayments webhook | Processing payment before HMAC validation | Validate HMAC as the very first action; reject with 400 if invalid, before any DB access |
| CloudPayments webhook | Returning non-200 after processing | CloudPayments retries on any non-200; always return 200 with `{"code": 0}` even if you detect a duplicate |
| CloudPayments | Trusting `Amount` from webhook body without verification | Always verify the amount matches the expected tariff price from your DB, not the body |
| aiogram 3 FSM | Triggering bot state transitions from Django directly | The bot process has its own event loop. Trigger via Celery task that calls the Telegram API, not direct aiogram state manipulation from Django |
| aiogram 3 FSM | Polling in production | Use webhook mode in production. Long-polling in production creates reconnect loops and misses updates during restarts |
| WeasyPrint | Relative paths for images and fonts in HTML template | Use `base_url=request.build_absolute_uri('/')` or absolute filesystem paths — relative paths fail when WeasyPrint runs in a different working directory |
| WeasyPrint | Large inline base64 images in HTML | Increases memory spike during rendering; use file:// paths to images in the container instead |
| Wazzup24 | Sending PDF as raw bytes via API | Use URL-based file attachment (MinIO presigned URL) if Wazzup24 supports it — avoids base64 encoding overhead |
| Wazzup24 | Not handling 429 rate limit responses | Implement exponential backoff in the Celery retry; Wazzup24 / WhatsApp enforces rate limits per WABA number |
| MinIO presigned URLs | Using default presigned URL expiry (hours) for PDF delivery | PDF download links sent to clients should be long-lived (7–30 days) or use permanent public bucket policies — a 15-minute presigned URL in the WhatsApp message becomes dead before the client opens it |
| Django + Celery | Running `migrate` in both `web` and `worker` entrypoints | Only one service runs migrations; use Docker Compose `depends_on` with healthcheck |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| WeasyPrint called in the same Celery worker as other tasks | Worker memory grows and OOM-kills interrupt unrelated tasks | Dedicated `pdf` Celery queue with `--max-tasks-per-child=5` | After ~10 PDF generations in one worker lifetime |
| Django admin loading all 27 answers inline for every Submission in the list view | Admin list page times out with 100+ submissions | Use `list_select_related`, limit inline queryset, add `raw_id_fields` | ~50–100 submissions |
| `Answer.objects.filter(submission=sub)` called N times in a loop (N+1) | Admin CRM card slow with 27 answers | `prefetch_related('answers__question')` on the Submission queryset | Even at 1 submission with 27 answers — this is always a bug |
| Telegram `sendDocument` called with `open(file_path, 'rb')` from disk in Celery | File descriptor leak; worker crashes | Pass MinIO presigned URL as string to `sendDocument(document=url)` | Immediately — file descriptors are a limited resource |
| Celery Beat scheduling the same reminder task without deduplication | Clients receive duplicate "haven't finished questionnaire" messages | Use a `reminder_sent_at` field on Submission; skip if already sent within the period | Every Beat tick after the first |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Not validating CloudPayments HMAC | Fraudulent payment confirmation — attacker POSTs fake `pay` webhook to activate an order without payment | HMAC validation must be the first line in the webhook view; reject all unsigned requests |
| Deep link token with no expiry or no single-use enforcement | Token replay attack; attacker uses old link to create new orders or hijack client identity | Tokens expire in 48h; marked `used=True` after first page load |
| MinIO bucket set to public-read with predictable PDF file paths | Any person with the URL (or able to guess it) can access any client's audit report | Use either presigned URLs with expiry, or keep bucket private and generate fresh presigned URLs on demand via the `/cabinet` API |
| `telegram_id` as the sole authentication factor for API calls | Anyone who knows a client's `telegram_id` (which is not secret) can call client endpoints | For any sensitive client API endpoint, validate that the JWT token was issued for the requesting `telegram_id`. JWT tokens must be short-lived. Never expose `telegram_id` in URLs |
| Storing CloudPayments API secret (`password`) in code or `.env` committed to git | Secret exposed in repository; anyone can create fake webhooks | Use `.env.example` with placeholder values; `.env` in `.gitignore`; rotate secret if ever committed |
| Admin panel accessible without HTTPS in production | Session cookies transmitted in plaintext; session hijacking | Enforce HTTPS in nginx config; set `SECURE_SSL_REDIRECT=True`, `SESSION_COOKIE_SECURE=True` in Django settings |
| Personal data (name, company, phone) stored without considering KZ data law | Regulatory violation; fines from Ministry of Digital Development | See KZ compliance section below |

---

## Kazakhstan Personal Data Law Compliance

**Confidence:** MEDIUM (verified against official KZ law text and 2024 amendments)

Kazakhstan Law No. 94-V "On Personal Data and their Protection" imposes specific obligations:

| Requirement | What It Means for Baqsy | Implementation |
|-------------|--------------------------|----------------|
| Data residency | Restricted personal data (name, phone, company details) must be stored in databases **located in Kazakhstan** | Hosting must be KZ-based (e.g., KazCloud, PS.kz, or a Kazakhstani DC); MinIO and PostgreSQL must run in KZ |
| Consent | Consent must be obtained before collecting personal data | Onboarding flow must include explicit consent checkbox with link to Privacy Policy |
| Breach notification | Since July 1, 2024: notify the Ministry of Digital Development of any data breach | Implement incident response procedure; document in operational playbook |
| Physical ID copy ban | Since 2024: cannot collect scanned copies of identity documents | Do not add passport/ID upload features without legal review |
| Privacy policy | Must publish and maintain a Privacy Policy describing what data is collected and why | Write Privacy Policy page; link from bot `/start` and website footer |
| Right to erasure | Users can request deletion of their data | Admin must have a "Delete client data" action in CRM |

**Phase to address:** Phase: Infrastructure & Docker Setup (hosting location decision before any production data); Phase: Web Platform (consent flows, Privacy Policy page)

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Bot asks all 27 questionnaire questions in one session without progress indication | Users don't know how many questions remain; abandon mid-way | Add progress indicator: "Question 12 of 27" in each message |
| Bot times out mid-questionnaire and doesn't offer resume | User loses progress, is confused, must start over | `/status` command shows current position; bot proactively offers to resume when user re-engages |
| Payment widget opens in Telegram's in-app browser, which sometimes blocks pop-ups | User cannot complete payment; clicks back confused | Test CloudPayments widget in TG WebView specifically; offer fallback "open in browser" link |
| PDF sent via Telegram without a preview or text accompaniment | User receives a file with no explanation | Always send a text message first ("Your audit report is ready!"), then the document |
| Admin "Confirm & Send" button triggers delivery immediately without a preview | Admin accidentally sends half-finished audit | Add confirmation modal: "Are you sure? This will send the PDF to the client immediately" |
| Upsell flow requires re-entering payment details without explaining what changed | Users unsure what they're paying for | Upsell page must clearly show: "You're upgrading from Ashide 1 to Ashide 2. You will pay 90,000 ₸ additionally." |
| Deep link URL in bot message is very long and looks suspicious | Users hesitant to click | Use `https://t.me/{bot}?start=TOKEN` format to keep URLs short and branded, or shorten the web URL |

---

## "Looks Done But Isn't" Checklist

- [ ] **CloudPayments webhook:** Handler returns 200 always AND validates HMAC AND idempotently creates Payment — verify all three with a unit test that replays the same webhook twice
- [ ] **FSM state:** Verify that aiogram is configured with RedisStorage (not MemoryStorage) in production. Check `docker-compose.prod.yml` explicitly.
- [ ] **PDF delivery:** Verify DeliveryLog has separate statuses for `queued_telegram`, `sent_telegram`, `queued_whatsapp`, `sent_whatsapp` — not a single boolean
- [ ] **Template versioning:** Verify that editing a live template in Django admin creates a new version rather than mutating in-place — write an integration test that edits a template and confirms historical Submission still renders correctly
- [ ] **Migrations in Docker:** Verify only one service runs `migrate`; confirm with `docker-compose logs` during a fresh `up` that migrations run exactly once
- [ ] **HTTPS:** Verify `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_SSL_REDIRECT` are `True` in production settings
- [ ] **MinIO PDF URLs:** Verify that a presigned URL sent to a client is valid for at least 7 days, not just 15 minutes
- [ ] **Bot in production:** Verify bot is running in webhook mode, not long-polling. Check that only one bot instance is running (polling + webhook simultaneously causes duplicate update processing)
- [ ] **Celery visibility timeout:** Verify `broker_transport_options = {"visibility_timeout": 43200}` in Celery config (12 hours, safely above any realistic task duration)
- [ ] **Tariff prices in DB:** Verify admin can change price from Django admin and the CloudPayments widget reflects the new price without code deployment
- [ ] **KZ data residency:** Verify production hosting is physically in Kazakhstan before any real user data is collected

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Duplicate Payment records created | MEDIUM | Deduplicate by `transaction_id`; manually verify which was processed; issue manual refund if double-charged; add DB unique constraint immediately |
| User FSM state lost mid-questionnaire | LOW | User can restart with `/start`; bot checks DB for existing `in_progress` Submission and resumes from last saved Answer; no data loss if answers were persisted per-step |
| Wrong Q&A on historical audit card (template mutated) | HIGH | Cannot recover original question text if it was overwritten; must rewrite from scratch using client memory or re-interview; add versioning migration immediately |
| PDF sent with missing Cyrillic | MEDIUM | Regenerate PDF with fixed Docker image; resend via bot and WhatsApp; admin manually notifies client |
| Worker OOM-killed, PDF tasks stuck PENDING | LOW | Restart worker container; tasks re-queue automatically if `acks_late=True`; verify idempotency before restarting |
| Deep link token replayed (duplicate Submission) | MEDIUM | Identify duplicate Submissions via `telegram_id`; manually cancel the duplicate; refund if payment was made; add single-use token migration |
| Migration ran twice, data inconsistency | HIGH | Restore from last PostgreSQL backup (MinIO cron backup); replay events from CloudPayments transaction log; this is why automated backups are non-negotiable |
| Wazzup24 WhatsApp not delivered | LOW | Admin manually sends PDF via their personal WhatsApp as fallback; `DeliveryLog` failure flag triggers admin notification in CRM |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Webhook duplicate processing | Phase: Payments & Webhook Integration | Replay same webhook twice in test; assert single Payment record and single state transition |
| FSM state eviction | Phase: Bot FSM + Questionnaire Flow | Kill Redis mid-questionnaire in integration test; verify bot can resume from DB |
| Template versioning breakage | Phase: Industries & Questionnaire Templates | Edit live template; assert historical Submission renders original questions |
| WeasyPrint Cyrillic font failure | Phase: PDF Generation & Delivery | CI renders PDF with Cyrillic sample text; `pdftotext` asserts non-empty output |
| WeasyPrint memory growth | Phase: PDF Generation & Delivery | Load test: generate 20 PDFs in sequence; assert worker RSS stays below 1 GB |
| WhatsApp fire-and-forget | Phase: PDF Generation & Delivery | Mock Wazzup24 API returning 200 but no delivery webhook; assert `DeliveryLog.status` stays `queued` |
| Deep link token replay | Phase: Web Platform + Payment Integration | Reuse same token twice; assert second attempt returns existing Submission, not a new one |
| Celery visibility timeout duplication | Phase: PDF Generation & Delivery (Celery infra) | Enable `acks_late` and simulate worker crash mid-PDF; assert exactly one PDF is generated |
| Migration race in Docker Compose | Phase: Infrastructure & Docker Setup | Run `docker-compose up` from clean state; verify migrations appear exactly once in logs |
| CRM lost update | Phase: CRM Admin Dashboard | Simulate two concurrent POSTs to save audit; assert second is rejected with conflict error |
| MinIO URL expiry | Phase: PDF Generation & Delivery | Assert presigned URL TTL >= 7 days in generated DeliveryLog |
| KZ data residency | Phase: Infrastructure & Docker Setup | Confirm hosting provider datacenter location before collecting any real user data |

---

## Sources

- CloudPayments developer documentation on webhook HMAC headers: https://developers.cloudpayments.ru/en/
- aiogram 3 FSM storages documentation: https://docs.aiogram.dev/en/stable/dispatcher/finite_state_machine/storages.html
- WeasyPrint GitHub issue — font fallback broken in v57: https://github.com/Kozea/WeasyPrint/issues/1776
- WeasyPrint GitHub issue — memory leak per PDF generation: https://github.com/Kozea/WeasyPrint/issues/2130
- Celery GitHub issue — task duplication with Redis + acks_late + retry: https://github.com/celery/celery/discussions/9963
- Celery GitHub issue — long-running job redelivery after visibility timeout: https://github.com/celery/celery/issues/5935
- Django ticket — admin change form race condition (ticket #27477): https://code.djangoproject.com/ticket/27477
- Vinta Software — Advanced Celery for Django guide: https://www.vintasoftware.com/blog/guide-django-celery-tasks
- Safe Django migrations guide (2025): https://www.loopwerk.io/articles/2025/safe-django-db-migrations/
- Kazakhstan personal data law amendments (2024): https://gratanet.com/publications/persona-data-protection-state-oversight-and-legislative-updates
- Wazzup24 attachment requirements (51 MB API limit): https://wazzup24.com/help/how-to-use-en/requirements-for-attachments/
- Webhook handling race conditions — Vinta Engineering: https://excessivecoding.com/blog/billing-webhook-race-condition-solution-guide

---

*Pitfalls research for: Telegram bot + Django + CloudPayments KZ + WeasyPrint PDF + Wazzup24 WhatsApp SaaS*
*Researched: 2026-04-15*
