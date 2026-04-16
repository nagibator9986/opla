---
phase: 01-infrastructure-data-model
plan: 02
type: execute
wave: 1
title: "App skeletons and all 13 data models"
depends_on: [00]
requirements: [DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06, DATA-07, DATA-08, DATA-09, DATA-10, DATA-11, DATA-12, DATA-13]
autonomous: true
files_modified:
  - backend/apps/__init__.py
  - backend/apps/core/__init__.py
  - backend/apps/core/apps.py
  - backend/apps/core/models.py
  - backend/apps/accounts/__init__.py
  - backend/apps/accounts/apps.py
  - backend/apps/accounts/models.py
  - backend/apps/accounts/managers.py
  - backend/apps/accounts/admin.py
  - backend/apps/industries/__init__.py
  - backend/apps/industries/apps.py
  - backend/apps/industries/models.py
  - backend/apps/industries/admin.py
  - backend/apps/submissions/__init__.py
  - backend/apps/submissions/apps.py
  - backend/apps/submissions/models.py
  - backend/apps/submissions/admin.py
  - backend/apps/payments/__init__.py
  - backend/apps/payments/apps.py
  - backend/apps/payments/models.py
  - backend/apps/payments/admin.py
  - backend/apps/reports/__init__.py
  - backend/apps/reports/apps.py
  - backend/apps/reports/models.py
  - backend/apps/reports/admin.py
  - backend/apps/delivery/__init__.py
  - backend/apps/delivery/apps.py
  - backend/apps/delivery/models.py
  - backend/apps/delivery/admin.py
  - backend/apps/content/__init__.py
  - backend/apps/content/apps.py
  - backend/apps/content/models.py
  - backend/apps/content/admin.py
nyquist_compliant: true
---

# Plan 02: App Skeletons and All 13 Data Models

## Goal

Create all 8 Django apps (core, accounts, industries, submissions, payments, reports, delivery, content) with their models, including the two critical invariants: QuestionnaireTemplate versioning and Submission.template_id immutability. All migrations generated and verified.

## must_haves

- All 13 models exist in schema after `migrate`
- `QuestionnaireTemplate.create_new_version()` atomically creates new version and deactivates old
- Partial unique constraint ensures exactly one active template per industry
- `Submission.template_id` cannot be changed after initial save — raises `ValidationError`
- `Payment.transaction_id` has unique constraint for webhook idempotency
- All models registered in Django Admin

## Tasks

<task id="02-01">
<title>Create apps/core with abstract base models</title>
<read_first>
- .planning/phases/01-infrastructure-data-model/01-CONTEXT.md
- .planning/phases/01-infrastructure-data-model/01-RESEARCH.md
</read_first>
<action>
Create directory structure:
```
backend/apps/__init__.py          (empty)
backend/apps/core/__init__.py     (empty)
backend/apps/core/apps.py         (CoreConfig, name="apps.core")
backend/apps/core/models.py
```

In `backend/apps/core/models.py`:

```python
import uuid
from django.db import models


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True
```

In `backend/apps/core/apps.py`:
```python
from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Core"
```
</action>
<acceptance_criteria>
- `backend/apps/core/models.py` contains `class TimestampedModel(models.Model):`
- `backend/apps/core/models.py` contains `class UUIDModel(models.Model):`
- `backend/apps/core/models.py` contains `id = models.UUIDField(primary_key=True, default=uuid.uuid4`
- `backend/apps/core/apps.py` contains `name = "apps.core"`
</acceptance_criteria>
</task>

<task id="02-02">
<title>Create apps/accounts with BaseUser and ClientProfile</title>
<read_first>
- .planning/phases/01-infrastructure-data-model/01-RESEARCH.md (Pattern: Custom User model)
- backend/apps/core/models.py
</read_first>
<action>
Create directory structure:
```
backend/apps/accounts/__init__.py
backend/apps/accounts/apps.py
backend/apps/accounts/managers.py
backend/apps/accounts/models.py
backend/apps/accounts/admin.py
```

