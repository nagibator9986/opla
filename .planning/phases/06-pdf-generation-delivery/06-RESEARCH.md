# Phase 6: PDF Generation & Delivery - Research

**Researched:** 2026-04-17
**Domain:** WeasyPrint PDF generation, MinIO/S3 storage, Celery task orchestration, Telegram Bot API sendDocument, Wazzup24 WhatsApp API v3
**Confidence:** HIGH (all major components already present in the codebase or verified against official docs)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**PDF-шаблон (PDF-01, PDF-02, PDF-03, PDF-04)**
- Один Jinja2 HTML-шаблон с условными секциями для Ashıde 1 и Ashıde 2
  - Ashıde 1: 7–9 параметров — короткий отчёт
  - Ashıde 2: 18–24 параметра — расширенный отчёт
  - Условие: `{% if tariff_code == 'ashide_2' %}` для дополнительных секций
- Обложка: имя клиента, название компании, отрасль, дата аудита, уровень тарифа
- Фирменный стиль: Cyrillic-шрифты (Liberation Sans, Roboto — уже в Docker), тёмные акценты (slate-900, amber-500)
- WeasyPrint рендерит HTML → PDF
- Шаблон в `backend/templates/pdf/audit_report.html`
- CSS в отдельном файле `backend/templates/pdf/styles.css` (или inline в шаблоне)

**Генерация PDF (PDF-05, PDF-06, PDF-07)**
- Celery-таск `generate_pdf(report_id)`:
  1. Загрузить AuditReport + Submission + ClientProfile + Answers
  2. Проверить идемпотентность: если `report.pdf_url` уже установлен — пропустить (PDF-07)
  3. Рендерить Jinja2-шаблон с данными клиента
  4. WeasyPrint HTML → PDF (в памяти, BytesIO)
  5. Загрузить PDF в MinIO: `pdfs/{submission_id}/{timestamp}.pdf`
  6. Получить presigned URL (TTL ≥ 7 дней) (PDF-05)
  7. Обновить `report.pdf_url` и `report.status = 'approved'`
- Worker config: `--pool=prefork --max-tasks-per-child=5` для защиты от memory leak WeasyPrint (PDF-06)
- Jinja2 Environment: отдельный от Django templates (не {% load %}, а чистый Jinja2)

**Доставка в Telegram (DLV-01, DLV-04, DLV-05, DLV-06)**
- Celery-таск `deliver_telegram(report_id)`:
  1. Загрузить AuditReport + Submission + ClientProfile
  2. Создать DeliveryLog(report=report, channel='telegram', status='queued')
  3. Отправить сопроводительный текст: «Спасибо за обращение! Ваш аудит-отчёт готов.» (DLV-06)
  4. Скачать PDF из MinIO (presigned URL → requests.get → bytes)
  5. Отправить через Telegram Bot API `sendDocument` (multipart/form-data с bytes)
  6. При успехе: `DeliveryLog.status = 'delivered'`, `DeliveryLog.external_id = message_id`
  7. Вызвать FSM `submission.mark_delivered()` + save (если оба канала доставлены)
- Retry: `autoretry_for=(RequestException,)`, `max_retries=5`, `retry_backoff=True` (DLV-05)

**Доставка в WhatsApp через Wazzup24 (DLV-02, DLV-03, DLV-05, DLV-06)**
- Абстракция `WhatsAppProvider` с методом `send_document(phone, file_url, caption)` (DLV-03)
- Реализация `Wazzup24Provider`:
  - API: `POST https://api.wazzup24.com/v3/message` с `channelId`, `chatId` (phone), `contentUri` (file URL), `text`
  - Авторизация: `Bearer {WAZZUP24_API_KEY}` header
  - `chatId` = `client.phone_wa` (WhatsApp номер из онбординга)
  - Ответ: `messageId` → сохранить в `DeliveryLog.external_id`
- Celery-таск `deliver_whatsapp(report_id)`:
  1. Создать DeliveryLog(report=report, channel='whatsapp', status='queued')
  2. Отправить сопроводительный текст + PDF через Wazzup24Provider
  3. При успехе: `DeliveryLog.status = 'delivered'`
  4. Retry аналогично Telegram (DLV-05)

**Оркестрация задач**
- Триггер: API-эндпоинт `POST /api/v1/reports/{report_id}/approve/` (admin-only, session auth)
  - Устанавливает `report.status = 'approved'`, `report.approved_at = now()`
  - Вызывает FSM `submission.start_audit()` если ещё не вызван
  - Запускает Celery chain: `generate_pdf.s(report_id) | group(deliver_telegram.s(report_id), deliver_whatsapp.s(report_id))`
- Выбор: chain (рекомендуется — гарантирует порядок)

**FSM-переход mark_delivered**
- `mark_delivered()` вызывается после ОБОИХ каналов доставки
- Проверка: оба DeliveryLog (telegram + whatsapp) имеют `status = 'delivered'`
- Race condition: `select_for_update()` на Submission при вызове `mark_delivered()`

