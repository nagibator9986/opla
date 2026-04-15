# Feature Research

**Domain:** Business audit SaaS with Telegram bot funnel, payment-gated questionnaire, manual expert report, PDF delivery via Telegram + WhatsApp
**Project:** Baqsy System (Kazakhstan/CIS SMB market)
**Researched:** 2026-04-15
**Confidence:** MEDIUM–HIGH (domain patterns from comparable SaaS + direct project requirements verified)

---

## Feature Landscape

Feature categories follow the 10 domains specified in the research scope:
Bot Onboarding / Questionnaire UX / Payments / Client Cabinet / Admin CRM / PDF Reports / Delivery / Upsell-Retention / Analytics / Content Management.

---

## 1. Bot Onboarding

### Table Stakes

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| /start command launches FSM scenario | Telegram convention — users expect tap-and-go entry | S | aiogram 3 FSM, Redis storage |
| 5-question intake (name, company, industry, contact, city) | Without basic profiling, industry-specific routing is impossible | S | Block A questions; industry choice drives template selection |
| Inline keyboard buttons for industry selection | Free-text industry entry causes typos, misrouting; buttons are Telegram UX norm | S | Render as InlineKeyboardMarkup; store Industry.id |
| Deep-link handoff to website with pre-filled context | User must not re-enter data on the payment page; continuity is expected | M | `tg://start?start_param=<uuid>` or signed URL parameter |
| Post-payment re-entry into bot automatically | After payment user must not hunt for next step; bot must receive callback and resume | M | CloudPayments webhook → Django → push Telegram message |
| Progress indicator during questionnaire | 27 questions is long; user needs to know "question 7/27" to stay motivated | S | Text prefix "Вопрос 7 из 27" in every message |
| Save-and-resume on disconnect | Mobile connections drop; losing progress kills completion rate | M | Each answer persisted to DB immediately; FSM state in Redis survives reconnect |
| /status command | Users ask "where is my report?" — give them a self-service answer | S | Returns Submission.status in human-readable form |
| Final "Thank you, your audit is in progress" message | Without closure message user assumes bot is broken | S | Sent immediately after last question answered |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Industry-conditional question blocks (B/C differ per industry) | Audit is relevant, not generic — main competitive claim | M | QuestionnaireTemplate versioned per Industry; Block A universal |
| Skip-to-resume on re-/start if questionnaire in progress | User drops off, returns next day, picks up exactly where they left | M | Check FSM state + Submission.status on every /start |
| Warm, personalised message copy (RU, «Вы») | Trust and tone matter for KZ/RU audience; formal-warm voice converts | S | Copywriting decision, not engineering |

### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Free-text industry entry | "More flexible" | Spelling variants, impossible to route to template reliably | Inline keyboard with fixed industry list; admin can add industries in CRM |
| Sending all 27 questions at once as a list | "Faster for user" | Overwhelming, abandonment rate spikes; loses per-answer persistence | One question per message; proven 40% higher completion in chatbot surveys |
| Collecting payment inside Telegram (Stars, etc.) | "Seamless" | CloudPayments KZ is required; Telegram Payments doesn't support KZT acquiring | Deep-link to web payment page |

---

## 2. Questionnaire UX

### Table Stakes

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| One question per message, sequential | Conversational norm in Telegram; reduces cognitive load | S | FSM state advances only on valid answer |
| Input validation per field type (text / number / choice / multichoice) | Without validation garbage data enters the audit; admin cannot work with it | M | JSONB Answer.value; validation in bot handler before persisting |
| Back button / ability to re-answer previous question | Users make typos; no back = frustration, abandonment | M | Store answer history per submission; allow single-step back |
| Timeout reminder after 24h inactivity | High drop-off window; reminder recovers revenue | M | Celery beat scheduled task checks incomplete submissions |
| Block structure visible to user (Block A / B / C transitions) | Signals progress, resets mental count | S | "Раздел 2 из 3" transition message |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Conditional skip logic within industry template | More relevant questionnaire; fewer irrelevant questions | M | Question.depends_on FK + condition JSONB; evaluated in bot handler |
| Inline keyboard answers for choice questions | Faster, no typos, mobile-friendly; increases throughput | S | field_type=choice → InlineKeyboardMarkup options |
| Character/format hint in question text | "Введите число (например: 5 000 000)" reduces wrong-format retries | S | hint field on Question model |

### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Branching into sub-questionnaires mid-flow | "Deeper personalization" | Exponential template maintenance complexity; version-safety breaks | Keep blocks B/C as flat 27-question sets per industry; branching only for skips |
| Photo/document upload questions | "Richer audit data" | S3 upload flow in bot is complex; admins receive files not text | Out of scope for v1; consider for v2 if admin requests |

---

## 3. Payments

### Table Stakes

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| CloudPayments KZ widget on tariff page | Required by client; standard KZ acquiring | M | `publicId` from env; CP JS widget injected in React page |
| HMAC webhook signature verification | Financial security baseline; without it anyone can fake a payment | M | `Content-HMAC` header; Django middleware validates before processing |
| Idempotent webhook processing | CP can re-send same webhook; double-activation is a real failure mode | S | Unique index on Payment.external_id (TransactionId) |
| Payment status reflected in Submission (paid → in_progress) | Downstream trigger for questionnaire start | S | Webhook handler updates both Payment and Submission atomically |
| KZT currency, price from DB | Admin can change prices without deploy; required by client | S | Tariff model with `price_kzt` and `is_active` fields |
| Receipt/confirmation message in bot | User needs proof of payment before continuing | S | Bot message sent via Celery task after webhook confirmation |
| Failure handling: declined card message | Without clear failure message user assumes system is broken | S | CP returns failure reason; display it on frontend; bot fallback message |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Apple Pay / Google Pay via CloudPayments | KZ mobile users heavily use these; lower friction at checkout | S | CloudPayments widget supports both natively; zero extra dev work |
| Pre-filled payment form (name, email from bot profile) | One fewer step; familiar data reduces abandonment | M | Pass client data as widget initialization params |

### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Kaspi QR payment | Popular in KZ | CloudPayments KZ widget already covers it via Kaspi integration layer; duplicating is engineering overhead | Use CP widget which includes Kaspi; verify in CP dashboard |
| Auto-refund processing | "Automation" | Refund policy undefined; auto-refunds are irreversible | Admin initiates refund manually via CP dashboard; log in Submission |
| Subscription / recurring billing | "MRR model" | Product is transactional, not subscription; CP recurring adds significant complexity | Out of scope for v1 |

---

## 4. Client Cabinet (Personal Account)

### Table Stakes

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Order status page (created / paid / in_progress / under_audit / delivered) | Client paid 45–135k KZT; must see what is happening with their order | S | Submission.status mapped to user-facing labels in RU |
| PDF download link (active after delivery) | Client needs to save/re-read their report; permanent URL expected | S | Signed S3/MinIO pre-signed URL, expire after N days or per-request token |
| Upsell CTA: "Upgrade to Ashıde 2" button | Shows after Ashıde 1 delivery; natural upgrade trigger | M | Only visible when: tariff=ashide_1 AND status=delivered AND no upsell paid |
| Authentication via Telegram (telegram_id) | No separate password for client; Telegram is the channel | S | URL with signed token generated at bot → stored as session cookie or JWT |
| Mobile-responsive layout | KZ SMB owners access on mobile; non-responsive = unusable | S | Tailwind responsive grid; test on 375px |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Status timeline with timestamps | "When was my audit started? When will it be ready?" — reduces support load | S | Display Submission status change log with dates |
| "Share report" button (copy link) | Business owners share results with partners | S | Pre-signed URL with fixed expiry; no auth required to download |

### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Full SPA client account with multiple orders history | "Full-featured portal" | Complexity for v1; most clients have 1 order | Single-order view for v1; multi-order list is trivial to add in v1.x |
| Chat with auditor from cabinet | "Direct communication" | Breaks async workflow; admin does not want real-time commitments | Async: client contacts via Telegram bot /help; admin replies via bot |
| Report editing requests from client | "Feedback loop" | Scope creep; undermines finality of audit | Not in v1; manual process if client calls |

---

## 5. Admin CRM

