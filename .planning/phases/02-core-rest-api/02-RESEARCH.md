# Phase 2: Core REST API - Research

**Researched:** 2026-04-16
**Domain:** Django REST Framework, SimpleJWT, Redis deep-link tokens, Submission lifecycle API
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**URL-структура и версионирование**
- Все API-эндпоинты под префиксом `/api/v1/`
- Каждое приложение включает свои urls через `include("apps.{app}.urls")`
- Корневой `backend/baqsy/urls.py` подключает `api/v1/` namespace
- Маршруты:
  - `POST   /api/v1/bot/onboarding/`
  - `POST   /api/v1/bot/deeplink/`
  - `POST   /api/v1/bot/deeplink/exchange/`
  - `GET    /api/v1/industries/`
  - `POST   /api/v1/submissions/`
  - `GET    /api/v1/submissions/{id}/`
  - `GET    /api/v1/submissions/{id}/next-question/`
  - `POST   /api/v1/submissions/{id}/answers/`
  - `POST   /api/v1/submissions/{id}/complete/`

**Аутентификация**
- JWT (SimpleJWT) для клиентов; access 1 час, refresh 7 дней
- Django session auth для админки (уже работает)
- `IsAuthenticated` для клиентских эндпоинтов
- `AllowAny` для: `bot/onboarding/`, `bot/deeplink/exchange/`, `industries/`
- `/bot/onboarding/` защищён `X-Bot-Token` header (API-ключ), не JWT

**Deep-link токены**
- Redis db=2 для хранения (Phase 1 CONTEXT.md)
- Формат: `deeplink:{uuid}` → `{client_profile_id}`, TTL 30 минут
- UUID одноразовый: удаляется при exchange
- Если UUID истёк → 404

**Serializer-подход**
- ModelSerializer с явным списком fields (никакого `__all__`)
- Отдельные serializer'ы input/output где нужно
- Вложенные serializer'ы только для чтения
- Answer.value — JSONField, валидация типа ответа в serializer

**Ответы и ошибки**
- Custom exception handler: `{"error": "код", "detail": "текст на русском"}`
- HTTP-статусы строго: 200, 201, 400, 401, 403, 404
- Validation errors: `{"field_name": ["Ошибка"]}`

**Пагинация**
- PageNumberPagination, page_size=20
- Только для list-эндпоинтов (industries/); Submission-эндпоинты без пагинации

**DRF конфигурация**
- DEFAULT_AUTHENTICATION_CLASSES: JWTAuthentication + SessionAuthentication
- DEFAULT_PERMISSION_CLASSES: IsAuthenticated
- DEFAULT_PAGINATION_CLASS: PageNumberPagination, PAGE_SIZE: 20
- DEFAULT_RENDERER_CLASSES: JSONRenderer только (без BrowsableAPI в prod)
- SIMPLE_JWT: access=1h, refresh=7d, rotate_refresh_tokens=True

**Celery-заглушка**
- `notify_bot_payment_success(submission_id)` как stub (логирует в stdout) — реальная реализация в Phase 4

### Claude's Discretion
- Точные имена ViewSet/APIView классов
- Структура test fixtures (factory-boy factories vs raw creation)
- Порядок полей в serializer'ах
- Точный формат progress-ответа (процент vs "N/M")
- Throttle rates для API (Phase 8)
- Swagger/OpenAPI документация (Phase 8)

### Deferred Ideas (OUT OF SCOPE)
- WebSocket для real-time уведомлений
- Swagger/OpenAPI автодокументация (Phase 8)
- Throttle/rate limiting API (Phase 8)
- Файловые загрузки в ответах (v2)
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| API-01 | JWT-аутентификация для клиента (SimpleJWT) | SimpleJWT 5.5.1 конфигурация; нет в pyproject.toml — нужно добавить |
| API-02 | Django session-auth для админки | Уже работает из Phase 1; SESSION_COOKIE_HTTPONLY=True достаточно |
| API-03 | POST /api/v1/bot/onboarding/ — создаёт/обновляет ClientProfile по telegram_id | get_or_create паттерн; IsBotAuthenticated permission class |
| API-04 | GET /api/v1/industries/ — список активных отраслей | Industry.objects.filter(is_active=True); ListAPIView + PageNumberPagination |
| API-05 | POST /api/v1/submissions/ — создаёт Submission с тарифом и отраслью | Ищет активный шаблон; возвращает id/status/total_questions |
| API-06 | GET /api/v1/submissions/{id}/next-question/ | First unanswered Q; 204 No Content если всё отвечено |
| API-07 | POST /api/v1/submissions/{id}/answers/ | JSONField validation по field_type; unique_together guard → 400 |
| API-08 | POST /api/v1/submissions/{id}/complete/ | Проверка required вопросов; вызов complete_questionnaire() FSM |
| API-09 | GET /api/v1/submissions/{id}/ | Клиент видит только свои; фильтр по JWT → ClientProfile |
| API-10 | POST /api/v1/bot/deeplink/ — выдаёт UUID-токен | Redis db=2 SET с TTL 1800; формат deeplink:{uuid} |
| API-11 | POST /api/v1/bot/deeplink/exchange/ — UUID → JWT | Redis GET + DELETE; RefreshToken.for_user(); 404 если истёк |
</phase_requirements>