**Env-переменные**
- `WAZZUP24_API_KEY`, `WAZZUP24_CHANNEL_ID`, `TELEGRAM_BOT_TOKEN`, MinIO vars — уже в `.env.example`

### Claude's Discretion
- Точный дизайн PDF-шаблона (отступы, шрифты, размер текста)
- Формат presigned URL (path vs query params)
- Точные тексты сопроводительных сообщений
- Структура Jinja2 контекста (какие поля передать в шаблон)
- Обработка edge case: клиент без WhatsApp-номера (skip WA delivery)
- Exact retry timing (backoff factor)

### Deferred Ideas (OUT OF SCOPE)
- Email-канал доставки — v2 (EMAIL-01)
- Автоматические возвраты — out of scope
- AI-предварительный анализ ответов — v2 (AI-01)
- Watermark на PDF — не обсуждалось
- PDF preview в браузере — Phase 7 CRM
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PDF-01 | Jinja2-шаблон Ashıde 1 (7–9 параметров, короткий отчёт) | Jinja2 3.1.5 уже transitive dep WeasyPrint; шаблон создаётся в `backend/templates/pdf/` |
| PDF-02 | Jinja2-шаблон Ashıde 2 (18–24 параметра, расширенный отчёт) | Один шаблон с условными секциями `{% if tariff_code == 'ashide_2' %}` |
| PDF-03 | WeasyPrint рендерит PDF в фирменном стиле с Cyrillic-шрифтами | WeasyPrint 68.1 в pyproject.toml; Cyrillic fonts (fonts-liberation, fonts-roboto) в Dockerfile ✓ |
| PDF-04 | Имя клиента и название компании подставляются в заголовок и на обложку | ClientProfile.name + ClientProfile.company доступны через Submission FK chain |
| PDF-05 | Сгенерированный PDF сохраняется в MinIO с presigned URL (TTL ≥ 7 дней) | boto3 + django-storages уже в стеке; AWS_QUERYSTRING_EXPIRE = 604800 уже в base.py |
| PDF-06 | Celery-воркер `--pool=prefork --max-tasks-per-child=5` для PDF | Уже настроен в docker-compose.yml worker command — ничего менять не надо |
| PDF-07 | Таск идемпотентен: проверка `AuditReport.pdf_url` перед генерацией | AuditReport.pdf_url URLField(blank=True) — проверка if report.pdf_url: return |
| DLV-01 | Отправка PDF в Telegram после подтверждения админа (sendDocument) | Telegram Bot API sendDocument = multipart POST; паттерн requests.post уже в tasks.py |
| DLV-02 | Отправка PDF в WhatsApp через Wazzup24 v3 API | POST /v3/message с contentUri = presigned URL; chatType='whatsapp'; Bearer auth |
| DLV-03 | Абстракция `WhatsAppProvider` с интерфейсом `send_document(phone, url, caption)` | ABC-паттерн; `delivery/providers/` директория |
| DLV-04 | `DeliveryLog` фиксирует `queued → delivered` для каждого канала | DeliveryLog модель уже создана с нужными статусами |
| DLV-05 | Retry через Celery при временных ошибках доставки (5xx, network) | `autoretry_for=(RequestException,)` + `retry_backoff=True` паттерн из payments tasks |
| DLV-06 | Сопроводительный текст «Спасибо за обращение» отправляется перед PDF | Два последовательных API-вызова: sendMessage (текст) + sendDocument (файл) |
</phase_requirements>

---

## Summary

Фаза 6 добавляет три связанных компонента: (1) Celery-таск генерации PDF через WeasyPrint + Jinja2 с сохранением в MinIO, (2) Celery-таск доставки в Telegram через Bot API sendDocument, (3) Celery-таск доставки в WhatsApp через Wazzup24 v3 API с абстракцией `WhatsAppProvider`. Все три таска связаны Celery chain/group с идемпотентностью на уровне `AuditReport.pdf_url`. Триггером служит новый API-эндпоинт `POST /api/v1/reports/{id}/approve/`.

Критично: все зависимости уже присутствуют в проекте. WeasyPrint 68.1 и Jinja2 3.1.5 установлены в virtualenv (Jinja2 как transitive dep WeasyPrint). Cyrillic-шрифты установлены в Docker-образе. boto3 + django-storages настроены для MinIO с `AWS_QUERYSTRING_EXPIRE = 604800` (7 дней). Celery worker уже запущен с `--pool=prefork --max-tasks-per-child=5`. Паттерн Celery-тасков с retry и Telegram API уже реализован в `submissions/tasks.py` — его нужно переиспользовать.

Единственная новая интеграция — Wazzup24 API. Wazzup24 принимает `POST /v3/message` с полями `channelId`, `chatId` (номер телефона), `chatType='whatsapp'`, `text`, `contentUri` (URL файла). Авторизация — `Bearer {WAZZUP24_API_KEY}`. Idempotency через `crmMessageId`. Поскольку MinIO presigned URLs публично доступны (по signature), их можно передавать напрямую в `contentUri` без скачивания файла на стороне сервера.