### Table Stakes

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Order list with status filters and sorting | Without filterable list admin cannot manage a queue of 20+ orders | S | Django DRF list endpoint; React table with status/date/industry filters |
| Order card: client answers + audit input field + "Confirm and Send" | Core workflow of the whole product; everything else serves this | M | Rich textarea for audit text; one-click triggers PDF generation + delivery |
| New order notification (email or Telegram to admin) | Admin must know in real-time when a new completed submission arrives | S | Celery task sends Telegram message to admin chat_id on status→completed |
| Order status history (audit trail) | Admin must see when status changed and by whom | S | StatusLog model: submission_id, from_status, to_status, actor, timestamp |
| Industry + questionnaire template manager (CRUD) | Admin must add new industries without a developer | M | Django admin or custom React CRM page; CRUD for Industry + QuestionnaireTemplate |
| Question editor per template with ordering | Admin needs to adjust question text and order independently | M | Inline editing; drag-and-drop order with integer `order` field |
| Template versioning: new version on edit, old orders unaffected | Safety invariant; without this historical data is corrupted | M | On save: create new QuestionnaireTemplate with version+1, set is_active=True on new, False on old |
| Tariff price editor (no deploy) | Required by client explicitly | S | Tariff model with price_kzt; admin edits in CRM UI |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Side-by-side answers + audit writing layout | Reduces admin context switching; increases audit quality and speed | M | Split-pane UI: left=answers, right=audit textarea |
| Answer export to CSV for a submission | Admin can paste into external tools if needed | S | Django CSV view; single-submission export |
| Industry/region breakdown in stats | Helps owner understand which segments buy most | M | Aggregation query; chart in dashboard (Recharts on React side) |
| Overdue order highlighting (SLA breach warning) | Admin may lose track; visual alert prevents client complaints | S | Color-coded row if `completed_at` > N hours ago and status still under_audit |

### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Multi-admin with role permissions | "Team scaling" | Not needed for v1 solo admin; adds auth complexity | Single admin account; add RBAC in v2 if team grows |
| Automated AI-generated audit text | "Saves time" | Explicitly out of scope per client requirement; owner wants human authorship | Human-written field; AI assist could be v2 opt-in |
| Client messaging from CRM | "Communication hub" | Wazzup24/TG are the channels; building a third one creates fragmentation | Admin communicates via Telegram bot commands or Wazzup dashboard directly |

---

## 6. PDF Reports

### Table Stakes

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Branded cover with client name + company name | Product is "personalised audit"; generic cover undermines the value prop | M | Jinja2 template variables; WeasyPrint @page CSS |
| Two report lengths: Ashıde 1 (7–9 params) vs Ashıde 2 (18–24 params) | Two paid tiers have different deliverables; wrong template = refund demand | M | Two separate Jinja2 HTML templates; selected by Submission.tariff |
| Consistent typography, page numbers, header/footer | "Солидный" (premium) feel explicitly requested by client | M | WeasyPrint @page rules; embedded fonts; position: running() for header |
| Unique filename per client (company + date) | File must be identifiable when client saves it to disk | S | `{company_slug}_{date}_audit.pdf` |
| Stored in MinIO, access via signed URL | File must survive bot restart and be re-downloadable | S | Celery upload task after generation; URL stored on AuditReport model |
| Async generation (Celery task) | PDF generation is CPU-heavy (1–5s); must not block Django request | S | Celery task triggered on admin "Confirm" action |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| «Вечный Иль» book visual style integration | Owner's brand identity; makes report feel like premium product | M | Design in HTML/CSS; fonts, colors, decorative elements per brand guide |
| Charts / visual metrics in Ashıde 2 report | Visual data is more persuasive and sharable than plain text | M | SVG charts embedded in HTML template; WeasyPrint renders SVG natively |
| Section page breaks matching audit structure | Professional layout; no orphaned headings | S | CSS `page-break-before: always` on section containers |
| Print-optimised (A4, CMYK-ready) | Client may print and hand to investors/bank | S | CSS `@media print` + A4 page dimensions in @page |

### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Editable PDF (fillable form) | "Client can update" | Complex (requires PDF form library, not WeasyPrint); no use case defined | Static PDF is the deliverable; if edits needed, admin regenerates |
| Multiple PDF versions per order (draft + final) | "Review workflow" | Adds storage and versioning complexity | Admin edits text in CRM before confirming; one final PDF generated |
| DOCX export | "Client needs Word format" | Different rendering stack entirely | Not in scope; PDF is the standard for formal audit reports |