---

## Summary

Phase 2 строит весь REST API слой поверх моделей из Phase 1. Основных технических задач три: (1) подключить и настроить SimpleJWT и DRF в settings; (2) реализовать deep-link flow через Redis db=2; (3) написать ViewSet/APIView классы для 9 эндпоинтов с правильной пермиссионной моделью.

**Критическая находка:** `djangorestframework-simplejwt` отсутствует в `backend/pyproject.toml`. Пакет нужно добавить в Phase 2 Wave 0 перед любой реализацией JWT. DRF 3.17.1 уже присутствует в зависимостях.

**Критическая находка по моделям:** `ClientProfile` не имеет FK на `BaseUser` — это автономная модель с `telegram_id`. Deep-link flow должен создавать "бот-пользователя" через отдельный механизм. `RefreshToken.for_user()` из SimpleJWT требует объект с `AbstractBaseUser` интерфейсом. Решение: при создании ClientProfile через onboarding endpoint — создавать связанный `BaseUser` (или использовать `ClientProfile` напрямую через кастомный токен-бэкенд). Рекомендация: добавить `user = OneToOneField(BaseUser, null=True)` к ClientProfile и создавать BaseUser при onboarding с синтетическим email `tg_{telegram_id}@baqsy.internal`.

**Primary recommendation:** Добавить simplejwt в pyproject.toml, добавить user FK на ClientProfile, настроить DRF settings блок, реализовать 9 эндпоинтов через APIView (не ViewSet — каждый эндпоинт имеет нестандартную логику).

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| djangorestframework | 3.17.1 | REST layer: serializers, views, permissions | Уже в pyproject.toml; Django 5.2 compatible |
| djangorestframework-simplejwt | 5.5.1 | JWT access/refresh tokens | Стандарт для Django JWT; поддерживает rotate_refresh |
| redis (py) | 5.3.0 | Sync Redis client для deep-link хранения в Views | Уже в pyproject.toml; синхронные Django views используют sync redis |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| factory-boy | 3.3.x | Test data factories для APIClient тестов | Уже в dev зависимостях |
| pytest-django | 4.9.x | APIClient, db fixtures | Уже в dev зависимостях |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| APIView per endpoint | ModelViewSet | ViewSet не подходит — у каждого эндпоинта нестандартный URL (next-question, complete, answers) |
| Sync redis в views | Django cache framework (CACHES backend) | Django cache проще, но менее контролируем для TTL и atomic del; прямой redis прозрачнее |
| Sync redis в views | django.core.cache | Альтернатива: использовать `cache.set/get/delete` с CACHES["deeplink"] → Redis db=2; плюс — не нужно отдельный redis клиент инициализировать |

**Installation (добавить в pyproject.toml):**
```bash
poetry add djangorestframework-simplejwt==5.5.1
```

---

## Architecture Patterns

### Recommended File Structure (Phase 2 additions)

```
backend/
├── baqsy/
│   ├── urls.py                       # добавить: path("api/v1/", include("baqsy.api_urls"))
│   └── api_urls.py                   # корневой API router — include всех app urls
├── apps/
│   ├── accounts/
│   │   ├── serializers.py            # NEW: ClientProfileSerializer, OnboardingSerializer
│   │   ├── views.py                  # NEW: OnboardingView, DeepLinkCreateView, DeepLinkExchangeView
│   │   ├── urls.py                   # NEW: bot/ prefix routes
│   │   └── permissions.py            # NEW: IsBotAuthenticated
│   ├── industries/
│   │   ├── serializers.py            # NEW: IndustrySerializer
│   │   ├── views.py                  # NEW: IndustryListView
│   │   └── urls.py                   # NEW
│   └── submissions/
│       ├── serializers.py            # NEW: SubmissionCreateSerializer, SubmissionDetailSerializer,
│       │                             #      QuestionSerializer, AnswerCreateSerializer
│       ├── views.py                  # NEW: SubmissionCreateView, SubmissionDetailView,
│       │                             #      NextQuestionView, AnswerCreateView, CompleteView
│       └── urls.py                   # NEW
```

### Pattern 1: DRF Settings Block

**What:** Полный блок REST_FRAMEWORK в settings/base.py
**When to use:** Добавить в Wave 0 этой фазы

```python
# backend/baqsy/settings/base.py — добавить

from datetime import timedelta

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "EXCEPTION_HANDLER": "apps.core.exceptions.custom_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,   # не используем blacklist app (overhead не нужен)
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
}
```

### Pattern 2: IsBotAuthenticated Permission

**What:** Custom DRF permission class проверяющий `X-Bot-Token` header для bot-only endpoints
**When to use:** На `OnboardingView` и `DeepLinkCreateView`

```python
# apps/accounts/permissions.py
from django.conf import settings
from rest_framework.permissions import BasePermission


class IsBotAuthenticated(BasePermission):
    """Разрешает доступ только боту через X-Bot-Token header."""

    message = "Доступ разрешён только внутреннему боту."

    def has_permission(self, request, view) -> bool:
        token = request.headers.get("X-Bot-Token", "")
        return bool(token and token == settings.BOT_API_SECRET)
```

