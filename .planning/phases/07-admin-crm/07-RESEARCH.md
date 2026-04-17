# Phase 7: Admin CRM - Research

**Researched:** 2026-04-17
**Domain:** Django Admin customization — django-unfold, django-axes, django-admin-sortable2, django-ckeditor-5, HTMX dashboard, custom changeform actions
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **CRM-платформа:** Django Admin с кастомизацией через django-unfold (современный UI). Отдельный React CRM избыточен. Session-auth уже настроена.
- **Дашборд (CRM-01, CRM-02):** Кастомная admin index page с числовыми карточками. Фильтры без перезагрузки (AJAX/HTMX). Без графиков — только числовые карточки.
- **Список и карточка заказа (CRM-03, CRM-04):** Стандартный admin list + кастомная change_form. Левая колонка ответы (read-only), правая — textarea аудита. Кнопка «Подтвердить и отправить» вызывает ApproveReportView (уже реализован Phase 6).
- **Industry CRUD (CRM-05):** Стандартный Django admin (уже есть, допилить).
- **QuestionnaireTemplate (CRM-06):** Кнопка «Создать новую версию» + auto-create при сохранении. Старые версии read-only.
- **Question drag-n-drop (CRM-07):** django-admin-sortable2.
- **Тарифы (CRM-08):** list_editable для цены и is_active.
- **Контент-блоки (CRM-09):** django-ckeditor-5 WYSIWYG для content поля.
- **Защита входа (CRM-10):** django-axes, AXES_FAILURE_LIMIT=10, AXES_COOLOFF_TIME=timedelta(hours=1).

### Claude's Discretion

- Точный выбор django-unfold theme/colors (в рамках «солидного» стиля)
- Layout деталей карточки заказа (точные размеры колонок)
- CKEditor toolbar configuration
- Dashboard card styling и responsive breakpoints
- Exact HTMX integration approach для фильтрации дашборда
- Admin site header/title text

### Deferred Ideas (OUT OF SCOPE)

- Экспорт статистики в CSV/Excel (ANALYTICS-01)
- OAuth для админов Google Workspace (SSO-01)
- Графики и визуализация трендов
- PDF preview в карточке заказа перед отправкой
- Уведомления админа в Telegram о новых заказах
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CRM-01 | Dashboard со счётчиками: всего заказов, в работе, завершённых, выручка за период | django-unfold DASHBOARD_CALLBACK + Django ORM aggregate queries |
| CRM-02 | Фильтры дашборда: отрасль, регион, тариф, дата — без перезагрузки | HTMX GET + Django view returning partial HTML fragment |
| CRM-03 | Список заказов с поиском и сортировкой по статусу | SubmissionAdmin list_display/list_filter/search_fields — уже частично готов |
| CRM-04 | Карточка заказа: ответы клиента слева, поле аудита справа, кнопка «Подтвердить и отправить» | unfold actions_detail + @action decorator + JS confirm + ApproveReportView |
| CRM-05 | Редактор отраслей (CRUD) | IndustryAdmin — уже готов, минимальные изменения |
| CRM-06 | Редактор шаблонов анкет: новая версия при изменении, история | QuestionnaireTemplateAdmin переопределить save_model + readonly для неактивных |
| CRM-07 | Редактор вопросов drag-n-drop, типы полей, обязательность | django-admin-sortable2 SortableInlineAdminMixin на QuestionInline |
| CRM-08 | Редактор тарифов (цена, описание, активность) | TariffAdmin list_editable — уже готов |
| CRM-09 | Редактор контент-блоков лендинга (WYSIWYG) | django-ckeditor-5 CKEditor5Widget через formfield_overrides |
| CRM-10 | Вход по email+пароль с защитой от брутфорса | django-axes 8.x INSTALLED_APPS + MIDDLEWARE + AUTHENTICATION_BACKENDS |
</phase_requirements>

---

## Summary

Phase 7 надстраивает уже существующие базовые ModelAdmin-регистрации (9+ admin.py файлов готовы) современным UI через django-unfold 0.90.0, добавляет функциональные блоки: кастомный дашборд с HTMX-фильтрацией, кастомную карточку заказа с кнопкой одобрения, drag-n-drop порядок вопросов (django-admin-sortable2), WYSIWYG для контент-блоков (django-ckeditor-5) и brute-force защиту входа (django-axes 8.3.1).