---

## 7. Delivery

### Table Stakes

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| PDF sent to Telegram chat where client completed questionnaire | Client used Telegram throughout; they expect result there | S | Bot sends document via `bot.send_document(chat_id, file)` |
| PDF sent to WhatsApp via Wazzup24 | Explicitly required by client; WhatsApp is primary in KZ business communication | M | Wazzup24 REST API; send file + cover message; abstract as WhatsAppProvider |
| Delivery confirmation logged (TG delivered / WA delivered) | Admin must know if delivery succeeded or failed | S | DeliveryLog model: channel, status, timestamp, error_message |
| Retry on delivery failure (Celery retry) | Network failures are common; silent failure is unacceptable | M | Celery task with max_retries=3, exponential backoff |
| Admin notification on delivery success | Closes the loop; admin knows the client received the report | S | Push Telegram message to admin after both channels confirm |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Cover message in WhatsApp with client name + personalised text | Makes WhatsApp delivery feel deliberate, not robotic | S | Jinja2 message template with `{{client_name}}`, `{{company}}` |
| Delivery status visible in client cabinet | "Did my report go to WhatsApp?" — self-service reduces support messages | S | DeliveryLog status displayed on cabinet page |

### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Email delivery | "Backup channel" | Out of scope v1; adds SMTP/SendGrid dependency | TG + WA is the agreed dual channel; email is v2 |
| Push notification to Telegram channel/group | "Marketing" | Unrelated to order delivery flow | Separate marketing tool (not this system) |
| Scheduled delayed delivery ("send tomorrow morning") | "Better open rate" | Adds scheduling complexity; audit is awaited, immediate delivery is better | Send immediately on admin confirm |

---

## 8. Upsell / Retention

### Table Stakes

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Upsell button in client cabinet after Ashıde 1 delivery | Standard SaaS upgrade pattern; +90k KZT per conversion | S | Show only when tariff=ashide_1 AND status=delivered |
| Upsell payment via same CloudPayments flow | Consistent payment experience | M | New Payment record for upsell; Submission.tariff upgraded on webhook; no new questionnaire |
| Upsell = no re-questionnaire | Explicitly agreed; removes friction from upgrade | S | On upsell webhook: update Submission.tariff, trigger Ashıde 2 PDF regeneration from existing answers |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Timed upsell reminder via bot (48h after delivery) | Passive reminder converts warm clients who missed the button | M | Celery beat task; one reminder only; check if upsell already purchased |
| "What you get in Ashıde 2" comparison on upsell page | Addresses "is it worth 90k more?" objection | S | Static content on upgrade page; 9 vs 24 parameter comparison table |

### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Email drip re-engagement sequence | "Retention automation" | Email not a channel in this product; client lives in TG/WA | Single Celery-scheduled TG bot reminder; not a drip sequence |
| Referral program | "Growth" | MVP complexity; referral tracking is a product of its own | Manual word-of-mouth; add in v2 with UTM tracking |
| Cross-sell (different products) | "Revenue diversification" | No other products defined; premature | Focus on upsell only; v2 if owner launches new audit products |

---

## 9. Analytics / Dashboard

### Table Stakes

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Total revenue (KZT, by period) | Owner must see business performance | S | Aggregate Payment.amount WHERE status=succeeded |
| Order count by status | Operational visibility: how many in queue? | S | GROUP BY Submission.status |
| Conversion funnel: created → paid → completed → delivered | Shows where clients drop off | M | Count per status stage; percentage falloff |
| Orders by industry | Main segmentation dimension | S | JOIN Submission → Industry; GROUP BY |
| Orders by city/region | KZ geography matters for expansion decisions | S | GROUP BY ClientProfile.city |
| Orders by tariff (Ashıde 1 vs 2 vs upsell) | Revenue mix visibility | S | GROUP BY Payment.tariff |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Average audit completion time (questionnaire started → delivered) | Operational SLA visibility; helps owner set client expectations | S | `delivered_at - paid_at` average |
| Upsell conversion rate | KPI for upsell effectiveness | S | upsell payments / ashide_1 deliveries |
| Orders over time chart | Trend visibility | S | Recharts LineChart in React; data from `/api/dashboard/orders-over-time/` |

### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Real-time live dashboard (WebSocket) | "Always current" | WebSocket infrastructure for a single-admin tool is over-engineering | Polling every 60s or manual refresh; sufficient for order volume expected |
| Client cohort analysis / LTV | "Advanced analytics" | Transactional product, not subscription; LTV is single-order | Not meaningful until repeat-purchase pattern emerges |
| Google Analytics / Mixpanel embedded | "Marketing funnel" | Separate concern; adds third-party script complexity to admin | Use built-in stats; GA on landing page frontend separately if needed |

---

## 10. Content Management

### Table Stakes

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Landing page text editable from admin (no deploy) | Explicitly required; owner changes copy regularly | M | Page sections as DB-backed ContentBlock model; React renders via API |
| Tariff names + prices editable from admin | Prices can change; deploy for price change is unacceptable | S | Tariff model in DB; admin UI form |
| Case studies / testimonials manageable from admin | Owner adds new client cases without a developer | M | Case model with text + logo fields; displayed on landing page |
| Industry list manageable (add new industries) | New vertical = new questionnaire; should not need a developer | M | Industry CRUD in admin; triggers template creation flow |
| Questionnaire question text editable (with versioning) | Question wording improves over time | M | Edit creates new template version automatically |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| PDF template HTML editable by developer in templates/pdf/ folder | Design updates without full redeploy; git pull + restart | S | Jinja2 templates in a mounted volume; `docker-compose restart worker` applies |
| Preview landing page changes before publish | Prevents typo going live | M | Draft/Published state on ContentBlock; preview mode in React |

### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Full headless CMS (Contentful, Strapi) | "Flexibility" | Over-engineered for a landing page with ~8 sections; heavy dependency | Simple Django ContentBlock model with textarea fields; sufficient |
| WYSIWYG rich text editor for all content | "Easy editing" | Rich text in questionnaire questions creates formatting bugs in bot messages | Plain text for questions; simple textarea for landing content; Markdown for audit text field |

---

## Feature Dependencies

```
[CloudPayments webhook] ──requires──> [Submission.status=paid]
    └──triggers──> [Bot questionnaire start message]
                       └──requires──> [QuestionnaireTemplate selected by industry]
                                          └──requires──> [Industry set during onboarding]

[Admin "Confirm and Send"] ──triggers──> [Celery PDF generation task]
    └──requires──> [AuditReport.text filled]
    └──requires──> [Submission.status=under_audit]
                       └──generates──> [PDF stored in MinIO]
                                          └──triggers──> [Telegram delivery task]
                                          └──triggers──> [WhatsApp (Wazzup24) delivery task]

[Upsell payment webhook] ──requires──> [Submission.tariff=ashide_1 AND status=delivered]
    └──triggers──> [Ashıde 2 PDF regeneration from existing answers]
                       └──requires──> [All 27 answers already in DB]

[Client cabinet status page] ──requires──> [Submission exists for telegram_id]
    └──enhances──> [DeliveryLog status display]

[Template versioning] ──protects──> [Historical submissions (old answers + old template version)]
    └──invariant: edit creates new version, does not mutate existing]

[Celery reminder task] ──requires──> [Celery beat running]
    └──reads──> [Submission.status=in_progress AND last_answer_at < 24h ago]
```

### Dependency Notes

- **Questionnaire requires Industry selection during onboarding:** If industry is not set, no template can be loaded. Industry selection in Step 1 of onboarding is blocking for the entire downstream flow.
- **PDF generation requires audit text:** Admin must write audit content before "Confirm" button is available. Empty text = generation blocked.
- **Upsell requires completed Ashıde 1 delivery:** The upgrade path depends on existing answers being in DB. This means the upsell can safely regenerate a longer PDF without re-asking questions.
- **Template versioning protects historical data:** Any edit to question text/order must create a new version. This is a hard invariant; violation corrupts audit-to-answer mapping.
- **DeliveryLog required for retry logic:** Celery retry decisions must check DeliveryLog to avoid double-sending after transient failures.

---

## MVP Definition

### Launch With (v1)

These are required for the described funnel to work end-to-end.