Добавить в `.env.example`:
```
BOT_API_SECRET=change-me-in-production
```

### Pattern 3: Redis Deep-Link Token (sync)

**What:** Создание и обмен UUID-токена через синхронный Redis client в Django views
**When to use:** `DeepLinkCreateView` и `DeepLinkExchangeView`

Два варианта — оба корректны:

**Вариант A (прямой redis.Redis):**
```python
# apps/accounts/views.py
import uuid
import redis
from django.conf import settings

# Инициализировать один раз (module-level или через django-redis cache alias)
redis_deeplink = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=2,
    decode_responses=True,
)

class DeepLinkCreateView(APIView):
    """POST /api/v1/bot/deeplink/ — бот запрашивает UUID для клиента."""
    authentication_classes = []
    permission_classes = [IsBotAuthenticated]

    def post(self, request):
        telegram_id = request.data.get("telegram_id")
        if not telegram_id:
            return Response(
                {"error": "validation_error", "detail": "telegram_id обязателен"},
                status=400,
            )
        try:
            profile = ClientProfile.objects.get(telegram_id=telegram_id)
        except ClientProfile.DoesNotExist:
            return Response(
                {"error": "not_found", "detail": "Профиль клиента не найден"},
                status=404,
            )
        token = str(uuid.uuid4())
        redis_deeplink.setex(f"deeplink:{token}", 1800, str(profile.id))
        return Response({"token": token}, status=201)


class DeepLinkExchangeView(APIView):
    """POST /api/v1/bot/deeplink/exchange/ — React обменивает UUID на JWT."""
    authentication_classes = []
    permission_classes = []  # AllowAny

    def post(self, request):
        token = request.data.get("token")
        if not token:
            return Response(
                {"error": "validation_error", "detail": "token обязателен"},
                status=400,
            )
        key = f"deeplink:{token}"
        profile_id = redis_deeplink.get(key)
        if not profile_id:
            return Response(
                {"error": "not_found", "detail": "Токен недействителен или истёк"},
                status=404,
            )
        redis_deeplink.delete(key)  # одноразовый токен

        try:
            profile = ClientProfile.objects.select_related("user").get(pk=profile_id)
        except ClientProfile.DoesNotExist:
            return Response(
                {"error": "not_found", "detail": "Профиль не найден"},
                status=404,
            )
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(profile.user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })
```

**Вариант B (через Django CACHES с redis backend):** Использовать `django.core.cache` с отдельным alias `"deeplink"` → `redis://redis:6379/2`. Плюс: нет отдельного redis client объекта. Минус: Django cache не гарантирует TTL точность при некоторых backends. Для UUID-токенов прямой redis надёжнее.

**Рекомендация: Вариант A** — прямой redis.Redis с db=2, как зафиксировано в Phase 1 CONTEXT.md.

Для конфигурации добавить в settings:
```python
REDIS_HOST = env("REDIS_HOST", default="redis")
REDIS_PORT = env.int("REDIS_PORT", default=6379)
```

### Pattern 4: ClientProfile → BaseUser связка для JWT

**Проблема:** `ClientProfile` не наследует `AbstractBaseUser` — `RefreshToken.for_user()` требует объект с интерфейсом `AbstractBaseUser` (поле `pk`, методы `get_username()`).

**Решение:** Добавить `OneToOneField` к `BaseUser` в `ClientProfile` и создавать синтетический `BaseUser` при onboarding.

```python
# apps/accounts/models.py — добавить поле к ClientProfile
class ClientProfile(TimestampedModel):
    user = models.OneToOneField(
        "accounts.BaseUser",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="client_profile",
    )
    telegram_id = models.BigIntegerField(unique=True)
    # ... остальные поля без изменений
```

```python
# apps/accounts/views.py — OnboardingView
class OnboardingView(APIView):
    """POST /api/v1/bot/onboarding/ — создать/обновить ClientProfile."""
    authentication_classes = []
    permission_classes = [IsBotAuthenticated]

    def post(self, request):
        telegram_id = request.data.get("telegram_id")
        # ... валидация
        profile, created = ClientProfile.objects.get_or_create(
            telegram_id=telegram_id,
            defaults=self._build_defaults(request.data),
        )
        if not created:
            # обновить изменяемые поля
            for field in ("name", "company", "phone_wa", "city"):
                if field in request.data:
                    setattr(profile, field, request.data[field])
            if "industry_id" in request.data:
                profile.industry_id = request.data["industry_id"]
            profile.save()

        # Создать BaseUser если нет (для JWT)
        if profile.user is None:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            synthetic_email = f"tg_{telegram_id}@baqsy.internal"
            user, _ = User.objects.get_or_create(
                email=synthetic_email,
                defaults={"is_active": True},
            )
            profile.user = user
            profile.save(update_fields=["user"])

        serializer = ClientProfileSerializer(profile)
        status_code = 201 if created else 200
        return Response(serializer.data, status=status_code)
```

**Важно:** Миграция для нового поля `user` на `ClientProfile` нужна в Wave 0 этой фазы.

### Pattern 5: Answer Validation по field_type