**Primary recommendation:** Следовать архитектуре, закреплённой в CONTEXT.md. Все технические блоки подтверждены — никаких блокеров для планирования нет.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| WeasyPrint | 68.1 (installed) | HTML → PDF rendering | Уже в pyproject.toml; Cyrillic через системные шрифты Pango/HarfBuzz |
| Jinja2 | 3.1.5 (transitive dep) | HTML-шаблон для PDF | Transitive dep WeasyPrint; чистые шаблоны без Django template tags |
| boto3 | >=1.35 (installed) | MinIO S3 API — upload, presigned URL | Уже в стеке через django-storages |
| celery | 5.6.3 (installed) | Async task queue — generate, deliver | Уже в стеке; worker с prefork настроен |
| requests | stdlib (installed) | HTTP calls — Telegram API, Wazzup24 API | Уже используется в submissions/tasks.py |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| django-storages[s3] | 1.14.6 (installed) | S3/MinIO django backend | Уже настроен в settings — для DefaultStorage |
| python-abc | stdlib | WhatsAppProvider abstract base | Для интерфейса провайдера |

### Not Needed (Already In Stack)
Jinja2 не нужно добавлять в pyproject.toml — он уже transitive dep WeasyPrint и присутствует в venv.

**Installation:** ничего нового не нужно устанавливать. Все зависимости уже в pyproject.toml.

**Version verification (confirmed 2026-04-17):**
- weasyprint: 68.1 (в pyproject.toml, pip show подтверждён)
- jinja2: 3.1.5 (pip show подтверждён как transitive dep weasyprint)
- celery: 5.6.3 (в pyproject.toml)
- boto3: >=1.35 (в pyproject.toml)

---

## Architecture Patterns

### Recommended Project Structure

```
backend/
├── apps/
│   ├── reports/
│   │   ├── models.py           # AuditReport (уже есть)
│   │   ├── views.py            # НОВОЕ: ApproveReportView
│   │   ├── serializers.py      # НОВОЕ: AuditReportSerializer
│   │   ├── urls.py             # НОВОЕ: path('<uuid:report_id>/approve/')
│   │   ├── services.py         # НОВОЕ: PDFGenerationService (Jinja2 + WeasyPrint + MinIO)
│   │   └── tasks.py            # НОВОЕ: generate_pdf task
│   └── delivery/
│       ├── models.py           # DeliveryLog (уже есть)
│       ├── providers/          # НОВОЕ: директория
│       │   ├── __init__.py
│       │   ├── base.py         # НОВОЕ: WhatsAppProvider ABC
│       │   └── wazzup24.py     # НОВОЕ: Wazzup24Provider
│       └── tasks.py            # НОВОЕ: deliver_telegram, deliver_whatsapp
├── templates/
│   └── pdf/                    # НОВОЕ: директория
│       ├── audit_report.html   # НОВОЕ: Jinja2 шаблон
│       └── styles.css          # НОВОЕ: CSS для PDF
```

### Pattern 1: Celery Chain для гарантированного порядка

**What:** `generate_pdf.s(report_id) | group(deliver_telegram.s(report_id), deliver_whatsapp.s(report_id))` — цепочка гарантирует, что PDF существует перед доставкой.

**When to use:** Всегда. deliver_* тасков не нужно стартовать до завершения generate_pdf.

```python
# Source: decisions from 06-CONTEXT.md + Celery docs pattern
from celery import chain, group
from apps.reports.tasks import generate_pdf
from apps.delivery.tasks import deliver_telegram, deliver_whatsapp

workflow = chain(
    generate_pdf.s(str(report.id)),
    group(
        deliver_telegram.s(str(report.id)),
        deliver_whatsapp.s(str(report.id)),
    )
)
workflow.delay()
```

### Pattern 2: generate_pdf Celery-таск с идемпотентностью

```python
# Source: established pattern from submissions/tasks.py + 06-CONTEXT.md
from celery import shared_task
from io import BytesIO
import boto3, logging
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from django.conf import settings
from django.utils import timezone

log = logging.getLogger(__name__)

@shared_task(
    name="reports.generate_pdf",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def generate_pdf(self, report_id: str):
    from apps.reports.models import AuditReport
    report = AuditReport.objects.select_related(
        "submission__client__industry",
        "submission__tariff",
    ).get(id=report_id)

    # Идемпотентность: уже сгенерирован
    if report.pdf_url:
        log.info("generate_pdf: already generated for report=%s, skipping", report_id)
        return

    # Рендеринг Jinja2
    env = Environment(
        loader=FileSystemLoader(str(settings.BASE_DIR / "templates" / "pdf")),
        autoescape=True,
    )
    template = env.get_template("audit_report.html")
    answers = list(report.submission.answers.select_related("question").order_by("question__order"))
    html_str = template.render(
        report=report,
        submission=report.submission,
        client=report.submission.client,
        tariff=report.submission.tariff,
        answers=answers,
        generated_at=timezone.now(),
    )

    # WeasyPrint → BytesIO
    pdf_bytes = HTML(string=html_str).write_pdf()

    # Upload to MinIO
    s3 = boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    timestamp = int(timezone.now().timestamp())
    key = f"pdfs/{report.submission_id}/{timestamp}.pdf"
    s3.put_object(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=key,
        Body=pdf_bytes,
        ContentType="application/pdf",
    )
    presigned_url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": key},
        ExpiresIn=settings.AWS_QUERYSTRING_EXPIRE,  # 604800 = 7 дней
    )
    report.pdf_url = presigned_url
    report.status = AuditReport.Status.APPROVED
    report.approved_at = timezone.now()
    report.save(update_fields=["pdf_url", "status", "approved_at"])
    log.info("generate_pdf: PDF generated for report=%s key=%s", report_id, key)
```