Ключевое: все модели уже зарегистрированы с базовыми ModelAdmin. Работа — это кастомизация, а не создание с нуля. ApproveReportView уже реализован в Phase 6 и принимает `POST /api/v1/reports/{id}/approve/` от staff-пользователей. Кнопка в карточке должна просто вызвать этот endpoint через JS (с confirm-диалогом).

HTMX — минималистичный выбор для фильтрации дашборда: он включается одним `<script>` тегом в кастомном шаблоне, не требует отдельной зависимости Python, и позволяет частичный re-render карточек без reload страницы.

**Primary recommendation:** Установить четыре пакета (django-unfold, django-axes, django-admin-sortable2, django-ckeditor-5), переписать все admin.py наследуясь от `unfold.admin.ModelAdmin`, создать `dashboard_callback` для счётчиков, добавить HTMX в шаблон дашборда, и настроить django-axes в middleware/backends.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| django-unfold | 0.90.0 | Современный Tailwind-based UI поверх Django admin | Активно поддерживается (релиз 16 апр 2026), поддержка Django 5–6, не заменяет admin — надстраивает |
| django-axes | 8.3.1 | Brute-force защита login endpoint | Jazzband-проект, поддержка Django 4.2/5.2/6.0, релиз фев 2026 |
| django-admin-sortable2 | 2.2.8 | Drag-n-drop порядок объектов в admin list и inlines | SortableJS-основа, поддержка Django 4.2/5.0+, TabularInline support |
| django-ckeditor-5 | 0.2.20 | WYSIWYG редактор для ContentBlock.content | Релиз фев 2026, поддержка Django 4.2/5.2/6.0, CKEditor5Widget для ModelAdmin |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| htmx | 2.x (CDN) | AJAX-фильтрация дашборда без JS-фреймворка | Подключается через `<script>` в кастомном шаблоне, не Python-пакет |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| django-unfold | django-jazzmin | Unfold активнее поддерживается, Tailwind-based, нет legacy jQuery |
| django-ckeditor-5 | django-tinymce | CKEditor5 современнее, BSD лицензия, лучше поддержка Django 5 |
| htmx (CDN) | Alpine.js + fetch | HTMX проще для server-rendered фрагментов, меньше кода |
| django-axes | django-ratelimit | axes специализирован на login brute-force + admin интерфейс для разблокировки |

**Installation:**
```bash
pip install django-unfold==0.90.0 django-axes==8.3.1 "django-admin-sortable2==2.2.8" "django-ckeditor-5==0.2.20"
```

---

## Architecture Patterns

### Recommended Project Structure

```
backend/
├── apps/
│   ├── dashboard/           # новый app — кастомный дашборд
│   │   ├── views.py         # dashboard_callback + DashboardStatsView (HTMX endpoint)
│   │   └── urls.py          # /admin/dashboard/stats/
│   ├── accounts/admin.py    # UserAdmin → unfold.admin.ModelAdmin
│   ├── submissions/admin.py # SubmissionAdmin — кастомная change_form + actions_detail
│   ├── industries/admin.py  # QuestionInline → SortableInlineAdminMixin
│   ├── reports/admin.py     # AuditReportAdmin + AuditReportInline в SubmissionAdmin
│   ├── content/admin.py     # ContentBlockAdmin + CKEditor5Widget
│   └── payments/admin.py    # TariffAdmin list_editable
├── templates/
│   └── admin/
│       └── index.html       # кастомный дашборд (extends admin/base_site.html)
└── baqsy/
    └── settings/
        └── base.py          # UNFOLD dict, AXES_*, CKEDITOR_5_CONFIGS
```

### Pattern 1: django-unfold INSTALLED_APPS порядок

**What:** unfold ДОЛЖЕН стоять перед `django.contrib.admin` в INSTALLED_APPS — иначе шаблоны django.contrib.admin перекрывают unfold-шаблоны.

**When to use:** Всегда при установке django-unfold.

**Example:**
```python
# Source: https://unfoldadmin.com/docs/configuration/settings/
INSTALLED_APPS = [
    "unfold",                          # FIRST — перед django.contrib.admin
    "unfold.contrib.filters",          # опционально: расширенные фильтры
    "unfold.contrib.forms",            # опционально: улучшенные виджеты форм
    "django.contrib.admin",
    # ... остальные apps
    "django_axes",
    "adminsortable2",
    "django_ckeditor_5",
    # ... наши apps
]
```