In `backend/apps/accounts/managers.py`:
```python
from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, password, **extra_fields)
```

In `backend/apps/accounts/models.py`:
```python
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from apps.core.models import TimestampedModel
from apps.accounts.managers import UserManager


class BaseUser(AbstractBaseUser, PermissionsMixin, TimestampedModel):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Администратор"
        verbose_name_plural = "Администраторы"

    def __str__(self):
        return self.email


class ClientProfile(TimestampedModel):
    telegram_id = models.BigIntegerField(unique=True)
    name = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    phone_wa = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100, blank=True)
    industry = models.ForeignKey(
        "industries.Industry",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clients",
    )

    class Meta:
        verbose_name = "Профиль клиента"
        verbose_name_plural = "Профили клиентов"

    def __str__(self):
        return f"{self.name} ({self.company})"
```

In `backend/apps/accounts/admin.py`:
```python
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.accounts.models import BaseUser, ClientProfile


@admin.register(BaseUser)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = ("email", "first_name", "last_name", "is_staff", "is_active")
    search_fields = ("email", "first_name", "last_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal", {"fields": ("first_name", "last_name")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),
    )


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "telegram_id", "city", "industry")
    search_fields = ("name", "company", "telegram_id")
    list_filter = ("industry", "city")
```

In `backend/apps/accounts/apps.py`:
```python
from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    verbose_name = "Accounts"
```

IMPORTANT: Ensure `AUTH_USER_MODEL = "accounts.BaseUser"` is set in settings/base.py (this should be done in Plan 01 — verify it exists).
</action>
<acceptance_criteria>
- `backend/apps/accounts/models.py` contains `class BaseUser(AbstractBaseUser, PermissionsMixin, TimestampedModel):`
- `backend/apps/accounts/models.py` contains `USERNAME_FIELD = "email"`
- `backend/apps/accounts/models.py` contains `class ClientProfile(TimestampedModel):`
- `backend/apps/accounts/models.py` contains `telegram_id = models.BigIntegerField(unique=True)`
- `backend/apps/accounts/managers.py` contains `class UserManager(BaseUserManager):`
- `backend/apps/accounts/admin.py` contains `@admin.register(BaseUser)`
- `backend/apps/accounts/admin.py` contains `@admin.register(ClientProfile)`
</acceptance_criteria>
</task>

<task id="02-03">
<title>Create apps/industries with Industry, QuestionnaireTemplate, Question</title>
<read_first>
- .planning/phases/01-infrastructure-data-model/01-RESEARCH.md (Pattern: QuestionnaireTemplate versioning)
- .planning/phases/01-infrastructure-data-model/01-CONTEXT.md (versioning decisions)
- backend/apps/core/models.py
</read_first>
<action>
Create directory structure:
```
backend/apps/industries/__init__.py
backend/apps/industries/apps.py
backend/apps/industries/models.py
backend/apps/industries/admin.py
```