### Pattern 3: deliver_telegram Celery-таск

```python
# Source: reuse of submissions/tasks.py Telegram pattern + CONTEXT.md decisions
import os
import requests
from celery import shared_task
from requests.exceptions import RequestException

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

@shared_task(
    name="delivery.deliver_telegram",
    bind=True,
    autoretry_for=(RequestException,),
    max_retries=5,
    retry_backoff=True,
    retry_backoff_max=300,
)
def deliver_telegram(self, report_id: str):
    from apps.reports.models import AuditReport
    from apps.delivery.models import DeliveryLog

    report = AuditReport.objects.select_related("submission__client").get(id=report_id)
    log_entry, _ = DeliveryLog.objects.get_or_create(
        report=report,
        channel=DeliveryLog.Channel.TELEGRAM,
        defaults={"status": DeliveryLog.Status.QUEUED},
    )

    telegram_id = report.submission.client.telegram_id

    # 1. Сопроводительный текст (DLV-06)
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": telegram_id, "text": "Спасибо за обращение! Ваш аудит-отчёт готов."},
        timeout=10,
    ).raise_for_status()

    # 2. Скачать PDF и отправить как файл (sendDocument multipart)
    pdf_bytes = requests.get(report.pdf_url, timeout=30).content
    resp = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
        data={"chat_id": telegram_id},
        files={"document": ("audit_report.pdf", pdf_bytes, "application/pdf")},
        timeout=30,
    )
    resp.raise_for_status()
    message_id = resp.json()["result"]["message_id"]

    log_entry.status = DeliveryLog.Status.DELIVERED
    log_entry.external_id = str(message_id)
    log_entry.save(update_fields=["status", "external_id"])

    _try_mark_delivered(report)
```

### Pattern 4: WhatsAppProvider абстракция (DLV-03)

```python
# Source: 06-CONTEXT.md + ABC pattern
from abc import ABC, abstractmethod

class WhatsAppProvider(ABC):
    @abstractmethod
    def send_document(self, phone: str, file_url: str, caption: str) -> str:
        """Send document to WhatsApp. Returns external message ID."""
        ...


class Wazzup24Provider(WhatsAppProvider):
    BASE_URL = "https://api.wazzup24.com/v3/message"

    def __init__(self, api_key: str, channel_id: str):
        self.api_key = api_key
        self.channel_id = channel_id

    def send_document(self, phone: str, file_url: str, caption: str) -> str:
        import requests
        resp = requests.post(
            self.BASE_URL,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={
                "channelId": self.channel_id,
                "chatId": phone,
                "chatType": "whatsapp",
                "text": caption,
                "contentUri": file_url,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("messageId", "")
```

### Pattern 5: mark_delivered с race condition protection

```python
# Source: 06-CONTEXT.md + Phase 04 select_for_update pattern
from django.db import transaction

def _try_mark_delivered(report):
    """Check if both channels delivered; if so, transition FSM to delivered."""
    from apps.delivery.models import DeliveryLog
    from apps.submissions.models import Submission

    delivered_channels = set(
        DeliveryLog.objects.filter(
            report=report,
            status=DeliveryLog.Status.DELIVERED,
        ).values_list("channel", flat=True)
    )
    required = {DeliveryLog.Channel.TELEGRAM, DeliveryLog.Channel.WHATSAPP}
    if not required.issubset(delivered_channels):
        return

    with transaction.atomic():
        sub = Submission.objects.select_for_update().get(pk=report.submission_id)
        if sub.status == Submission.Status.UNDER_AUDIT:
            sub.mark_delivered()
            sub.save(update_fields=["status"])
```

### Pattern 6: ApproveReportView (API-эндпоинт триггер)

```python
# Source: 06-CONTEXT.md decisions + Phase 02 session-auth pattern
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.utils import timezone
from celery import chain, group

class ApproveReportView(APIView):
    permission_classes = [IsAdminUser]  # session auth — only staff

    def post(self, request, report_id):
        from apps.reports.models import AuditReport
        from apps.reports.tasks import generate_pdf
        from apps.delivery.tasks import deliver_telegram, deliver_whatsapp

        report = AuditReport.objects.select_related("submission").get(id=report_id)

        # FSM: completed → under_audit (idempotent guard)
        sub = report.submission
        if sub.status == sub.Status.COMPLETED:
            sub.start_audit()
            sub.save(update_fields=["status"])

        # Mark report as approved
        if not report.approved_at:
            report.approved_at = timezone.now()
            report.save(update_fields=["approved_at"])

        # Launch Celery pipeline
        workflow = chain(
            generate_pdf.s(str(report.id)),
            group(
                deliver_telegram.s(str(report.id)),
                deliver_whatsapp.s(str(report.id)),
            )
        )
        workflow.delay()

        return Response({"status": "queued"})
```