**What:** Serializer validate() метод проверяет структуру `Answer.value` JSONB относительно `question.field_type`
**When to use:** `AnswerCreateSerializer.validate()`

```python
# apps/submissions/serializers.py
from apps.industries.models import Question

class AnswerCreateSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    value = serializers.JSONField()

    def validate(self, attrs):
        question_id = attrs["question_id"]
        value = attrs["value"]

        try:
            question = Question.objects.get(pk=question_id)
        except Question.DoesNotExist:
            raise serializers.ValidationError(
                {"question_id": ["Вопрос не найден."]}
            )

        field_type = question.field_type
        err = self._validate_value(field_type, value, question.options)
        if err:
            raise serializers.ValidationError({"value": [err]})

        attrs["question"] = question
        return attrs

    @staticmethod
    def _validate_value(field_type: str, value, options: dict) -> str | None:
        """Возвращает строку ошибки или None если валидно."""
        if field_type == Question.FieldType.TEXT:
            if not isinstance(value, str) or not value.strip():
                return "Ожидается непустая строка для текстового вопроса."

        elif field_type == Question.FieldType.NUMBER:
            if not isinstance(value, (int, float)):
                return "Ожидается число для числового вопроса."

        elif field_type == Question.FieldType.CHOICE:
            allowed = options.get("choices", [])
            if value not in allowed:
                return f"Выберите один из вариантов: {', '.join(allowed)}."

        elif field_type == Question.FieldType.MULTICHOICE:
            allowed = set(options.get("choices", []))
            if not isinstance(value, list):
                return "Ожидается список значений для вопроса с множественным выбором."
            invalid = [v for v in value if v not in allowed]
            if invalid:
                return f"Недопустимые значения: {', '.join(str(v) for v in invalid)}."

        return None
```

**Хранение value в Answer.value JSONField:** Сохранять напрямую как переданное значение (строка/число/список). Поле `Answer.value` — JSONField, поддерживает все Python types.

### Pattern 6: Submission ownership guard

**What:** Клиент может обращаться только к своим Submission. Проверка через `get_object_or_404` с дополнительным фильтром по `client`.

```python
# apps/submissions/views.py
from django.shortcuts import get_object_or_404
from apps.submissions.models import Submission

def get_client_submission(request, pk):
    """Возвращает Submission принадлежащую текущему клиенту или 404."""
    profile = request.user.client_profile  # через OneToOneField
    return get_object_or_404(Submission, pk=pk, client=profile)
```

### Pattern 7: next-question логика

**What:** Первый уnanswered required Question из шаблона Submission
**When to use:** `GET /api/v1/submissions/{id}/next-question/`

```python
# apps/submissions/views.py
class NextQuestionView(APIView):
    def get(self, request, pk):
        submission = get_client_submission(request, pk)
        answered_ids = submission.answers.values_list("question_id", flat=True)
        next_q = (
            submission.template.questions
            .exclude(id__in=answered_ids)
            .order_by("order")
            .first()
        )
        if next_q is None:
            return Response(status=204)  # No Content — все вопросы отвечены
        return Response(QuestionSerializer(next_q).data)
```

### Pattern 8: complete endpoint с проверкой required вопросов

```python
# apps/submissions/views.py
class SubmissionCompleteView(APIView):
    def post(self, request, pk):
        submission = get_client_submission(request, pk)

        required_ids = set(
            submission.template.questions
            .filter(required=True)
            .values_list("id", flat=True)
        )
        answered_ids = set(submission.answers.values_list("question_id", flat=True))
        missing = required_ids - answered_ids

        if missing:
            return Response(
                {
                    "error": "incomplete",
                    "detail": f"Не отвечено на {len(missing)} обязательных вопроса(ов).",
                },
                status=400,
            )

        try:
            submission.complete_questionnaire()
            submission.save()
        except TransitionNotAllowed:
            return Response(
                {"error": "invalid_state", "detail": "Анкета не в статусе заполнения."},
                status=400,
            )
        return Response({"status": submission.status})
```

### Pattern 9: Custom Exception Handler

```python
# apps/core/exceptions.py
from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        data = response.data
        # DRF ValidationError имеет dict или list
        if isinstance(data, dict) and "detail" in data:
            response.data = {
                "error": _status_to_code(response.status_code),
                "detail": str(data["detail"]),
            }
        # Validation errors остаются как {"field": ["msg"]} — не оборачиваем
    return response


def _status_to_code(status_code: int) -> str:
    return {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        405: "method_not_allowed",
        429: "throttled",
        500: "server_error",
    }.get(status_code, "error")
```

### Pattern 10: URL routing

```python
# backend/baqsy/urls.py — обновить
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include


def health(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
    path("api/v1/", include("baqsy.api_urls")),
]
```

```python
# backend/baqsy/api_urls.py — новый файл
from django.urls import path, include

urlpatterns = [
    path("bot/", include("apps.accounts.urls")),
    path("industries/", include("apps.industries.urls")),
    path("submissions/", include("apps.submissions.urls")),
]
```