In `backend/apps/industries/models.py`:
```python
from django.db import models, transaction
from django.core.exceptions import ValidationError

from apps.core.models import TimestampedModel


class Industry(TimestampedModel):
    name = models.CharField(max_length=100)
    code = models.SlugField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Отрасль"
        verbose_name_plural = "Отрасли"
        ordering = ["name"]

    def __str__(self):
        return self.name


class QuestionnaireTemplate(TimestampedModel):
    industry = models.ForeignKey(
        Industry,
        on_delete=models.CASCADE,
        related_name="templates",
    )
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    name = models.CharField(max_length=255)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Шаблон анкеты"
        verbose_name_plural = "Шаблоны анкет"
        unique_together = [("industry", "version")]
        constraints = [
            models.UniqueConstraint(
                fields=["industry"],
                condition=models.Q(is_active=True),
                name="one_active_template_per_industry",
            )
        ]
        ordering = ["industry", "-version"]

    def __str__(self):
        return f"{self.industry.name} v{self.version}"

    @classmethod
    def create_new_version(cls, old_template):
        """Atomically create a new template version cloning questions from the old one."""
        with transaction.atomic():
            old = cls.objects.select_for_update().get(pk=old_template.pk)
            old_questions = list(old.questions.all())

            new_version = cls.objects.create(
                industry=old.industry,
                version=old.version + 1,
                is_active=True,
                name=old.name,
            )

            old.is_active = False
            old.save(update_fields=["is_active"])

            for q in old_questions:
                Question.objects.create(
                    template=new_version,
                    order=q.order,
                    text=q.text,
                    field_type=q.field_type,
                    options=q.options,
                    required=q.required,
                    block=q.block,
                )

            return new_version


class Question(TimestampedModel):
    class FieldType(models.TextChoices):
        TEXT = "text", "Текст"
        NUMBER = "number", "Число"
        CHOICE = "choice", "Выбор одного"
        MULTICHOICE = "multichoice", "Множественный выбор"

    class Block(models.TextChoices):
        A = "A", "Блок А — Технический паспорт"
        B = "B", "Блок Б — Содержательная часть"
        C = "C", "Блок В — Глубокое сканирование"

    template = models.ForeignKey(
        QuestionnaireTemplate,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    order = models.PositiveIntegerField()
    text = models.TextField()
    field_type = models.CharField(max_length=20, choices=FieldType.choices, default=FieldType.TEXT)
    options = models.JSONField(default=dict, blank=True, help_text="Options for choice/multichoice fields")
    required = models.BooleanField(default=True)
    block = models.CharField(max_length=1, choices=Block.choices, default=Block.A)

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
        ordering = ["template", "order"]
        unique_together = [("template", "order")]

    def __str__(self):
        return f"Q{self.order}: {self.text[:50]}"
```

In `backend/apps/industries/admin.py`:
```python
from django.contrib import admin
from apps.industries.models import Industry, QuestionnaireTemplate, Question


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    ordering = ["order"]


@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active")
    search_fields = ("name", "code")
    prepopulated_fields = {"code": ("name",)}


@admin.register(QuestionnaireTemplate)
class QuestionnaireTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "industry", "version", "is_active", "published_at")
    list_filter = ("industry", "is_active")
    inlines = [QuestionInline]
    readonly_fields = ("version",)
```
</action>
<acceptance_criteria>
- `backend/apps/industries/models.py` contains `class Industry(TimestampedModel):`
- `backend/apps/industries/models.py` contains `class QuestionnaireTemplate(TimestampedModel):`
- `backend/apps/industries/models.py` contains `name="one_active_template_per_industry"`
- `backend/apps/industries/models.py` contains `def create_new_version(cls, old_template):`
- `backend/apps/industries/models.py` contains `class Question(TimestampedModel):`
- `backend/apps/industries/models.py` contains `class FieldType(models.TextChoices):`
- `backend/apps/industries/models.py` contains `options = models.JSONField(`
- `backend/apps/industries/admin.py` contains `class QuestionInline(admin.TabularInline):`
</acceptance_criteria>
</task>

<task id="02-04">
<title>Create apps/submissions with Submission (FSM + immutability) and Answer</title>
<read_first>
- .planning/phases/01-infrastructure-data-model/01-RESEARCH.md (Pattern: Submission immutability, django-fsm-2)
- .planning/phases/01-infrastructure-data-model/01-CONTEXT.md (FSM states)
- backend/apps/core/models.py
- backend/apps/industries/models.py
</read_first>
<action>
Create directory structure:
```
backend/apps/submissions/__init__.py
backend/apps/submissions/apps.py
backend/apps/submissions/models.py
backend/apps/submissions/admin.py
```