### Anti-Patterns to Avoid

- **Django template backend для PDF:** Использовать `jinja2.Environment(FileSystemLoader(...))` напрямую, НЕ Django's `{% load %}` / `render_to_string()`. WeasyPrint требует чистый HTML без Django template escape-логики.
- **Запись PDF на диск:** Всегда `BytesIO` / `write_pdf()` → bytes в памяти, затем прямо в S3. Никаких временных файлов в `/tmp` — на воркере с `max-tasks-per-child=5` они не будут убраны вовремя.
- **Singleton boto3 клиент на уровне модуля:** Создавать `boto3.client(...)` внутри таска, не на уровне модуля — воркеры prefork форкают процессы, shared клиент ломается.
- **deliver_* без generate_pdf:** Никогда не вызывать deliver_* напрямую без проверки `report.pdf_url` — файла в MinIO ещё нет.
- **Wazzup24 upload файла:** Wazzup24 v3 принимает `contentUri` (URL) напрямую — не нужно скачивать PDF и загружать его в Wazzup24. Presigned URL MinIO публично доступен по HMAC-подписи — передавать его в `contentUri`.
- **FSM mark_delivered без select_for_update:** Два deliver-таска могут гонять к `mark_delivered()` одновременно. Всегда оборачивать в `transaction.atomic() + select_for_update()`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PDF рендеринг | Кастомный HTML→PDF конвертер | WeasyPrint 68.1 (уже установлен) | Pango/HarfBuzz для Cyrillic, CSS float, page-break |
| Jinja2 шаблоны | Django template для PDF | `jinja2.Environment(FileSystemLoader(...))` | Чистые шаблоны без Django-specific теги |
| S3 upload | Кастомный multipart upload | `boto3.client.put_object()` + `generate_presigned_url()` | Retry, HMAC, multipart — всё внутри boto3 |
| Task retry логика | Кастомный retry-loop | `autoretry_for=`, `retry_backoff=True` в Celery | Exponential backoff, jitter — встроено в Celery |
| Telegram file отправка | Кастомный multipart builder | `requests.post(..., files={...})` | requests обрабатывает multipart/form-data |

**Key insight:** WeasyPrint + Jinja2 — единственный корректный путь для Cyrillic PDF в Python без внешних сервисов. Альтернативы (xhtml2pdf, reportlab) не поддерживают Pango/HarfBuzz шрифты так же надёжно.

---

## Common Pitfalls

### Pitfall 1: WeasyPrint memory leak в Celery воркере
**What goes wrong:** WeasyPrint 68+ использует Cairo/Pango для рендеринга и накапливает память внутри C-extension. После 5–10 задач воркер съедает >500MB.
**Why it happens:** Pango font cache не освобождается между задачами в одном процессе.
**How to avoid:** `--max-tasks-per-child=5` уже настроен в docker-compose.yml — НЕ убирать это значение. При рендеринге создавать `jinja2.Environment` внутри таска, не на уровне модуля.
**Warning signs:** OOMKilled в docker logs worker; celery stats показывают растущую RSS у воркеров.

### Pitfall 2: Presigned URL истекает до доставки
**What goes wrong:** По умолчанию `AWS_QUERYSTRING_EXPIRE = 604800` (7 дней). Если deliver_* вызван сразу (chain), URL действителен. Но если retry занял >7 дней — URL истёк.
**Why it happens:** Presigned URL не обновляется сам.
**How to avoid:** В deliver_telegram скачивать PDF (`requests.get(report.pdf_url)`) сразу после начала таска — если URL истёк, получить `403` → retry → к этому времени нужно регенерировать URL. Альтернатива: в `_try_deliver_*` проверять TTL и при необходимости генерировать новый presigned URL из существующего S3 key.
**Warning signs:** `403 Forbidden` при `requests.get(report.pdf_url)` в логах deliver_telegram.

### Pitfall 3: Jinja2 autoescape ломает HTML
**What goes wrong:** `autoescape=True` в Jinja2 Environment эскейпит HTML-теги в `admin_text`, превращая `<br>` в `&lt;br&gt;`.
**Why it happens:** `admin_text` содержит форматирование от AdminCRM.
**How to avoid:** Использовать `{{ admin_text | safe }}` в шаблоне для полей, которые содержат доверенный HTML. Либо `autoescape=False` + ручное экранирование где нужно.
**Warning signs:** PDF содержит буквальный `&lt;p&gt;` вместо отрендеренных абзацев.

### Pitfall 4: DeliveryLog дублирование при retry
**What goes wrong:** При retry таск создаёт второй `DeliveryLog` с тем же channel, что приводит к дублям в БД и некорректной проверке `_try_mark_delivered`.
**Why it happens:** `DeliveryLog.objects.create(...)` без idempotency guard вызывается повторно.
**How to avoid:** Использовать `get_or_create(report=report, channel=channel, defaults={"status": "queued"})`. Уже указано в CONTEXT.md.
**Warning signs:** `report.deliveries.count()` > 2 для одного отчёта.