### Pattern 2: Переход на unfold.admin.ModelAdmin

**What:** Все существующие ModelAdmin должны наследоваться от `unfold.admin.ModelAdmin` вместо `django.contrib.admin.ModelAdmin`.

**When to use:** Для всех 9 admin.py файлов в проекте.

**Example:**
```python
# Source: https://unfoldadmin.com/blog/migrating-django-admin-unfold/
from unfold.admin import ModelAdmin, TabularInline  # заменить import

class AnswerInline(TabularInline):      # было: admin.TabularInline
    model = Answer
    extra = 0
    readonly_fields = ("question", "value", "answered_at")

@admin.register(Submission)
class SubmissionAdmin(ModelAdmin):      # было: admin.ModelAdmin
    # ... всё остальное без изменений
```

### Pattern 3: UNFOLD settings dict

**What:** Настройки django-unfold в settings.py через словарь `UNFOLD`.

**Example:**
```python
# Source: https://unfoldadmin.com/docs/configuration/settings/
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

UNFOLD = {
    "SITE_TITLE": "Baqsy CRM",
    "SITE_HEADER": "Baqsy System",
    "SITE_URL": "/",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "DASHBOARD_CALLBACK": "apps.dashboard.views.dashboard_callback",
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": _("Аналитика"),
                "items": [
                    {
                        "title": _("Дашборд"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": _("Заказы"),
                "items": [
                    {
                        "title": _("Заявки"),
                        "icon": "description",
                        "link": reverse_lazy("admin:submissions_submission_changelist"),
                    },
                    {
                        "title": _("Отчёты"),
                        "icon": "picture_as_pdf",
                        "link": reverse_lazy("admin:reports_auditreport_changelist"),
                    },
                ],
            },
            {
                "title": _("Контент"),
                "items": [
                    {
                        "title": _("Тарифы"),
                        "icon": "payments",
                        "link": reverse_lazy("admin:payments_tariff_changelist"),
                    },
                    {
                        "title": _("Блоки лендинга"),
                        "icon": "web",
                        "link": reverse_lazy("admin:content_contentblock_changelist"),
                    },
                ],
            },
            {
                "title": _("Конфигурация"),
                "items": [
                    {
                        "title": _("Отрасли"),
                        "icon": "category",
                        "link": reverse_lazy("admin:industries_industry_changelist"),
                    },
                    {
                        "title": _("Шаблоны анкет"),
                        "icon": "assignment",
                        "link": reverse_lazy("admin:industries_questionnairetemplate_changelist"),
                    },
                ],
            },
        ],
    },
}
```

### Pattern 4: DASHBOARD_CALLBACK с HTMX-фильтрацией

**What:** Кастомная index.html страница с карточками счётчиков и HTMX-фильтрами.

**When to use:** CRM-01, CRM-02.

**Example dashboard_callback:**
```python
# Source: https://unfoldadmin.com/docs/configuration/dashboard/
# apps/dashboard/views.py
from django.db.models import Sum, Q
from apps.submissions.models import Submission
from apps.payments.models import Payment

def dashboard_callback(request, context):
    """Inject dashboard stats into admin index template."""
    filters = _build_filters(request)
    qs_submissions = Submission.objects.filter(**filters)
    qs_payments = Payment.objects.filter(
        status="succeeded",
        submission__in=qs_submissions,
    )

    context.update({
        "stats": {
            "total": qs_submissions.count(),
            "in_progress": qs_submissions.filter(
                status__in=["in_progress", "completed", "under_audit"]
            ).count(),
            "delivered": qs_submissions.filter(status="delivered").count(),
            "revenue": qs_payments.aggregate(total=Sum("amount"))["total"] or 0,
        },
        "filter_industries": Industry.objects.filter(is_active=True),
        "filter_tariffs": Tariff.objects.filter(is_active=True),
        # активные фильтры для формы
        "active_filters": request.GET.dict(),
    })
    return context
```

**HTMX partial endpoint:**
```python
# apps/dashboard/views.py
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

@staff_member_required
def dashboard_stats_partial(request):
    """HTMX endpoint: returns only stats cards fragment."""
    context = dashboard_callback(request, {})
    return render(request, "admin/dashboard/_stats_cards.html", context)
```