In `backend/apps/submissions/models.py`:
```python
from django.core.exceptions import ValidationError
from django.db import models
from django_fsm import FSMField, transition

from apps.core.models import TimestampedModel, UUIDModel


class Submission(UUIDModel, TimestampedModel):
    class Status(models.TextChoices):
        CREATED = "created", "Создан"
        IN_PROGRESS_BASIC = "in_progress_basic", "Базовый онбординг"
        PAID = "paid", "Оплачен"
        IN_PROGRESS_FULL = "in_progress_full", "Заполнение анкеты"
        COMPLETED = "completed", "Анкета завершена"
        UNDER_AUDIT = "under_audit", "На аудите"
        DELIVERED = "delivered", "Доставлен"

    client = models.ForeignKey(
        "accounts.ClientProfile",
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    template = models.ForeignKey(
        "industries.QuestionnaireTemplate",
        on_delete=models.PROTECT,
        related_name="submissions",
    )
    tariff = models.ForeignKey(
        "payments.Tariff",
        on_delete=models.PROTECT,
        related_name="submissions",
        null=True,
        blank=True,
    )
    status = FSMField(default=Status.CREATED, choices=Status.choices)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ["-created_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_template_id = self.template_id

    def save(self, *args, **kwargs):
        if self.pk and self._original_template_id is not None:
            if self.template_id != self._original_template_id:
                raise ValidationError(
                    "Нельзя изменить шаблон анкеты после создания заказа."
                )
        super().save(*args, **kwargs)
        self._original_template_id = self.template_id

    def __str__(self):
        return f"Заказ {self.id} ({self.client})"

    # FSM transitions
    @transition(field=status, source=Status.CREATED, target=Status.IN_PROGRESS_BASIC)
    def start_onboarding(self):
        pass

    @transition(field=status, source=Status.IN_PROGRESS_BASIC, target=Status.PAID)
    def mark_paid(self):
        pass

    @transition(field=status, source=Status.PAID, target=Status.IN_PROGRESS_FULL)
    def start_questionnaire(self):
        pass

    @transition(field=status, source=Status.IN_PROGRESS_FULL, target=Status.COMPLETED)
    def complete_questionnaire(self):
        from django.utils import timezone
        self.completed_at = timezone.now()

    @transition(field=status, source=Status.COMPLETED, target=Status.UNDER_AUDIT)
    def start_audit(self):
        pass

    @transition(field=status, source=Status.UNDER_AUDIT, target=Status.DELIVERED)
    def mark_delivered(self):
        pass


class Answer(TimestampedModel):
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    question = models.ForeignKey(
        "industries.Question",
        on_delete=models.PROTECT,
        related_name="answers",
    )
    value = models.JSONField(help_text="Answer data: {text: ''} or {number: N} or {choice: ''} or {choices: []}")
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ответ"
        verbose_name_plural = "Ответы"
        unique_together = [("submission", "question")]
        ordering = ["question__order"]

    def __str__(self):
        return f"Ответ на Q{self.question.order} ({self.submission_id})"
```

In `backend/apps/submissions/admin.py`:
```python
from django.contrib import admin
from apps.submissions.models import Submission, Answer


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ("question", "value", "answered_at")


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "template", "tariff", "status", "created_at")
    list_filter = ("status", "tariff", "template__industry")
    search_fields = ("client__name", "client__company")
    readonly_fields = ("id", "template", "created_at")
    inlines = [AnswerInline]
```
</action>
<acceptance_criteria>
- `backend/apps/submissions/models.py` contains `class Submission(UUIDModel, TimestampedModel):`
- `backend/apps/submissions/models.py` contains `status = FSMField(default=Status.CREATED`
- `backend/apps/submissions/models.py` contains `self._original_template_id = self.template_id`
- `backend/apps/submissions/models.py` contains `raise ValidationError`
- `backend/apps/submissions/models.py` contains `@transition(field=status`
- `backend/apps/submissions/models.py` contains `class Answer(TimestampedModel):`
- `backend/apps/submissions/models.py` contains `value = models.JSONField(`
- `backend/apps/submissions/models.py` contains `unique_together = [("submission", "question")]`
</acceptance_criteria>
</task>

<task id="02-05">
<title>Create apps/payments with Tariff and Payment</title>
<read_first>
- .planning/phases/01-infrastructure-data-model/01-CONTEXT.md
- backend/apps/core/models.py
</read_first>
<action>
Create directory structure:
```
backend/apps/payments/__init__.py
backend/apps/payments/apps.py
backend/apps/payments/models.py
backend/apps/payments/admin.py
```

