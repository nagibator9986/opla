---
phase: 02-core-rest-api
plan: 00
type: execute
wave: 0
title: "API bootstrap — DRF + SimpleJWT + factories"
depends_on: []
requirements: []
autonomous: true
files_modified:
  - backend/pyproject.toml
  - backend/baqsy/settings/base.py
  - backend/baqsy/urls.py
  - backend/tests/factories.py
nyquist_compliant: true
---

# Plan 00: API Bootstrap — DRF + SimpleJWT + Factories

## Goal

Install and configure DRF + SimpleJWT in settings. Create URL routing skeleton for `/api/v1/`. Create factory-boy factories for all models used in API tests.

## must_haves

- SimpleJWT installed and configured in settings
- `/api/v1/` URL namespace exists
- Factory-boy factories for ClientProfile, Industry, QuestionnaireTemplate, Question, Submission, Answer, Tariff

## Tasks

<task id="00-01">
<title>Add SimpleJWT to dependencies and configure DRF in settings</title>
<read_first>
- backend/pyproject.toml
- backend/baqsy/settings/base.py
- .planning/phases/02-core-rest-api/02-CONTEXT.md
- .planning/phases/02-core-rest-api/02-RESEARCH.md
</read_first>
<action>
1. Add `djangorestframework-simplejwt` to pyproject.toml main dependencies:
   `poetry add djangorestframework-simplejwt==5.5.1`

2. Add to INSTALLED_APPS in `backend/baqsy/settings/base.py`:
   - `"rest_framework"` (may already exist)
   - `"rest_framework_simplejwt"`

3. Add DRF configuration block to base.py:
```python
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

from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}
```

4. Add `BOT_API_SECRET` to env reading:
```python
BOT_API_SECRET = env("BOT_API_SECRET", default="dev-bot-secret")
```

5. Add `BOT_API_SECRET=` to `.env.example`

6. Create `backend/apps/core/exceptions.py`:
```python
from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None and hasattr(response, 'data'):
        if isinstance(response.data, dict) and 'detail' in response.data:
            response.data = {
                "error": response.status_code,
                "detail": str(response.data["detail"]),
            }
    return response
```
</action>
<acceptance_criteria>
- `backend/baqsy/settings/base.py` contains `"rest_framework_simplejwt"`
- `backend/baqsy/settings/base.py` contains `REST_FRAMEWORK`
- `backend/baqsy/settings/base.py` contains `SIMPLE_JWT`
- `backend/baqsy/settings/base.py` contains `BOT_API_SECRET`
- `backend/apps/core/exceptions.py` contains `def custom_exception_handler`
- `.env.example` contains `BOT_API_SECRET=`
</acceptance_criteria>
</task>

<task id="00-02">
<title>Create /api/v1/ URL routing skeleton</title>
<read_first>
- backend/baqsy/urls.py
- .planning/phases/02-core-rest-api/02-CONTEXT.md (URL structure)
</read_first>
<action>
Update `backend/baqsy/urls.py` to include api/v1/ namespace:

```python
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include


def health(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
    path("api/v1/", include("apps.core.api_urls")),
]
```

Create `backend/apps/core/api_urls.py`:
```python
from django.urls import path, include

urlpatterns = [
    path("bot/", include("apps.accounts.bot_urls")),
    path("industries/", include("apps.industries.urls")),
    path("submissions/", include("apps.submissions.urls")),
]
```

Create placeholder URL files in each app (empty urlpatterns for now — filled in Plans 01-03):
- `backend/apps/accounts/bot_urls.py` with `urlpatterns = []`
- `backend/apps/industries/urls.py` with `urlpatterns = []`
- `backend/apps/submissions/urls.py` with `urlpatterns = []`
</action>
<acceptance_criteria>
- `backend/baqsy/urls.py` contains `path("api/v1/", include("apps.core.api_urls"))`
- `backend/apps/core/api_urls.py` contains `path("bot/", include("apps.accounts.bot_urls"))`
- `backend/apps/core/api_urls.py` contains `path("industries/", include("apps.industries.urls"))`
- `backend/apps/core/api_urls.py` contains `path("submissions/", include("apps.submissions.urls"))`
- `python manage.py check` exits 0
</acceptance_criteria>
</task>

