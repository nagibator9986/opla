# Phase 7: Admin CRM - Context

**Gathered:** 2026-04-17
**Status:** Ready for planning
**Mode:** auto (recommended defaults)

<domain>
## Phase Boundary

Администратор может управлять всем жизненным циклом заказа, контентом и конфигурацией системы через веб-интерфейс без правки кода. Включает: дашборд со статистикой и фильтрами, карточка заказа с ответами клиента и редактором аудита, CRUD отраслей и шаблонов анкет с версионированием, редактор тарифов и контент-блоков лендинга, защита входа от брутфорса.

**Не делаем в этой фазе:** structlog/Sentry/CI (Phase 8), TLS/rate limiting (Phase 8), webhook-режим бота (Phase 8), seed-скрипт (Phase 8). Фронтенд клиента уже готов (Phase 5). API для approve уже реализован (Phase 6).

Требования: CRM-01..CRM-10 (10 штук).

</domain>

<decisions>
## Implementation Decisions

### CRM-платформа
- Django Admin с кастомизацией через django-unfold (современный UI для Django admin)
- Все модели уже зарегистрированы с базовыми ModelAdmin — нужна кастомизация, не создание с нуля
- Админ один (владелец методологии) — отдельный React CRM избыточен
- Session-auth (Django sessions) — уже настроена (Phase 2, API-02)

### Дашборд статистики (CRM-01, CRM-02)
- Кастомная admin index page с числовыми карточками (counters):
  - Всего заказов
  - В работе (status=in_progress/completed/under_audit)
  - Завершённых (status=delivered)
  - Выручка за период (сумма Payment.amount где status=succeeded)
- Фильтры: отрасль, регион (город), тариф, дата — без перезагрузки (AJAX/HTMX)
- Без графиков на MVP — только числовые карточки с фильтрами
- Фильтрация реализуется через Django ORM aggregate queries

### Список и карточка заказа (CRM-03, CRM-04)
- Список заказов: стандартный Django admin list с поиском, сортировкой и фильтрами по статусу
- Карточка заказа — кастомная change_form:
  - Левая колонка: все ответы клиента (read-only, из Answer + Question)
  - Правая колонка: textarea для admin_text (аудит)
  - Снизу: кнопка «Подтвердить и отправить» — вызывает ApproveReportView (уже реализован в Phase 6)
- AuditReport создаётся автоматически при переходе submission в completed (или вручную через admin)
- Inline AuditReport в SubmissionAdmin для быстрого доступа

### Редактор отраслей и шаблонов анкет (CRM-05, CRM-06, CRM-07)
- Industry CRUD: стандартный Django admin (уже есть, допилить)
- QuestionnaireTemplate: кнопка «Создать новую версию» на странице шаблона
  - При сохранении изменённого шаблона — auto-create новой версии (через create_new_version)
  - Старые версии — read-only в списке (ссылки на исторические заказы видны)
  - Просмотр истории версий в list view
- Question ordering: django-admin-sortable2 для drag-n-drop порядка вопросов (CRM-07)
- Типы полей вопросов (text/number/choice/multichoice) — уже в модели, нужен удобный UI для options JSONB

### Редактор тарифов (CRM-08)
- Стандартный Django admin с list_editable для цены и is_active
- Изменение цены мгновенно отражается на лендинге (ContentBlock + Tariff API уже работают)
- Три тарифа: ashide_1, ashide_2, upsell — коды фиксированы

### Редактор контент-блоков (CRM-09)
- WYSIWYG-редактор для content поля: django-ckeditor-5 (современный, поддерживает Django 5)
- ContentBlock.content_type определяет тип контента (text/html/markdown)
- Группировка по content_type в list view для удобства
- Предпросмотр HTML-контента в admin (read-only rendered preview)

### Защита входа (CRM-10)
- django-axes для защиты от брутфорса: 10 неверных попыток → блокировка IP
- Настройки: AXES_FAILURE_LIMIT=10, AXES_COOLOFF_TIME=timedelta(hours=1)
- Логин: стандартный Django admin login (/admin/)

### Claude's Discretion
- Точный выбор django-unfold theme/colors (в рамках «солидного» стиля)
- Layout деталей карточки заказа (точные размеры колонок)
- CKEditor toolbar configuration
- Dashboard card styling и responsive breakpoints
- Exact HTMX integration approach для фильтрации дашборда
- Admin site header/title text

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project-level
- `CLAUDE.md` — архитектура, стек, принцип «автономная админка», Django session-auth для админки
- `.planning/PROJECT.md` — Core Value, требование заказчика «полная автономия админки (изменение цен, вопросов, текстов без разработчика)»
- `.planning/REQUIREMENTS.md` — CRM-01..CRM-10
- `.planning/ROADMAP.md` — Phase 7 success criteria