```python
# apps/accounts/urls.py
from django.urls import path
from apps.accounts.views import OnboardingView, DeepLinkCreateView, DeepLinkExchangeView

urlpatterns = [
    path("onboarding/", OnboardingView.as_view(), name="bot-onboarding"),
    path("deeplink/", DeepLinkCreateView.as_view(), name="bot-deeplink-create"),
    path("deeplink/exchange/", DeepLinkExchangeView.as_view(), name="bot-deeplink-exchange"),
]
```

```python
# apps/submissions/urls.py
from django.urls import path
from apps.submissions.views import (
    SubmissionCreateView,
    SubmissionDetailView,
    NextQuestionView,
    AnswerCreateView,
    SubmissionCompleteView,
)

urlpatterns = [
    path("", SubmissionCreateView.as_view(), name="submission-create"),
    path("<uuid:pk>/", SubmissionDetailView.as_view(), name="submission-detail"),
    path("<uuid:pk>/next-question/", NextQuestionView.as_view(), name="submission-next-question"),
    path("<uuid:pk>/answers/", AnswerCreateView.as_view(), name="submission-answer-create"),
    path("<uuid:pk>/complete/", SubmissionCompleteView.as_view(), name="submission-complete"),
]
```

**Важно:** Submission.id — UUID (UUIDModel). URL pattern должен использовать `<uuid:pk>`, не `<int:pk>`.

### Pattern 11: Celery stub task

```python
# apps/payments/tasks.py — заглушка Phase 2
import logging
from baqsy.celery import app

logger = logging.getLogger(__name__)


@app.task(name="payments.notify_bot_payment_success")
def notify_bot_payment_success(submission_id: str) -> None:
    """Stub: Phase 4 реализует реальное уведомление бота через Telegram Bot API."""
    logger.info(
        "notify_bot_payment_success stub called",
        extra={"submission_id": submission_id},
    )
```

### Anti-Patterns to Avoid