**index.html с HTMX:**
```html
<!-- templates/admin/index.html -->
{% extends "unfold/layouts/base_simple.html" %}
{% block content %}
<form id="dashboard-filters"
      hx-get="{% url 'admin_dashboard_stats' %}"
      hx-target="#stats-cards"
      hx-trigger="change">
    <select name="industry">...</select>
    <select name="tariff">...</select>
    <input type="date" name="date_from">
    <input type="date" name="date_to">
</form>
<div id="stats-cards">
    {% include "admin/dashboard/_stats_cards.html" %}
</div>
<script src="https://unpkg.com/htmx.org@2.0.4"></script>
{% endblock %}
```

### Pattern 5: Кнопка «Подтвердить и отправить» в карточке заказа

**What:** unfold `actions_detail` + `@action` декоратор для кастомной кнопки в change_form. Кнопка POST-ит на ApproveReportView через JS.

**When to use:** CRM-04 — кнопка в карточке Submission/AuditReport.

**Example:**
```python
# Source: https://unfoldadmin.com/docs/actions/changeform/
from unfold.admin import ModelAdmin
from unfold.decorators import action
from django.http import HttpResponseRedirect
from django.contrib import messages
import requests

@admin.register(AuditReport)
class AuditReportAdmin(ModelAdmin):
    actions_detail = ["approve_and_send"]

    @action(
        description=_("Подтвердить и отправить"),
        url_path="approve",
    )
    def approve_and_send(self, request, object_id):
        report = AuditReport.objects.get(pk=object_id)
        # Сохранить admin_text если есть изменения
        # Вызвать ApproveReportView через внутренний вызов или requests
        from apps.reports.views import ApproveReportView
        view = ApproveReportView()
        response = view.post(request, report_id=object_id)
        if response.status_code == 200:
            messages.success(request, "Отчёт поставлен в очередь на генерацию и доставку.")
        else:
            messages.error(request, f"Ошибка: {response.data}")
        return HttpResponseRedirect(
            reverse("admin:reports_auditreport_change", args=(object_id,))
        )
```

**Важно:** Прямой вызов view внутри admin action — правильный паттерн (нет HTTP overhead, сохраняется request.user для IsAdminUser permission check).

### Pattern 6: django-admin-sortable2 для QuestionInline

**What:** SortableInlineAdminMixin на TabularInline добавляет drag-n-drop в inline строки.

**When to use:** CRM-07 — порядок вопросов в шаблоне анкеты.

**Example:**
```python
# Source: https://github.com/jrief/django-admin-sortable2
from adminsortable2.admin import SortableInlineAdminMixin
from unfold.admin import TabularInline, ModelAdmin

class QuestionInline(SortableInlineAdminMixin, TabularInline):
    model = Question
    extra = 0
    # SortableInlineAdminMixin использует поле `order` для сортировки
    # Question.order — IntegerField — уже существует в модели
```

**Требование к модели:** Поле для ordering должно быть в Question.order (уже есть в DATA-03).

**INSTALLED_APPS:**
```python
"adminsortable2",  # добавить в INSTALLED_APPS
```

### Pattern 7: django-ckeditor-5 для ContentBlock

**What:** CKEditor5Widget через formfield_overrides в ContentBlockAdmin.

**When to use:** CRM-09 — WYSIWYG для ContentBlock.content.

**Example:**
```python
# Source: https://pypi.org/project/django-ckeditor-5/
from django_ckeditor_5.widgets import CKEditor5Widget
from django.db import models
from unfold.admin import ModelAdmin

CKEDITOR_5_CONFIGS = {
    "content_block": {
        "toolbar": {
            "items": [
                "heading", "|",
                "bold", "italic", "underline", "|",
                "link", "bulletedList", "numberedList", "|",
                "blockQuote", "insertTable", "|",
                "undo", "redo",
            ]
        },
        "language": "ru",
    },
}

@admin.register(ContentBlock)
class ContentBlockAdmin(ModelAdmin):
    list_display = ("key", "title", "content_type", "is_active")
    list_filter = ("content_type", "is_active")
    search_fields = ("key", "title")
    list_editable = ("is_active",)
    formfield_overrides = {
        models.TextField: {
            "widget": CKEditor5Widget(config_name="content_block")
        }
    }
```

**settings.py:**
```python
INSTALLED_APPS = [
    ...
    "django_ckeditor_5",
]

CKEDITOR_5_CONFIGS = {
    "content_block": { ... }
}
```

### Pattern 8: django-axes конфигурация