### Pitfall 5: Wazzup24 contentUri требует публично доступный URL
**What goes wrong:** MinIO в dev-окружении слушает `http://minio:9000` — это внутренний Docker hostname, недоступный для Wazzup24.
**Why it happens:** Presigned URL генерируется с `endpoint_url=http://minio:9000`.
**How to avoid:** В dev/test deliver_whatsapp мокировать Wazzup24Provider. В prod использовать внешний `MINIO_ENDPOINT_URL` (например `https://storage.baqsy.kz`). Добавить `MINIO_PUBLIC_URL` env var для presigned URL generation в prod.
**Warning signs:** Wazzup24 возвращает ошибку доступа к файлу; PDF получен в Telegram но не в WhatsApp.

### Pitfall 6: FSM race condition mark_delivered
**What goes wrong:** deliver_telegram и deliver_whatsapp завершаются одновременно. Оба читают DeliveryLog, оба видят 2 delivered, оба вызывают `mark_delivered()`. Django-fsm бросает `TransitionNotAllowed` на втором вызове.
**Why it happens:** Нет блокировки между тасками.
**How to avoid:** `select_for_update()` на Submission + проверка текущего status перед transition. Уже описано в CONTEXT.md и Pattern 5.
**Warning signs:** `TransitionNotAllowed: mark_delivered is not allowed in state delivered` в Celery logs.

### Pitfall 7: boto3 клиент создан на уровне модуля (prefork fork-safety)
**What goes wrong:** `s3 = boto3.client(...)` на уровне модуля инициализируется в родительском процессе. После fork дочерние воркеры разделяют сокеты → `BrokenPipeError` или некорректные ответы S3.
**Why it happens:** Prefork pool форкает Python процессы; HTTP-соединения не fork-safe.
**How to avoid:** Всегда создавать `boto3.client(...)` внутри функции таска.
**Warning signs:** Случайные `ConnectionResetError` при upload в MinIO в воркере.

---

## Code Examples

### WeasyPrint HTML → PDF bytes (verified pattern)

```python
# Source: WeasyPrint 68.x official docs + Medium/dantebytes verified pattern
from io import BytesIO
from weasyprint import HTML

html_string = "<html><body><h1>Аудит-отчёт</h1></body></html>"
pdf_bytes = HTML(string=html_string).write_pdf()
# pdf_bytes — bytes объект, готов к upload
```

### Jinja2 Environment для PDF-шаблонов

```python
# Source: jinja2 official docs; отдельный Environment от Django templates
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

env = Environment(
    loader=FileSystemLoader(str(Path(settings.BASE_DIR) / "templates" / "pdf")),
    autoescape=True,  # autoescape для безопасности; использовать | safe для admin_text
)
template = env.get_template("audit_report.html")
html_str = template.render(
    client_name="Иван Иванов",
    company="ООО Ромашка",
    tariff_code="ashide_2",
    admin_text="<p>Текст аудита</p>",
    answers=[...],
)
```

### MinIO presigned URL generation (boto3)

```python
# Source: boto3 docs + settings.py confirmed config
import boto3

s3 = boto3.client(
    "s3",
    endpoint_url=settings.AWS_S3_ENDPOINT_URL,   # http://minio:9000 в dev
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    config=boto3.session.Config(signature_version="s3v4"),
)
s3.put_object(
    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
    Key=f"pdfs/{submission_id}/{timestamp}.pdf",
    Body=pdf_bytes,
    ContentType="application/pdf",
)
url = s3.generate_presigned_url(
    "get_object",
    Params={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": key},
    ExpiresIn=604800,  # 7 дней
)
```

### Telegram sendDocument (multipart)

```python
# Source: Telegram Bot API docs + reuse of submissions/tasks.py pattern
import requests

resp = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
    data={"chat_id": telegram_id},
    files={"document": ("audit_report.pdf", pdf_bytes, "application/pdf")},
    timeout=30,
)
resp.raise_for_status()
message_id = resp.json()["result"]["message_id"]
```

### Wazzup24 send document via contentUri

```python
# Source: Wazzup24 API v3 docs (verified via WebSearch 2026-04-17)
import requests

resp = requests.post(
    "https://api.wazzup24.com/v3/message",
    headers={
        "Authorization": f"Bearer {WAZZUP24_API_KEY}",
        "Content-Type": "application/json",
    },
    json={
        "channelId": WAZZUP24_CHANNEL_ID,
        "chatId": client_phone,         # номер WhatsApp из ClientProfile.phone_wa
        "chatType": "whatsapp",
        "text": "Спасибо за обращение! Ваш аудит-отчёт готов.",
        "contentUri": presigned_pdf_url, # прямая ссылка на PDF в MinIO
        "crmMessageId": f"report-{report_id}",  # idempotency key
    },
    timeout=30,
)
resp.raise_for_status()
message_id = resp.json().get("messageId", "")
```