- **`fields = "__all__"`** в ModelSerializer — всегда явный список fields
- **Напрямую менять `submission.status = "completed"`** — только через FSM transition методы (`submission.complete_questionnaire()`)
- **JWT токен в URL** (deep-link) — слишком длинный для Telegram start param; UUID 36 символов
- **Импортировать Django ORM в bot/** — бот никогда не импортирует models напрямую
- **Вложенные serializer'ы для write** — только для чтения; write через явные поля + validate()
- **Один serializer для create и detail** — `SubmissionCreateSerializer` (input) vs `SubmissionDetailSerializer` (output) — разные поля

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JWT creation/validation | Ручная HMAC-подпись токенов | simplejwt `RefreshToken.for_user()` | Rotation, blacklisting, expiry — всё готово |
| Permission checking | if/else в view | `permission_classes = [IsBotAuthenticated]` | DRF вызывает до view логики; стандартный способ |
| Redis TTL management | Ручной cron cleanup | `redis.setex(key, ttl, value)` | Атомарное set+expire; Redis сам удаляет по TTL |
| Pagination | Ручной slice + count | `PageNumberPagination` | Автоматический `count`, `next`, `previous` |
| 404 ownership check | try/except DoesNotExist + if obj.client != profile | `get_object_or_404(Submission, pk=pk, client=profile)` | Одна строка, правильный HTTP 404 |

**Key insight:** Самая дорогая ошибка в DRF — писать бизнес-логику в `validate()` вместо service layer. Для сложной логики (проверка required вопросов, FSM transition) — вынести в отдельные методы модели или service функции, serializer только валидирует данные.

---

## Common Pitfalls

### Pitfall 1: simplejwt не в INSTALLED_APPS и не в pyproject.toml

**What goes wrong:** `ImportError: No module named 'rest_framework_simplejwt'` на первом запуске
**Why it happens:** `djangorestframework-simplejwt` отсутствует в текущем `pyproject.toml` (только `djangorestframework` есть)
**How to avoid:** Wave 0 задача — добавить `djangorestframework-simplejwt==5.5.1` в pyproject.toml и `"rest_framework_simplejwt"` в INSTALLED_APPS
**Warning signs:** ImportError при старте gunicorn или в тестах

### Pitfall 2: ClientProfile не имеет user FK — JWT невозможен

**What goes wrong:** `AttributeError: 'ClientProfile' has no attribute 'pk'` при попытке `RefreshToken.for_user(profile)`
**Why it happens:** `ClientProfile` не наследует `AbstractBaseUser`; simplejwt требует `AbstractBaseUser`-совместимый объект
**How to avoid:** Добавить `user = OneToOneField(BaseUser, ...)` к ClientProfile + миграция в Wave 0; создавать BaseUser при onboarding с email `tg_{id}@baqsy.internal`
**Warning signs:** `TypeError` или `AttributeError` при генерации JWT

### Pitfall 3: Submission pk — UUID, не int

**What goes wrong:** `ValueError: invalid literal for int()` или 404 на всех submission endpoints
**Why it happens:** URL pattern `<int:pk>` не матчит UUID primary key
**How to avoid:** Использовать `<uuid:pk>` во всех submission URL patterns
**Warning signs:** Все submission endpoints возвращают 404 в тестах

### Pitfall 4: FSMField защищён от прямого присваивания

**What goes wrong:** `TransitionNotAllowed` или `AttributeError` при попытке `submission.status = "completed"`
**Why it happens:** `django-fsm-2` блокирует прямые присваивания к FSMField
**How to avoid:** Всегда вызывать transition методы: `submission.complete_questionnaire()`, затем `submission.save()`
**Warning signs:** Tests pass в unit но fail в integration при прямом присваивании

### Pitfall 5: Redis db split — не перепутать

**What goes wrong:** Deep-link токены попадают в Celery broker (db=0) и засоряют очередь задач
**Why it happens:** Неправильный db index при инициализации redis.Redis()
**How to avoid:** `redis.Redis(host=..., port=..., db=2)` — строго db=2 для deeplink как зафиксировано в Phase 1
**Warning signs:** Celery workers получают непонятные сообщения; токены не удаляются при FLUSHDB db=0

### Pitfall 6: unique_together (submission, question) → IntegrityError не 400

**What goes wrong:** При повторном POST ответа на тот же вопрос — 500 Internal Server Error
**Why it happens:** `Answer.Meta.unique_together = [("submission", "question")]` — PostgreSQL вернёт IntegrityError
**How to avoid:** В `AnswerCreateView` использовать `get_or_create` или предварительная проверка `exists()`:
```python
if Answer.objects.filter(submission=submission, question=question).exists():
    return Response(
        {"error": "duplicate", "detail": "Ответ на этот вопрос уже сохранён."},
        status=400,
    )
```

### Pitfall 7: BrowsableAPIRenderer в prod

**What goes wrong:** Django REST Framework отдаёт HTML браузеру в production — раскрывает структуру API и значительно замедляет ответы для JSON клиентов
**Why it happens:** DRF включает BrowsableAPIRenderer по умолчанию
**How to avoid:** В `settings/base.py` явно указать `DEFAULT_RENDERER_CLASSES = ["rest_framework.renderers.JSONRenderer"]`. Решено в CONTEXT.md.

### Pitfall 8: INSTALLED_APPS порядок для simplejwt

**What goes wrong:** JWT токены не работают; `ImproperlyConfigured` при настройке blacklist
**Why it happens:** `rest_framework_simplejwt` должен быть в INSTALLED_APPS если используется blacklist app
**Note:** Blacklist не используется (CONTEXT.md: `BLACKLIST_AFTER_ROTATION = False`). Достаточно добавить `"rest_framework_simplejwt"` в INSTALLED_APPS для корректной работы token serializers.

---

## Code Examples

### SubmissionCreateView — полный паттерн

```python
# apps/submissions/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.submissions.models import Submission
from apps.industries.models import QuestionnaireTemplate
from apps.payments.models import Tariff
from apps.submissions.serializers import SubmissionCreateSerializer, SubmissionDetailSerializer


class SubmissionCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SubmissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        profile = request.user.client_profile

        # Найти активный шаблон для отрасли
        try:
            template = QuestionnaireTemplate.objects.get(
                industry_id=data["industry_id"],
                is_active=True,
            )
        except QuestionnaireTemplate.DoesNotExist:
            return Response(
                {"error": "not_found", "detail": "Активный шаблон анкеты для отрасли не найден."},
                status=404,
            )

        tariff = Tariff.objects.filter(
            id=data["tariff_id"], is_active=True
        ).first()
        if not tariff:
            return Response(
                {"error": "not_found", "detail": "Тариф не найден или неактивен."},
                status=404,
            )

        submission = Submission.objects.create(
            client=profile,
            template=template,
            tariff=tariff,
        )
        total_questions = template.questions.count()
        return Response(
            {
                "id": str(submission.id),
                "status": submission.status,
                "template_name": template.name,
                "total_questions": total_questions,
            },
            status=201,
        )
```

### AnswerCreateView — с progress response

```python
class AnswerCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        submission = get_client_submission(request, pk)

        serializer = AnswerCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.validated_data["question"]
        value = serializer.validated_data["value"]

        # Проверить дубликат
        if Answer.objects.filter(submission=submission, question=question).exists():
            return Response(
                {"error": "duplicate", "detail": "Ответ на этот вопрос уже сохранён."},
                status=400,
            )

        # Первый ответ → FSM переход в in_progress_full
        if submission.status == Submission.Status.PAID:
            try:
                submission.start_questionnaire()
                submission.save()
            except TransitionNotAllowed:
                pass  # Уже in_progress_full от другого ответа (race condition guard)

        Answer.objects.create(submission=submission, question=question, value=value)

        answered_count = submission.answers.count()
        total_count = submission.template.questions.count()
        return Response(
            {"progress": f"{answered_count}/{total_count}"},
            status=201,
        )
```

### IndustryListView

```python
# apps/industries/views.py
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from apps.industries.models import Industry
from apps.industries.serializers import IndustrySerializer


class IndustryListView(ListAPIView):
    queryset = Industry.objects.filter(is_active=True).order_by("name")
    serializer_class = IndustrySerializer
    permission_classes = [AllowAny]
    # PageNumberPagination применяется автоматически из DEFAULT_PAGINATION_CLASS
```

### Factory-boy для тестов

```python
# apps/accounts/tests/factories.py
import factory
from django.contrib.auth import get_user_model
from apps.accounts.models import ClientProfile
from apps.industries.models import Industry

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@baqsy.internal")
    is_active = True


class IndustryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Industry

    name = factory.Sequence(lambda n: f"Industry {n}")
    code = factory.Sequence(lambda n: f"industry-{n}")
    is_active = True


class ClientProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ClientProfile

    user = factory.SubFactory(UserFactory)
    telegram_id = factory.Sequence(lambda n: 10000 + n)
    name = "Test Client"
    company = "Test Company"
```

### pytest APIClient паттерн

```python
# apps/submissions/tests/test_api.py
import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from apps.accounts.tests.factories import ClientProfileFactory, IndustryFactory
from apps.industries.models import QuestionnaireTemplate


@pytest.fixture
def auth_client(db):
    profile = ClientProfileFactory()
    refresh = RefreshToken.for_user(profile.user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client, profile


@pytest.mark.django_db
def test_submission_create(auth_client):
    client, profile = auth_client
    industry = IndustryFactory()
    template = QuestionnaireTemplate.objects.create(
        industry=industry, version=1, is_active=True, name="Test"
    )
    # создать тариф...
    response = client.post("/api/v1/submissions/", {
        "industry_id": industry.id,
        "tariff_id": ...,
    })
    assert response.status_code == 201
    assert "id" in response.json()
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `djangorestframework-jwt` (PyJWT-based) | `djangorestframework-simplejwt` | 2019 | simplejwt — активно поддерживается; djangorestframework-jwt заброшен |
| `aioredis` для Redis | `redis` (py) async | aiogram 3.x (2022) | `import redis.asyncio as aioredis` — один пакет для sync и async |
| `request.user.profile` (implicit) | `request.user.client_profile` (OneToOneField reverse) | Django 3+ | Явный related_name предотвращает `RelatedObjectDoesNotExist` |

**Deprecated:**
- `djangorestframework-jwt`: заброшен, не использовать
- `rest_framework.decorators.api_view` для complex views: предпочтительны APIView классы для тестируемости
- `DEFAULT_AUTHENTICATION_CLASSES` без явного порядка: JWT должен быть первым (до SessionAuthentication) для API endpoints

---

## Open Questions

1. **ClientProfile.industry — нужен ли он на уровне API?**
   - Что мы знаем: ClientProfile имеет `industry FK` (nullable). Onboarding принимает industry от бота.
   - Что неясно: Нужно ли проверять что `industry_id` в `POST /submissions/` совпадает с `profile.industry`?
   - Рекомендация: Не проверять совпадение — клиент может выбрать другую отрасль. `profile.industry` — справочное поле, не ограничитель.

2. **BOT_API_SECRET в .env — зафиксировано ли имя переменной?**
   - Что мы знаем: ARCHITECTURE.md использует `BOT_API_SECRET`, CONTEXT.md — `X-Bot-Token` header
   - Что неясно: Финальное имя env переменной
   - Рекомендация: Использовать `BOT_API_SECRET` в .env, `X-Bot-Token` как имя header (разные вещи)

3. **Тариф в POST /submissions/ — передаётся tariff_id или tariff_code?**
   - Что мы знаем: `Tariff.code` — slug ("ashide_1"), `Tariff.id` — BigAutoField
   - Что неясно: Бот удобнее передавать code (понятнее), React — id
   - Рекомендация: Принимать `tariff_code` (slug) — бот знает коды из конфига; избегает жёсткой привязки к ID

---

## Validation Architecture

> nyquist_validation: true — секция включена

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.x + pytest-django 4.9.x |
| Config file | `backend/pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `docker-compose exec web pytest apps/accounts/tests/ apps/industries/tests/ apps/submissions/tests/ -x -q` |
| Full suite command | `docker-compose exec web pytest --cov=apps --cov-report=term-missing -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| API-01 | JWT token returned for valid ClientProfile.user | unit | `pytest apps/accounts/tests/test_api.py::test_deeplink_exchange_returns_jwt -x` | Wave 0 |
| API-02 | Session auth для Django admin работает | smoke | `pytest tests/test_settings.py -x` (расширить) | Частично |
| API-03 | POST /bot/onboarding/ создаёт ClientProfile + user | unit | `pytest apps/accounts/tests/test_api.py::test_onboarding_creates_profile -x` | Wave 0 |
| API-03 | POST /bot/onboarding/ без X-Bot-Token → 403 | unit | `pytest apps/accounts/tests/test_api.py::test_onboarding_requires_bot_token -x` | Wave 0 |
| API-04 | GET /industries/ возвращает только is_active=True | unit | `pytest apps/industries/tests/test_api.py::test_industry_list_active_only -x` | Wave 0 |
| API-05 | POST /submissions/ создаёт Submission с активным шаблоном | unit | `pytest apps/submissions/tests/test_api.py::test_submission_create -x` | Wave 0 |
| API-05 | POST /submissions/ без активного шаблона → 404 | unit | `pytest apps/submissions/tests/test_api.py::test_submission_create_no_template -x` | Wave 0 |
| API-06 | GET /next-question/ возвращает первый неотвеченный | unit | `pytest apps/submissions/tests/test_api.py::test_next_question -x` | Wave 0 |
| API-06 | GET /next-question/ → 204 когда всё отвечено | unit | `pytest apps/submissions/tests/test_api.py::test_next_question_all_answered -x` | Wave 0 |
| API-07 | POST /answers/ сохраняет Answer, возвращает progress | unit | `pytest apps/submissions/tests/test_api.py::test_answer_create -x` | Wave 0 |
| API-07 | POST /answers/ дубликат → 400 (не 500) | unit | `pytest apps/submissions/tests/test_api.py::test_answer_duplicate -x` | Wave 0 |
| API-07 | POST /answers/ неверный field_type → 400 | unit | `pytest apps/submissions/tests/test_api.py::test_answer_wrong_type -x` | Wave 0 |
| API-08 | POST /complete/ с незавершёнными required → 400 | unit | `pytest apps/submissions/tests/test_api.py::test_complete_missing_required -x` | Wave 0 |
| API-08 | POST /complete/ все required отвечены → status=completed | unit | `pytest apps/submissions/tests/test_api.py::test_complete_success -x` | Wave 0 |
| API-09 | GET /submissions/{id}/ чужого клиента → 404 | unit | `pytest apps/submissions/tests/test_api.py::test_submission_ownership -x` | Wave 0 |
| API-10 | POST /bot/deeplink/ создаёт UUID токен в Redis | unit | `pytest apps/accounts/tests/test_api.py::test_deeplink_create -x` | Wave 0 |
| API-11 | POST /bot/deeplink/exchange/ обменивает UUID на JWT | unit | `pytest apps/accounts/tests/test_api.py::test_deeplink_exchange -x` | Wave 0 |
| API-11 | POST /bot/deeplink/exchange/ истёкший UUID → 404 | unit | `pytest apps/accounts/tests/test_api.py::test_deeplink_exchange_expired -x` | Wave 0 |

**Примечание по Redis в тестах:** Тесты deep-link exchange требуют Redis. Варианты: (1) `fakeredis` — mock Redis без запущенного инстанса; (2) `pytest-mock` + monkeypatch redis client. Рекомендация: `fakeredis` для изолированных unit тестов.

Добавить `fakeredis` в dev зависимости:
```
fakeredis = "^2.23"
```

### Sampling Rate

- **Per task commit:** `pytest apps/{changed_app}/tests/ -x -q`
- **Per wave merge:** `pytest --cov=apps -q`
- **Phase gate:** Full suite green перед `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `backend/apps/accounts/tests/test_api.py` — покрывает API-01, API-03, API-10, API-11
- [ ] `backend/apps/industries/tests/test_api.py` — покрывает API-04
- [ ] `backend/apps/submissions/tests/test_api.py` — покрывает API-05 — API-09
- [ ] `backend/apps/accounts/tests/factories.py` — UserFactory, ClientProfileFactory
- [ ] `backend/apps/submissions/tests/factories.py` — SubmissionFactory, QuestionFactory
- [ ] Добавить `fakeredis` в dev зависимости (`pyproject.toml`)
- [ ] Добавить `djangorestframework-simplejwt==5.5.1` в pyproject.toml
- [ ] Миграция для `ClientProfile.user = OneToOneField(BaseUser, null=True)`
- [ ] `backend/apps/core/exceptions.py` — custom_exception_handler
- [ ] REST_FRAMEWORK + SIMPLE_JWT блоки в `settings/base.py`

---

## Sources

### Primary (HIGH confidence)

- DRF 3.17.1 официальная документация — APIView, permission_classes, exception_handler, serializers
- simplejwt 5.5.1 PyPI + docs — RefreshToken.for_user(), SIMPLE_JWT settings dict
- `.planning/research/STACK.md` (verified 2026-04-15) — версии пакетов
- `.planning/research/ARCHITECTURE.md` (verified 2026-04-15) — deep-link pattern, Redis db split
- `.planning/phases/01-infrastructure-data-model/01-CONTEXT.md` — Redis db=2 для deeplink (locked decision)
- `backend/apps/submissions/models.py` — FSM transitions, Answer.unique_together
- `backend/apps/accounts/models.py` — ClientProfile fields
- `backend/pyproject.toml` — точные версии установленных пакетов

### Secondary (MEDIUM confidence)

- `backend/apps/industries/models.py` — Question.FieldType choices, options структура
- `backend/conftest.py` — существующие test fixtures
- `backend/apps/submissions/tests/test_fsm.py` — установленный паттерн django_db тестов

### Tertiary (LOW confidence)

- `fakeredis` как замена Redis в тестах — нужна проверка совместимости с redis 5.3.0

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — все версии подтверждены в pyproject.toml и STACK.md; simplejwt отсутствует в pyproject.toml — задокументировано
- Architecture: HIGH — паттерны подтверждены из ARCHITECTURE.md и существующего кода моделей
- Pitfalls: HIGH — все питфоллы выведены из реального кода моделей (UUID pk, FSMField, unique_together)
- Test patterns: HIGH — pytest-django и factory-boy уже в dev зависимостях; паттерн установлен в Phase 1

**Research date:** 2026-04-16
**Valid until:** 2026-05-16 (стабильный стек; DRF и simplejwt выходят редко)