- [ ] Bot FSM onboarding: /start → 5 questions → deep-link — *gateway to everything*
- [ ] Industry-specific questionnaire templates (at least 5 industries, versioned) — *core product differentiation*
- [ ] CloudPayments KZ widget + HMAC webhook + idempotency — *revenue gate*
- [ ] Post-payment questionnaire flow in bot (27 questions, one per message, with persistence) — *data collection*
- [ ] Admin CRM order list + order card with answers + audit textarea + "Confirm and Send" — *human expert value add*
- [ ] Celery PDF generation via WeasyPrint (two templates: Ashıde 1, Ashıde 2) — *deliverable*
- [ ] Telegram delivery of PDF — *primary channel*
- [ ] WhatsApp delivery via Wazzup24 — *required by client*
- [ ] Client cabinet with status + PDF download — *client self-service*
- [ ] Upsell flow: payment → upgrade tariff → regenerate PDF — *second revenue stream*
- [ ] Admin content management: tariff prices, landing texts, questionnaire questions — *owner autonomy*
- [ ] Dashboard: revenue, order counts by status/industry/tariff — *operational visibility*

### Add After Validation (v1.x)

- [ ] Conditional skip logic within templates — *trigger: admin requests; complex industries with optional blocks*
- [ ] 24h drop-off reminder via bot — *trigger: measurable completion rate drop-off*
- [ ] Status timeline with timestamps in client cabinet — *trigger: support questions about order timing*
- [ ] Overdue SLA warning in CRM — *trigger: admin misses orders*
- [ ] Charts/SVG metrics in Ashıde 2 PDF — *trigger: client feedback on report presentation*
- [ ] Upsell reminder via bot (48h Celery task) — *trigger: upsell conversion rate below expectation*
- [ ] Preview mode for landing content changes — *trigger: owner publishes a typo*

### Future Consideration (v2+)

- [ ] AI-assisted audit text drafts (opt-in, admin still reviews) — *explicitly deferred by client; revisit after v1 volume*
- [ ] Multi-admin with role permissions — *trigger: team grows beyond solo admin*
- [ ] Email delivery channel — *trigger: client requests it*
- [ ] Photo/document upload questions in questionnaire — *trigger: auditor requests richer data*
- [ ] Referral tracking — *trigger: organic word-of-mouth identified as growth channel*
- [ ] KZ and EN language support — *trigger: validated demand outside Russian-speaking segment*
- [ ] White-label / multi-tenant — *trigger: partner agencies want to resell the platform*

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Bot FSM onboarding (5 questions + deep-link) | HIGH | LOW | P1 |
| Industry questionnaire templates + versioning | HIGH | MEDIUM | P1 |
| CloudPayments webhook + idempotency | HIGH | MEDIUM | P1 |
| Post-payment 27-question bot flow | HIGH | MEDIUM | P1 |
| Admin CRM order card + audit confirm | HIGH | MEDIUM | P1 |
| WeasyPrint PDF generation (2 templates) | HIGH | MEDIUM | P1 |
| Telegram PDF delivery | HIGH | LOW | P1 |
| WhatsApp (Wazzup24) PDF delivery | HIGH | MEDIUM | P1 |
| Client cabinet (status + download) | MEDIUM | LOW | P1 |
| Upsell flow (payment → regen PDF) | HIGH | MEDIUM | P1 |
| Tariff price + landing content management | HIGH | LOW | P1 |
| Dashboard (revenue, orders by segment) | MEDIUM | MEDIUM | P1 |
| Progress indicator in bot ("7/27") | HIGH | LOW | P1 |
| Input validation per field type | HIGH | LOW | P1 |
| Admin new-order Telegram notification | HIGH | LOW | P1 |
| Back/re-answer in questionnaire | MEDIUM | MEDIUM | P2 |
| 24h drop-off reminder (Celery beat) | MEDIUM | MEDIUM | P2 |
| Delivery status in client cabinet | MEDIUM | LOW | P2 |
| SLA overdue highlight in CRM | MEDIUM | LOW | P2 |
| SVG charts in Ashıde 2 PDF | MEDIUM | MEDIUM | P2 |
| Upsell 48h reminder | MEDIUM | LOW | P2 |
| Status timeline in client cabinet | LOW | LOW | P2 |
| Conditional skip logic in templates | LOW | HIGH | P3 |
| Preview mode for content changes | LOW | MEDIUM | P3 |
| CSV export of submission answers | LOW | LOW | P3 |
| Multi-admin RBAC | LOW | HIGH | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