In `backend/apps/payments/models.py`:
```python
from django.db import models

from apps.core.models import TimestampedModel, UUIDModel


class Tariff(TimestampedModel):
    code = models.SlugField(max_length=50, unique=True)
    title = models.CharField(max_length=255)
    price_kzt = models.DecimalField(max_digits=10, decimal_places=0, help_text="Цена в тенге")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Тариф"
        verbose_name_plural = "Тарифы"
        ordering = ["price_kzt"]

    def __str__(self):
        return f"{self.title} ({self.price_kzt} ₸)"


class Payment(UUIDModel, TimestampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Ожидание"
        SUCCEEDED = "succeeded", "Успешно"
        FAILED = "failed", "Ошибка"
        REFUNDED = "refunded", "Возврат"

    submission = models.ForeignKey(
        "submissions.Submission",
        on_delete=models.CASCADE,
        related_name="payments",
    )
    tariff = models.ForeignKey(
        Tariff,
        on_delete=models.PROTECT,
        related_name="payments",
    )
    transaction_id = models.CharField(max_length=255, unique=True, help_text="CloudPayments TransactionId")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    amount = models.DecimalField(max_digits=10, decimal_places=0)
    currency = models.CharField(max_length=3, default="KZT")
    raw_webhook = models.JSONField(default=dict, blank=True, help_text="Raw CloudPayments webhook payload")

    class Meta:
        verbose_name = "Платёж"
        verbose_name_plural = "Платежи"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment {self.transaction_id} ({self.status})"
```

In `backend/apps/payments/admin.py`:
```python
from django.contrib import admin
from apps.payments.models import Tariff, Payment


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    list_display = ("title", "code", "price_kzt", "is_active")
    list_editable = ("price_kzt", "is_active")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("transaction_id", "submission", "tariff", "amount", "status", "created_at")
    list_filter = ("status", "tariff")
    readonly_fields = ("transaction_id", "raw_webhook")
```
</action>
<acceptance_criteria>
- `backend/apps/payments/models.py` contains `class Tariff(TimestampedModel):`
- `backend/apps/payments/models.py` contains `price_kzt = models.DecimalField(`
- `backend/apps/payments/models.py` contains `class Payment(UUIDModel, TimestampedModel):`
- `backend/apps/payments/models.py` contains `transaction_id = models.CharField(max_length=255, unique=True`
- `backend/apps/payments/models.py` contains `raw_webhook = models.JSONField(`
- `backend/apps/payments/admin.py` contains `list_editable = ("price_kzt", "is_active")`
</acceptance_criteria>
</task>

<task id="02-06">
<title>Create apps/reports, apps/delivery, apps/content</title>
<read_first>
- .planning/phases/01-infrastructure-data-model/01-CONTEXT.md
- backend/apps/core/models.py
</read_first>
<action>
Create 3 apps with their models:

**apps/reports/models.py:**
```python
from django.db import models
from apps.core.models import TimestampedModel


class AuditReport(TimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        APPROVED = "approved", "Утверждён"
        SENT = "sent", "Отправлен"

    submission = models.OneToOneField(
        "submissions.Submission",
        on_delete=models.CASCADE,
        related_name="report",
    )
    admin_text = models.TextField(blank=True, help_text="Текст аудита от администратора")
    pdf_url = models.URLField(blank=True, help_text="MinIO presigned URL to PDF")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Аудит-отчёт"
        verbose_name_plural = "Аудит-отчёты"

    def __str__(self):
        return f"Report for {self.submission_id} ({self.status})"
```

**apps/delivery/models.py:**
```python
from django.db import models
from apps.core.models import TimestampedModel


class DeliveryLog(TimestampedModel):
    class Channel(models.TextChoices):
        TELEGRAM = "telegram", "Telegram"
        WHATSAPP = "whatsapp", "WhatsApp"

    class Status(models.TextChoices):
        QUEUED = "queued", "В очереди"
        SENT = "sent", "Отправлено"
        DELIVERED = "delivered", "Доставлено"
        FAILED = "failed", "Ошибка"

    report = models.ForeignKey(
        "reports.AuditReport",
        on_delete=models.CASCADE,
        related_name="deliveries",
    )
    channel = models.CharField(max_length=20, choices=Channel.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    external_id = models.CharField(max_length=255, blank=True, help_text="External message/delivery ID")
    error = models.TextField(blank=True)

    class Meta:
        verbose_name = "Лог доставки"
        verbose_name_plural = "Логи доставки"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.channel} → {self.status} ({self.report_id})"
```