### Prior phase decisions
- `.planning/phases/01-infrastructure-data-model/01-CONTEXT.md` — все модели (AuditReport, Submission, Industry, QuestionnaireTemplate, Question, ContentBlock, Tariff, Payment, DeliveryLog), версионирование шаблонов (create_new_version), Django admin базовая регистрация
- `.planning/phases/02-core-rest-api/02-CONTEXT.md` — session auth для админки (API-02), API URL structure
- `.planning/phases/05-react-frontend/05-CONTEXT.md` — ContentBlock API (ключи hero_title, method_text и т.д.), Tariff API, deep-link auth
- `.planning/phases/06-pdf-generation-delivery/06-CONTEXT.md` — ApproveReportView (POST /api/v1/reports/{id}/approve/), Celery chain generate_pdf → deliver_telegram + deliver_whatsapp

### Existing admin code (MUST read)
- `backend/apps/reports/admin.py` — AuditReportAdmin (list_display, search, readonly)
- `backend/apps/submissions/admin.py` — SubmissionAdmin (list_display, filters, AnswerInline)
- `backend/apps/industries/admin.py` — IndustryAdmin, QuestionnaireTemplateAdmin (QuestionInline)
- `backend/apps/content/admin.py` — ContentBlockAdmin (list_editable is_active)
- `backend/apps/payments/admin.py` — TariffAdmin, PaymentAdmin
- `backend/apps/delivery/admin.py` — DeliveryLogAdmin
- `backend/apps/accounts/admin.py` — ClientProfileAdmin

### Existing backend code (MUST read)
- `backend/apps/reports/views.py` — ApproveReportView (already implemented, Phase 6)
- `backend/apps/reports/models.py` — AuditReport (submission, admin_text, pdf_url, status, approved_at)
- `backend/apps/submissions/models.py` — Submission FSM states, Answer model
- `backend/apps/industries/models.py` — Industry, QuestionnaireTemplate (create_new_version), Question
- `backend/apps/content/models.py` — ContentBlock (key, title, content, content_type, is_active)
- `backend/apps/payments/models.py` — Tariff (code, title, price_kzt, is_active), Payment

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Django Admin registrations** — все 9+ моделей уже зарегистрированы с базовыми ModelAdmin, list_display, filters, search, inlines
- **ApproveReportView** — `POST /api/v1/reports/{id}/approve/` уже реализован в Phase 6, запускает Celery chain генерации и доставки PDF
- **AnswerInline** — TabularInline в SubmissionAdmin, показывает ответы (question, value, answered_at)
- **QuestionInline** — TabularInline в QuestionnaireTemplateAdmin с ordering
- **create_new_version()** — метод на QuestionnaireTemplate для версионирования (Phase 1)
- **ContentBlock API** — GET /api/v1/content/ уже работает, фронт уже потребляет

### Established Patterns
- **Django session auth** — настроена, IsAdminUser permission используется в ApproveReportView
- **ModelAdmin с list_filter/search_fields/list_display** — единообразный паттерн во всех apps
- **TabularInline** — для Answer и Question вложенных в parent admin
- **UUID primary keys** — Submission, Payment используют UUID
- **JSONB fields** — Answer.value, Question.options — нужен удобный виджет в admin

### Integration Points
- `backend/baqsy/settings/base.py` — добавить django-unfold, django-axes, django-ckeditor-5, django-admin-sortable2 в INSTALLED_APPS
- `backend/apps/*/admin.py` — переписать все admin registrations для unfold-совместимости
- `backend/apps/dashboard/` — app для кастомного дашборда (или переиспользовать admin index)
- `backend/baqsy/urls.py` — admin site уже настроен, может потребоваться кастомный AdminSite
- `requirements.txt` / `pyproject.toml` — добавить зависимости

</code_context>

<specifics>
## Specific Ideas

- Заказчик требует «полную автономию админки» — менять цены, вопросы, тексты лендинга без разработчика
- Админ один — владелец методологии, не команда. Не нужна ролевая модель или разграничение прав
- «Подтвердить и отправить» уже реализовано как API — нужна только кнопка в UI admin карточки
- Кнопка ApproveReport в карточке должна быть заметной и вызывать JS-confirm перед отправкой
- Версионирование шаблонов — ключевая фишка: админ редактирует вопросы, но старые заказы не ломаются

</specifics>

<deferred>
## Deferred Ideas

- Экспорт статистики в CSV/Excel — v2 (ANALYTICS-01)
- OAuth для админов (Google Workspace) — v2 (SSO-01)
- Графики и визуализация трендов на дашборде — v2
- PDF preview в карточке заказа перед отправкой — nice to have
- Уведомления админа в Telegram о новых заказах — не в скоупе Phase 7

</deferred>

---

*Phase: 07-admin-crm*
*Context gathered: 2026-04-17*