**What:** INSTALLED_APPS + MIDDLEWARE (последним) + AUTHENTICATION_BACKENDS (первым) + settings.

**When to use:** CRM-10 — защита входа.

**Example:**
```python
# Source: https://django-axes.readthedocs.io/en/latest/2_installation.html

INSTALLED_APPS = [
    ...
    "axes",  # добавить
]

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",  # FIRST
    "django.contrib.auth.backends.ModelBackend",
]

MIDDLEWARE = [
    ...
    "axes.middleware.AxesMiddleware",  # LAST
]

# Конфигурация (per CONTEXT.md decisions)
AXES_FAILURE_LIMIT = 10
AXES_COOLOFF_TIME = timedelta(hours=1)
AXES_LOCKOUT_PARAMETERS = ["ip_address"]  # блокировка по IP
AXES_RESET_ON_SUCCESS = True  # сбросить счётчик при успешном входе
```

**Миграция:** После добавления `axes` в INSTALLED_APPS — обязательно `python manage.py migrate`.

### Pattern 9: QuestionnaireTemplate версионирование в admin save_model

**What:** При сохранении шаблона с изменёнными вопросами — создавать новую версию через `create_new_version()`.

**When to use:** CRM-06 — версионирование шаблонов.

**Example:**
```python
@admin.register(QuestionnaireTemplate)
class QuestionnaireTemplateAdmin(ModelAdmin):
    list_display = ("name", "industry", "version", "is_active", "published_at")
    list_filter = ("industry", "is_active")
    readonly_fields = ("version", "published_at")
    inlines = [QuestionInline]

    def save_model(self, request, obj, form, change):
        if change and obj.is_active:
            # При изменении активного шаблона — создать новую версию
            new_version = obj.create_new_version()
            # redirect на новую версию (через message + response override)
            self.message_user(
                request,
                f"Создана новая версия шаблона: v{new_version.version}",
                messages.SUCCESS,
            )
        else:
            super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        # Неактивные (архивные) шаблоны — только просмотр
        if obj and not obj.is_active:
            return False
        return super().has_change_permission(request, obj)
```

### Anti-Patterns to Avoid

- **Не размещать `unfold` ПОСЛЕ `django.contrib.admin`** — шаблоны не перекроются, UI останется стандартным.
- **Не пропускать `axes.middleware.AxesMiddleware` как последний middleware** — axes не будет перехватывать lockout responses.
- **Не забывать `AUTHENTICATION_BACKENDS` для axes** — без `AxesStandaloneBackend` as first backend, django-axes не блокирует вход.
- **Не вызывать `super().save_model()` при create_new_version** — иначе будет два сохранения и гонка версий.
- **Не ставить `django_ckeditor_5` до `unfold`** — возможны конфликты статических файлов.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Drag-n-drop order | Custom JS с fetch PATCH | django-admin-sortable2 | Edge cases: atomic reorder, bulk drag, undo — всё в библиотеке |
| Brute-force protection | Счётчик попыток в Redis | django-axes | GDPR compliance, admin UI для разблокировки, database-persistent |
| WYSIWYG editor | Textarea + JS-редактор вручную | django-ckeditor-5 | XSS sanitization, paste from Word, image upload — слишком сложно вручную |
| Admin UI modernization | Кастомные CSS поверх стандартного admin | django-unfold | Admin шаблоны изменятся в Django 6 — unfold абстрагирует |
| Dashboard stats refresh | Polling или WebSocket | HTMX hx-trigger=change | One-shot fetch при изменении фильтра — проще, нет постоянного соединения |

**Key insight:** Django admin кастомизация очень глубокая — писать custom admin widgets, drag-n-drop, WYSIWYG с нуля займёт 3–5x больше времени и создаст неподдерживаемый код.

---

## Common Pitfalls

### Pitfall 1: unfold INSTALLED_APPS порядок
**What goes wrong:** Django admin отображается в стандартном виде (без Tailwind UI).
**Why it happens:** `django.contrib.admin` загружает свои шаблоны раньше unfold.
**How to avoid:** `"unfold"` — ПЕРВЫЙ в INSTALLED_APPS, до `"django.contrib.admin"`.
**Warning signs:** Admin page не показывает unfold-сайдбар и Tailwind стили после установки.