**apps/content/models.py:**
```python
from django.db import models
from apps.core.models import TimestampedModel


class ContentBlock(TimestampedModel):
    class ContentType(models.TextChoices):
        TEXT = "text", "Текст"
        HTML = "html", "HTML"

    key = models.SlugField(max_length=100, unique=True, help_text="Unique block identifier, e.g. 'hero_title'")
    title = models.CharField(max_length=255, help_text="Human-readable label for admin")
    content = models.TextField(blank=True)
    content_type = models.CharField(max_length=10, choices=ContentType.choices, default=ContentType.TEXT)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Контент-блок"
        verbose_name_plural = "Контент-блоки"
        ordering = ["key"]

    def __str__(self):
        return f"{self.title} ({self.key})"
```

For each app create:
- `__init__.py` (empty)
- `apps.py` with `AppConfig(name="apps.reports"/"apps.delivery"/"apps.content")`
- `admin.py` with `@admin.register` for each model (basic list_display, list_filter, search_fields)
</action>
<acceptance_criteria>
- `backend/apps/reports/models.py` contains `class AuditReport(TimestampedModel):`
- `backend/apps/reports/models.py` contains `submission = models.OneToOneField(`
- `backend/apps/delivery/models.py` contains `class DeliveryLog(TimestampedModel):`
- `backend/apps/delivery/models.py` contains `class Channel(models.TextChoices):`
- `backend/apps/content/models.py` contains `class ContentBlock(TimestampedModel):`
- `backend/apps/content/models.py` contains `key = models.SlugField(max_length=100, unique=True`
- `backend/apps/reports/admin.py` contains `@admin.register(AuditReport)`
- `backend/apps/delivery/admin.py` contains `@admin.register(DeliveryLog)`
- `backend/apps/content/admin.py` contains `@admin.register(ContentBlock)`
</acceptance_criteria>
</task>

<task id="02-07">
<title>Generate and verify all migrations</title>
<read_first>
- backend/baqsy/settings/base.py (INSTALLED_APPS must include all 8 apps)
</read_first>
<action>
Ensure `INSTALLED_APPS` in `backend/baqsy/settings/base.py` includes:
```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 3rd party
    "django_fsm",
    "corsheaders",
    # project apps
    "apps.core",
    "apps.accounts",
    "apps.industries",
    "apps.submissions",
    "apps.payments",
    "apps.reports",
    "apps.delivery",
    "apps.content",
]
```

Also ensure `AUTH_USER_MODEL = "accounts.BaseUser"` is in base.py.

Run: `python manage.py makemigrations` for each app.
Run: `python manage.py migrate` to verify all migrations apply cleanly.
Run: `python manage.py check --deploy` (with dev settings) to verify no issues.
</action>
<acceptance_criteria>
- `backend/baqsy/settings/base.py` contains `"apps.core"`
- `backend/baqsy/settings/base.py` contains `"apps.accounts"`
- `backend/baqsy/settings/base.py` contains `"apps.industries"`
- `backend/baqsy/settings/base.py` contains `"apps.submissions"`
- `backend/baqsy/settings/base.py` contains `"apps.payments"`
- `backend/baqsy/settings/base.py` contains `"apps.reports"`
- `backend/baqsy/settings/base.py` contains `"apps.delivery"`
- `backend/baqsy/settings/base.py` contains `"apps.content"`
- `backend/baqsy/settings/base.py` contains `AUTH_USER_MODEL = "accounts.BaseUser"`
- `python manage.py migrate --check` exits 0
- `python manage.py check` exits 0
</acceptance_criteria>
</task>