<task id="00-03">
<title>Create factory-boy model factories</title>
<read_first>
- backend/apps/accounts/models.py
- backend/apps/industries/models.py
- backend/apps/submissions/models.py
- backend/apps/payments/models.py
</read_first>
<action>
Create `backend/tests/factories.py`:

```python
import factory
from factory.django import DjangoModelFactory

from apps.accounts.models import BaseUser, ClientProfile
from apps.industries.models import Industry, QuestionnaireTemplate, Question
from apps.submissions.models import Submission
from apps.payments.models import Tariff


class UserFactory(DjangoModelFactory):
    class Meta:
        model = BaseUser
    email = factory.Sequence(lambda n: f"user{n}@baqsy.kz")
    is_active = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop("password", "testpass123")
        obj = super()._create(model_class, *args, **kwargs)
        obj.set_password(password)
        obj.save()
        return obj


class IndustryFactory(DjangoModelFactory):
    class Meta:
        model = Industry
    name = factory.Sequence(lambda n: f"Industry {n}")
    code = factory.Sequence(lambda n: f"industry-{n}")
    is_active = True


class QuestionnaireTemplateFactory(DjangoModelFactory):
    class Meta:
        model = QuestionnaireTemplate
    industry = factory.SubFactory(IndustryFactory)
    version = 1
    is_active = True
    name = factory.LazyAttribute(lambda o: f"Template {o.industry.name} v{o.version}")


class QuestionFactory(DjangoModelFactory):
    class Meta:
        model = Question
    template = factory.SubFactory(QuestionnaireTemplateFactory)
    order = factory.Sequence(lambda n: n + 1)
    text = factory.Sequence(lambda n: f"Question {n}?")
    field_type = "text"
    options = {}
    required = True
    block = "A"


class TariffFactory(DjangoModelFactory):
    class Meta:
        model = Tariff
    code = factory.Sequence(lambda n: f"tariff-{n}")
    title = factory.Sequence(lambda n: f"Tariff {n}")
    price_kzt = 45000
    is_active = True


class ClientProfileFactory(DjangoModelFactory):
    class Meta:
        model = ClientProfile
    telegram_id = factory.Sequence(lambda n: 100000 + n)
    name = factory.Faker("name")
    company = factory.Faker("company")
    phone_wa = factory.Sequence(lambda n: f"+7700{n:07d}")
    city = "Алматы"
    industry = factory.SubFactory(IndustryFactory)


class SubmissionFactory(DjangoModelFactory):
    class Meta:
        model = Submission
    client = factory.SubFactory(ClientProfileFactory)
    template = factory.SubFactory(QuestionnaireTemplateFactory)
    tariff = factory.SubFactory(TariffFactory)
```

Update `backend/conftest.py` to expose factories:
```python
import pytest
from tests.factories import (
    UserFactory, IndustryFactory, QuestionnaireTemplateFactory,
    QuestionFactory, TariffFactory, ClientProfileFactory, SubmissionFactory,
)

@pytest.fixture
def user_factory():
    return UserFactory

@pytest.fixture
def industry_factory():
    return IndustryFactory

@pytest.fixture
def client_profile_factory():
    return ClientProfileFactory

@pytest.fixture
def submission_factory():
    return SubmissionFactory
```
</action>
<acceptance_criteria>
- `backend/tests/factories.py` contains `class UserFactory`
- `backend/tests/factories.py` contains `class ClientProfileFactory`
- `backend/tests/factories.py` contains `class SubmissionFactory`
- `backend/tests/factories.py` contains `class IndustryFactory`
- `backend/tests/factories.py` contains `class QuestionFactory`
- `python -c "from tests.factories import *"` runs without error
</acceptance_criteria>
</task>

## Verification

```bash
python manage.py check
python -m pytest --collect-only  # factories importable
```