### Jinja2 audit_report.html — структура шаблона

```html
{# Source: 06-CONTEXT.md decisions — один шаблон с условными секциями #}
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <link rel="stylesheet" href="styles.css">
  <title>Аудит-отчёт — {{ client.company }}</title>
</head>
<body>
  <!-- ОБЛОЖКА -->
  <div class="cover-page">
    <h1>Бизнес-Аудит</h1>
    <h2>{{ client.company }}</h2>
    <p class="client-name">{{ client.name }}</p>
    <p class="industry">{{ client.industry.name }}</p>
    <p class="tariff">{{ tariff.title }}</p>
    <p class="date">{{ generated_at.strftime('%d.%m.%Y') }}</p>
  </div>

  <!-- ТЕКСТ АУДИТА -->
  <div class="audit-section">
    {{ report.admin_text | safe }}
  </div>

  <!-- ASHIDE 1: 7–9 параметров -->
  <div class="answers-section">
    {% for answer in answers %}
      {% if loop.index <= 9 %}
        <div class="answer-item">
          <strong>{{ answer.question.text }}</strong>
          <p>{{ answer.value | tojson }}</p>
        </div>
      {% endif %}
    {% endfor %}
  </div>

  <!-- ASHIDE 2: дополнительные параметры -->
  {% if tariff.code == 'ashide_2' %}
  <div class="extended-section">
    {% for answer in answers %}
      {% if loop.index > 9 %}
        <div class="answer-item">
          <strong>{{ answer.question.text }}</strong>
          <p>{{ answer.value | tojson }}</p>
        </div>
      {% endif %}
    {% endfor %}
  </div>
  {% endif %}
</body>
</html>
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| xhtml2pdf (reportlab) | WeasyPrint | ~2020+ | Полная поддержка CSS3 + Cyrillic через системные шрифты |
| Загрузка файла в Wazzup24 | contentUri (URL-ссылка) | Wazzup24 v3 | Не нужно скачивать и загружать PDF — передаётся presigned URL напрямую |
| Wazzup24 v2 API | Wazzup24 v3 API | 2023+ | Другие поля запроса; v2 deprecated |
| Запись PDF в /tmp | BytesIO в памяти | Best practice | Нет I/O overhead; совместимо с prefork без дискового мусора |
| Отдельный воркер для PDF | prefork pool с `max-tasks-per-child` | WeasyPrint pitfall | Защита от memory leak без отдельного процесса |

**Deprecated/outdated:**
- `weasyprint.HTML(filename=...)` с записью в файл: использовать `HTML(string=...).write_pdf()` → bytes
- Wazzup24 v2 API (`/v2/send`): заменён на `/v3/message`

---

## Open Questions

1. **Wazzup24 contentUri с внутренним MinIO URL в dev-окружении**
   - Что знаем: В dev `MINIO_ENDPOINT_URL=http://minio:9000` — недоступен снаружи Docker сети
   - Что неясно: Нет `MINIO_PUBLIC_URL` env var для генерации presigned URLs с внешним hostname
   - Recommendation: В `deliver_whatsapp` таске — при тестировании мокировать Wazzup24Provider через `unittest.mock`. В prod добавить `MINIO_PUBLIC_URL` в `.env.example` и использовать его при генерации presigned URL для WA-доставки.

2. **Jinja2 autoescape и `admin_text` с HTML-разметкой**
   - Что знаем: `admin_text` — TextField, admin вводит текст в CRM (Phase 7). Формат пока не определён.
   - Что неясно: Будет ли admin_text содержать HTML-теги или plain text?
   - Recommendation: Использовать `{{ report.admin_text | safe }}` для допустимости HTML; документировать это в CRM Phase 7.