<task id="02-08">
<title>Write model tests: creation, versioning invariant, immutability invariant</title>
<read_first>
- backend/apps/industries/models.py (create_new_version)
- backend/apps/submissions/models.py (save override)
- .planning/phases/01-infrastructure-data-model/01-VALIDATION.md (test map)
</read_first>
<action>
Replace xfail stubs (from Wave 0) with real tests. Key tests:

**apps/industries/tests/test_versioning.py:**
```python
import pytest
from apps.industries.models import Industry, QuestionnaireTemplate, Question

@pytest.mark.django_db
def test_create_new_version_deactivates_old():
    industry = Industry.objects.create(name="Test", code="test")
    t1 = QuestionnaireTemplate.objects.create(industry=industry, version=1, is_active=True, name="T")
    Question.objects.create(template=t1, order=1, text="Q1", field_type="text", block="A")
    
    t2 = QuestionnaireTemplate.create_new_version(t1)
    
    t1.refresh_from_db()
    assert t1.is_active is False
    assert t2.is_active is True
    assert t2.version == 2
    assert t2.questions.count() == 1

@pytest.mark.django_db
def test_only_one_active_per_industry_constraint():
    from django.db import IntegrityError
    industry = Industry.objects.create(name="Test2", code="test2")
    QuestionnaireTemplate.objects.create(industry=industry, version=1, is_active=True, name="T1")
    with pytest.raises(IntegrityError):
        QuestionnaireTemplate.objects.create(industry=industry, version=2, is_active=True, name="T2")
```

**apps/submissions/tests/test_immutability.py:**
```python
import pytest
from django.core.exceptions import ValidationError
from apps.accounts.models import ClientProfile
from apps.industries.models import Industry, QuestionnaireTemplate
from apps.submissions.models import Submission

@pytest.mark.django_db
def test_submission_template_id_cannot_change():
    industry = Industry.objects.create(name="Retail", code="retail")
    t1 = QuestionnaireTemplate.objects.create(industry=industry, version=1, is_active=True, name="R1")
    t2 = QuestionnaireTemplate.objects.create(industry=Industry.objects.create(name="IT", code="it"), version=1, is_active=True, name="IT1")
    client = ClientProfile.objects.create(telegram_id=12345, name="Test", company="TestCo")
    sub = Submission.objects.create(client=client, template=t1)
    
    sub.template = t2
    with pytest.raises(ValidationError, match="Нельзя изменить шаблон"):
        sub.save()
```

**apps/payments/tests/test_models.py:**
```python
import pytest
from django.db import IntegrityError

@pytest.mark.django_db
def test_payment_unique_transaction_id(submission_factory):
    from apps.payments.models import Tariff, Payment
    tariff = Tariff.objects.create(code="t1", title="Test", price_kzt=1000)
    # Create submission via factory or manually
    # Then test unique constraint on transaction_id
    # Payment.objects.create(submission=sub, tariff=tariff, transaction_id="TX1", amount=1000)
    # with pytest.raises(IntegrityError):
    #     Payment.objects.create(submission=sub, tariff=tariff, transaction_id="TX1", amount=1000)
```

Add basic creation tests for each model (Industry, Question, ClientProfile, Answer, Tariff, AuditReport, DeliveryLog, ContentBlock) in their respective test files.
</action>
<acceptance_criteria>
- `backend/apps/industries/tests/test_versioning.py` contains `def test_create_new_version_deactivates_old`
- `backend/apps/industries/tests/test_versioning.py` contains `def test_only_one_active_per_industry_constraint`
- `backend/apps/submissions/tests/test_immutability.py` contains `def test_submission_template_id_cannot_change`
- `pytest apps/industries/tests/test_versioning.py -x` exits 0
- `pytest apps/submissions/tests/test_immutability.py -x` exits 0
</acceptance_criteria>
</task>

## Verification

After all tasks complete:
```bash
python manage.py migrate --check    # all migrations applied
python manage.py check              # no issues
pytest apps/ -x -q                  # all model tests pass
```