---

## Competitor Feature Baseline

No direct CIS-market competitor for this exact product type was found (business audit SaaS with Telegram-native funnel and manual expert review). The closest analogues are:

| Feature Area | Typeform / SurveyMonkey (global) | Consulting firms (manual) | Baqsy approach |
|---|---|---|---|
| Questionnaire delivery | Web form | Email / Google Forms | Telegram bot (native KZ channel) |
| Payment gate | Stripe/PayPal | Invoice | CloudPayments KZ (KZT, Kaspi) |
| Report | Auto-generated or none | Manual Word/PDF | Manual audit + auto-branded PDF |
| Delivery | Email | Email / WhatsApp manually | TG + WA automated |
| Admin tool | None / export to CSV | None | Dedicated CRM with order workflow |
| Industry branching | Generic | Per-client manual | Template-per-industry, versioned |
| Upsell | None | Manual offer | In-product, no re-questionnaire |

**Baqsy's competitive differentiation:** Telegram-native funnel (meets KZ/RU users where they are), industry-specific questionnaires (relevance), manual expert authorship (trust), dual-channel automated delivery (convenience).

---

## KZ/Russian-Speaking Audience Notes

These considerations are specific to the target market and affect feature decisions:

1. **WhatsApp is primary business communication in KZ** (>80% business users). Telegram is primary for communities and bots. Dual-channel delivery is not "nice to have" — it is expected.
2. **Kaspi is the dominant payment method** in Kazakhstan. CloudPayments KZ integrates Kaspi Pay within the widget — this must be verified active and prominently visible on the payment page.
3. **Formal-warm Russian tone ("Вы" not "ты")** in all bot messages and PDF copy. Casual tone reduces perceived authority of the audit.
4. **KZT pricing must be displayed as round numbers** (45 000 ₸ not 45 000.00 ₸) — cosmetic but matters for perception.
5. **City field in onboarding** is analytics-relevant: KZ business distribution is heavily skewed (Almaty, Astana account for ~60% of SMB activity). Segmenting by city informs where to focus marketing.
6. **Industry labels must be in Russian**, matching how KZ business owners self-describe (Ритейл, Услуги, Производство, HoReCa, IT — not English equivalents).
7. **No email assumed as a working channel**. Many KZ SMB owners have nominal email addresses but check them rarely. Telegram and WhatsApp are the real inboxes.

---

## Sources

- Project requirements: `/Users/a1111/Desktop/projects/oplata project/.planning/PROJECT.md` (HIGH confidence — direct client requirements)
- Chatbot questionnaire UX: PMC study "User Experience of a Chatbot Questionnaire Versus a Regular Computer Questionnaire" — one-question-at-a-time shows higher completion and preference
- Conversational survey completion rates: SurveySparrow "Why Survey Bots Outperform Static Forms" — 40% higher completion vs static forms
- SaaS upsell patterns: Userpilot "12 Real-World Upselling Examples in SaaS" — usage-based triggers, frictionless upgrade
- Payment UX: Usio "SaaS Platforms Should Take Control of Payments Experience" — pre-filled forms reduce abandonment
- WeasyPrint PDF: Medium "Using Weasyprint and Jinja2 to create PDFs" — CSS Flexbox, @page rules, embedded fonts
- Wazzup24 integration: wazzup24.com — WhatsApp Business API, message delivery status, file sending
- CloudPayments KZ: cloudpayments.ru/kz documentation — Widget, HMAC webhook, Kaspi Pay support
- CRM workflow patterns: Monday.com "CRM order management" — status tracking, color-coded queues
- Branching logic: Qualaroo "Skip Logic Best Practices" — reduces survey length 20–40%, increases completion
- Client portal patterns: HubSpot "Best customer portal SaaS tools" — order status, document download, mobile-first

---

*Feature research for: Business audit SaaS — Baqsy System (KZ/CIS market)*
*Researched: 2026-04-15*