### Pitfall 2: axes без AUTHENTICATION_BACKENDS
**What goes wrong:** django-axes устанавливается, мигрируется, но login не блокируется.
**Why it happens:** Django использует только ModelBackend, не вызывает AxesStandaloneBackend.
**How to avoid:** Добавить `AUTHENTICATION_BACKENDS` с `AxesStandaloneBackend` first.
**Warning signs:** `python manage.py check` может показать предупреждение об отсутствующем backend.

### Pitfall 3: axes Middleware не последний
**What goes wrong:** lockout response не возвращается (200 вместо 429 при превышении лимита).
**Why it happens:** AxesMiddleware должен быть последним, чтобы перехватить auth-failure.
**How to avoid:** `axes.middleware.AxesMiddleware` — последний элемент в MIDDLEWARE.

### Pitfall 4: adminsortable2 и INSTALLED_APPS
**What goes wrong:** `SortableInlineAdminMixin` работает, но JS не загружается (drag не работает).
**Why it happens:** `adminsortable2` не в INSTALLED_APPS → collectstatic не включает JS.
**How to avoid:** `"adminsortable2"` в INSTALLED_APPS + `python manage.py collectstatic`.

### Pitfall 5: axes run_on_test_only = False
**What goes wrong:** pytest-тесты начинают падать с 403 при тестировании admin login.
**Why it happens:** django-axes блокирует тестовые попытки входа.
**How to avoid:** В тестовых настройках добавить `AXES_ENABLED = False` или `AXES_HANDLER = "axes.handlers.dummy.AxesDummyHandler"`.

### Pitfall 6: CKEditor5 и collectstatic
**What goes wrong:** CKEditor не загружается в prod.
**Why it happens:** Django не собирает статику django-ckeditor-5 без `collectstatic`.
**How to avoid:** `"django_ckeditor_5"` в INSTALLED_APPS + `CKEDITOR_5_CONFIGS` в settings + `collectstatic` в entrypoint prod.

### Pitfall 7: ApproveReportView вызов из admin action
**What goes wrong:** `IsAdminUser` permission check падает — `request.user` не staff.
**Why it happens:** При прямом вызове view.post(request, ...) из admin action — request.user уже staff (из admin), поэтому должно работать. Проблема если action вызывается без авторизации.
**How to avoid:** Тест action через `self.client.post(...)` с staff-пользователем в тестах. Убедиться что `permission_classes = [IsAdminUser]` проверяет `request.user.is_staff`.

### Pitfall 8: save_model версионирование — двойное сохранение
**What goes wrong:** При `save_model` вызывается и `create_new_version()` и `super().save_model()` — создаются две записи или версия портится.
**Why it happens:** Разработчик вызывает super() после create_new_version().
**How to avoid:** В ветке `change and obj.is_active` — только `create_new_version()`, NOT `super().save_model()`. create_new_version сам делает save.

---

## Code Examples

### django-axes полная конфигурация settings.py
```python
# Source: https://pypi.org/project/django-axes/ + https://django-axes.readthedocs.io
from datetime import timedelta

# в INSTALLED_APPS
"axes",

# в MIDDLEWARE (последним)
"axes.middleware.AxesMiddleware",

# отдельный раздел settings
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AXES_ENABLED = True
AXES_FAILURE_LIMIT = 10
AXES_COOLOFF_TIME = timedelta(hours=1)
AXES_LOCKOUT_PARAMETERS = ["ip_address"]
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_CALLABLE = None  # использовать дефолтный HTTP 429
```

### django-admin-sortable2 — QuestionInline
```python
# Source: https://github.com/jrief/django-admin-sortable2
from adminsortable2.admin import SortableInlineAdminMixin
from unfold.admin import TabularInline, ModelAdmin

class QuestionInline(SortableInlineAdminMixin, TabularInline):
    model = Question
    extra = 0
    fields = ("order", "text", "field_type", "required", "block")
    # SortableInlineAdminMixin автоматически использует поле с именем 'order'
    # (или указать через default_order_field = 'order')
```

### unfold @action для approve_and_send
```python
# Source: https://unfoldadmin.com/docs/actions/changeform/
from unfold.admin import ModelAdmin
from unfold.decorators import action
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

@admin.register(AuditReport)
class AuditReportAdmin(ModelAdmin):
    actions_detail = ["approve_and_send"]

    @action(
        description=_("Подтвердить и отправить PDF"),
        url_path="approve",
    )
    def approve_and_send(self, request, object_id):
        from apps.reports.views import ApproveReportView
        view = ApproveReportView.as_view()
        # Прямой вызов с request.user уже staff (admin session)
        response = ApproveReportView().post(request, report_id=object_id)
        if hasattr(response, "status_code") and response.status_code == 200:
            messages.success(request, _("Отчёт поставлен в очередь на генерацию и доставку."))
        else:
            data = getattr(response, "data", {})
            messages.error(request, f"Ошибка: {data.get('error', 'неизвестная ошибка')}")
        return HttpResponseRedirect(
            reverse("admin:reports_auditreport_change", args=(object_id,))
        )
```