3. **`phone_wa` формат для Wazzup24 chatId**
   - Что знаем: `ClientProfile.phone_wa = CharField(max_length=20, blank=True)` — может быть пустым
   - Что неясно: Wazzup24 принимает `chatId` как E.164 (`+77001234567`) или без `+` (`77001234567`)?
   - Recommendation: В `Wazzup24Provider.send_document` нормализовать: убрать `+` если есть, передавать как `77001234567`. Если `phone_wa` пуст — skip WA delivery (создать DeliveryLog со статусом `failed` + error='no_phone').

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3 + pytest-django 4.9 |
| Config file | `backend/pyproject.toml` → `[tool.pytest.ini_options]` |
| Quick run command | `docker-compose exec web pytest apps/reports/ apps/delivery/ -x` |
| Full suite command | `docker-compose exec web pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PDF-01 | Jinja2 шаблон рендерится для ashide_1 | unit | `pytest apps/reports/tests/test_tasks.py::test_generate_pdf_ashide1 -x` | ❌ Wave 0 |
| PDF-02 | Jinja2 шаблон рендерится для ashide_2 с доп. секциями | unit | `pytest apps/reports/tests/test_tasks.py::test_generate_pdf_ashide2 -x` | ❌ Wave 0 |
| PDF-03 | WeasyPrint возвращает bytes начинающиеся с %PDF | unit | `pytest apps/reports/tests/test_tasks.py::test_pdf_bytes_format -x` | ❌ Wave 0 |
| PDF-04 | PDF-контекст содержит имя клиента и компанию | unit | `pytest apps/reports/tests/test_tasks.py::test_pdf_context_client_data -x` | ❌ Wave 0 |
| PDF-05 | pdf_url сохраняется в AuditReport.pdf_url | integration | `pytest apps/reports/tests/test_tasks.py::test_generate_pdf_saves_url -x` | ❌ Wave 0 |
| PDF-06 | Воркер config prefork max-tasks-per-child=5 | manual | docker-compose config проверка | — |
| PDF-07 | Повторный вызов generate_pdf не создаёт новый PDF | unit | `pytest apps/reports/tests/test_tasks.py::test_generate_pdf_idempotent -x` | ❌ Wave 0 |
| DLV-01 | deliver_telegram вызывает sendDocument | unit (mock) | `pytest apps/delivery/tests/test_tasks.py::test_deliver_telegram_calls_api -x` | ❌ Wave 0 |
| DLV-02 | deliver_whatsapp вызывает Wazzup24Provider.send_document | unit (mock) | `pytest apps/delivery/tests/test_tasks.py::test_deliver_whatsapp_calls_provider -x` | ❌ Wave 0 |
| DLV-03 | WhatsAppProvider ABC не инстанциируется напрямую | unit | `pytest apps/delivery/tests/test_providers.py::test_abstract_provider -x` | ❌ Wave 0 |
| DLV-04 | DeliveryLog статус queued→delivered после успеха | integration | `pytest apps/delivery/tests/test_tasks.py::test_delivery_log_status_update -x` | ❌ Wave 0 |
| DLV-05 | Retry при RequestException | unit (mock) | `pytest apps/delivery/tests/test_tasks.py::test_deliver_retries_on_network_error -x` | ❌ Wave 0 |
| DLV-06 | Сопроводительный текст отправляется перед PDF | unit (mock) | `pytest apps/delivery/tests/test_tasks.py::test_deliver_telegram_sends_text_first -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `docker-compose exec web pytest apps/reports/ apps/delivery/ -x`
- **Per wave merge:** `docker-compose exec web pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `backend/apps/reports/tests/test_tasks.py` — covers PDF-01..PDF-07
- [ ] `backend/apps/delivery/tests/test_tasks.py` — covers DLV-01, DLV-02, DLV-04, DLV-05, DLV-06
- [ ] `backend/apps/delivery/tests/test_providers.py` — covers DLV-03
- [ ] `backend/apps/reports/tests/test_views.py` — covers ApproveReportView (API endpoint)
- [ ] `backend/templates/pdf/` директория — нужна для шаблона
- [ ] Jinja2 не нужно добавлять в pyproject.toml (уже transitive dep)

---

## Sources

### Primary (HIGH confidence)
- Codebase direct inspection — `backend/pyproject.toml` (WeasyPrint 68.1, Jinja2 3.1.5, celery 5.6.3, boto3 >=1.35)
- `backend/Dockerfile` — Cyrillic fonts confirmed: fonts-liberation, fonts-roboto, fonts-dejavu-core
- `backend/baqsy/settings/base.py` — MinIO config: `AWS_QUERYSTRING_EXPIRE = 604800`; S3 addressing style path; boto3 configured
- `docker/docker-compose.yml` — worker command: `--pool=prefork --max-tasks-per-child=5` confirmed
- `backend/apps/submissions/tasks.py` — Telegram API pattern, Celery retry pattern, established code to reuse
- `backend/apps/reports/models.py` — AuditReport fields confirmed
- `backend/apps/delivery/models.py` — DeliveryLog fields + statuses confirmed
- `backend/apps/submissions/models.py` — FSM transitions confirmed: start_audit(), mark_delivered()

### Secondary (MEDIUM confidence)
- Wazzup24 API v3 — WebSearch verified: POST `/v3/message`, fields `channelId`, `chatId`, `chatType`, `text`, `contentUri`, `crmMessageId`; Bearer auth; returns `messageId`. Official docs returned 403, verified via multiple search results including cached documentation.
- WeasyPrint + Jinja2 integration pattern — verified via multiple independent sources (Medium, Josh Karamuth blog, dantebytes.com)

### Tertiary (LOW confidence)
- Wazzup24 `chatId` format (E.164 vs без `+`) — не подтверждено официальной документацией из-за 403; нужно проверить при интеграционном тестировании

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — все зависимости подтверждены прямым чтением pyproject.toml, Dockerfile, settings.py
- Architecture: HIGH — паттерны из существующего кода (tasks.py, models.py); Celery chain/group стандартный паттерн
- Pitfalls: HIGH — WeasyPrint memory leak, prefork fork-safety, presigned URL expiry — подтверждены через multiple sources
- Wazzup24 API: MEDIUM — основные поля подтверждены, chatId формат и точный response schema требуют проверки при интеграции

**Research date:** 2026-04-17
**Valid until:** 2026-05-17 (стабильный стек; Wazzup24 API может меняться быстрее)