### Тест отключения axes в pytest settings
```python
# backend/baqsy/settings/test.py (или conftest.py override)
AXES_ENABLED = False
# или:
AXES_HANDLER = "axes.handlers.dummy.AxesDummyHandler"
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| django-jazzmin | django-unfold 0.90 | 2023–2026 | Unfold активно развивается, Tailwind-based, поддержка Django 6 |
| django-ckeditor (v4) | django-ckeditor-5 | 2022+ | django-ckeditor устарел, не поддерживает Django 5 |
| axes.backends.AxesBackend | axes.backends.AxesStandaloneBackend | axes 6.x+ | AxesStandaloneBackend не дублирует ModelBackend permissions |
| jQuery drag-n-drop | adminsortable2 с SortableJS | 2.x | jQuery удалён из Django admin в Django 4.x |

**Deprecated/outdated:**
- `django-ckeditor` (старая v4): не поддерживает Django 5, архивирован. Использовать `django-ckeditor-5`.
- `axes.backends.AxesBackend`: всё ещё работает, но `AxesStandaloneBackend` рекомендован для новых установок.
- `django-admin-sortable` (без цифры 2): устарел, заменён на `django-admin-sortable2`.

---

## Open Questions

1. **HTMX CDN vs static**
   - Что знаем: HTMX работает с CDN-ссылкой в template
   - Что неясно: Нужен ли pip/npm package или достаточно CDN в prod
   - Recommendation: Использовать CDN `https://unpkg.com/htmx.org@2.0.4` для простоты — нет Python-зависимости, малый размер, кэшируется браузером

2. **axes и test isolation**
   - Что знаем: django-axes пишет в БД при каждой неуспешной авторизации
   - Что неясно: Нужен ли отдельный test settings file или достаточно fixture
   - Recommendation: Добавить `AXES_ENABLED = False` в `baqsy/settings/test.py` (или создать его), refs существующий `DJANGO_SETTINGS_MODULE = "baqsy.settings.dev"` в pyproject.toml — вероятно нужен отдельный `test.py`

3. **unfold и django-admin-sortable2 совместимость**
   - Что знаем: Оба работают через monkey-patching шаблонов admin
   - Что неясно: Возможны конфликты шаблонов при совместном использовании
   - Recommendation: Протестировать вместе в Wave 0 — если конфликты, adminsortable2 имеет специальные unfold-совместимые классы или workaround через override template

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.3 + pytest-django 4.9 |
| Config file | `backend/pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `docker-compose exec web pytest apps/submissions/tests/ apps/reports/tests/ apps/industries/tests/ -x -q` |
| Full suite command | `docker-compose exec web pytest --tb=short` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CRM-01 | dashboard_callback возвращает корректные счётчики | unit | `pytest apps/dashboard/tests/test_dashboard.py::test_stats_counters -x` | ❌ Wave 0 |
| CRM-02 | DashboardStatsView (HTMX endpoint) фильтрует по industry/tariff/date | unit | `pytest apps/dashboard/tests/test_dashboard.py::test_filter_by_industry -x` | ❌ Wave 0 |
| CRM-03 | SubmissionAdmin list доступен staff-пользователю | smoke | `pytest apps/submissions/tests/test_admin.py::test_submission_list -x` | ❌ Wave 0 |
| CRM-04 | approve_and_send action вызывает ApproveReportView и возвращает redirect | unit | `pytest apps/reports/tests/test_admin.py::test_approve_action -x` | ❌ Wave 0 |
| CRM-05 | IndustryAdmin CRUD работает для staff | smoke | `pytest apps/industries/tests/test_admin.py::test_industry_crud -x` | ❌ Wave 0 |
| CRM-06 | Сохранение активного шаблона создаёт новую версию, старая деактивируется | unit | `pytest apps/industries/tests/test_admin.py::test_template_versioning_on_save -x` | ❌ Wave 0 |
| CRM-07 | QuestionInline имеет SortableInlineAdminMixin в MRO | unit | `pytest apps/industries/tests/test_admin.py::test_question_inline_sortable -x` | ❌ Wave 0 |
| CRM-08 | TariffAdmin list_editable price_kzt обновляет цену | unit | `pytest apps/payments/tests/test_admin.py::test_tariff_price_edit -x` | ❌ Wave 0 |
| CRM-09 | ContentBlockAdmin formfield_overrides содержит CKEditor5Widget | unit | `pytest apps/content/tests/test_admin.py::test_ckeditor_widget -x` | ❌ Wave 0 |
| CRM-10 | 10 неуспешных попыток входа → HTTP 429 lockout | unit | `pytest apps/accounts/tests/test_axes.py::test_brute_force_lockout -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `docker-compose exec web pytest apps/{app}/tests/ -x -q`
- **Per wave merge:** `docker-compose exec web pytest --tb=short -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `backend/apps/dashboard/__init__.py` + `apps/dashboard/views.py` + `apps/dashboard/tests/__init__.py` — app не существует
- [ ] `backend/apps/dashboard/tests/test_dashboard.py` — covers CRM-01, CRM-02
- [ ] `backend/apps/submissions/tests/test_admin.py` — covers CRM-03, CRM-04
- [ ] `backend/apps/industries/tests/test_admin.py` — covers CRM-05, CRM-06, CRM-07
- [ ] `backend/apps/payments/tests/test_admin.py` — covers CRM-08
- [ ] `backend/apps/content/tests/test_admin.py` — covers CRM-09
- [ ] `backend/apps/accounts/tests/test_axes.py` — covers CRM-10
- [ ] `backend/baqsy/settings/test.py` — с `AXES_ENABLED = False` для изоляции
- [ ] pip-пакеты: django-unfold, django-axes, django-admin-sortable2, django-ckeditor-5 — не в pyproject.toml

---

## Sources

### Primary (HIGH confidence)

- [django-unfold PyPI 0.90.0](https://pypi.org/project/django-unfold/) — версия и поддержка Django 5–6
- [unfoldadmin.com/docs/configuration/dashboard/](https://unfoldadmin.com/docs/configuration/dashboard/) — DASHBOARD_CALLBACK pattern
- [unfoldadmin.com/docs/actions/changeform/](https://unfoldadmin.com/docs/actions/changeform/) — @action decorator для кнопки в change_form
- [unfoldadmin.com/docs/configuration/settings/](https://unfoldadmin.com/docs/configuration/settings/) — UNFOLD dict структура
- [django-axes PyPI 8.3.1](https://pypi.org/project/django-axes/) — версия и поддержка Django 5.2
- [django-ckeditor-5 PyPI 0.2.20](https://pypi.org/project/django-ckeditor-5/) — версия, INSTALLED_APPS, formfield_overrides pattern
- [django-admin-sortable2 PyPI 2.2.8](https://pypi.org/project/django-admin-sortable2/) — версия

### Secondary (MEDIUM confidence)

- [unfoldadmin.com/blog/migrating-django-admin-unfold/](https://unfoldadmin.com/blog/migrating-django-admin-unfold/) — migration steps: inherit unfold.admin.ModelAdmin
- [django-axes readthedocs installation](https://django-axes.readthedocs.io/en/latest/2_installation.html) — INSTALLED_APPS + MIDDLEWARE + AUTHENTICATION_BACKENDS порядок (подтверждён WebSearch)
- [github.com/jazzband/django-axes conf.py](https://github.com/jazzband/django-axes/blob/master/axes/conf.py) — актуальные настройки AXES_*

### Tertiary (LOW confidence)

- WebSearch: django-admin-sortable2 TabularInline usage — документация недоступна, но GitHub README и PyPI подтверждают SortableInlineAdminMixin наличие

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — все четыре пакета верифицированы через PyPI, версии актуальны на апрель 2026
- Architecture: HIGH — patterns верифицированы через официальную документацию unfold и axes
- Pitfalls: HIGH — типичные ошибки INSTALLED_APPS порядка и axes backends верифицированы через документацию
- Dashboard HTMX approach: MEDIUM — стандартный HTMX pattern, но конкретная интеграция с unfold index.html не верифицирована через официальный пример

**Research date:** 2026-04-17
**Valid until:** 2026-05-17 (django-unfold выходит часто — проверить версию перед установкой)
