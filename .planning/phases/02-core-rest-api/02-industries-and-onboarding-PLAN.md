---
phase: 02-core-rest-api
plan: 02
type: execute
wave: 1
title: "Industries list and bot onboarding API"
depends_on: [00]
requirements: [API-03, API-04]
autonomous: true
files_modified:
  - backend/apps/industries/serializers.py
  - backend/apps/industries/views.py
  - backend/apps/industries/urls.py
  - backend/apps/industries/tests/test_api.py
nyquist_compliant: true
---

# Plan 02: Industries List and Bot Onboarding API

## Goal

Create `/api/v1/industries/` list endpoint (public, paginated) and test the onboarding flow from Plan 01 with industry association.

## must_haves

- GET /api/v1/industries/ returns active industries with name, code, description
- Industry list is paginated (PageNumberPagination, page_size=20)
- Onboarding with industry_code associates ClientProfile with Industry
- API-03 and API-04 tested

## Tasks

<task id="02-01">
<title>Create Industries list API</title>
<read_first>
- backend/apps/industries/models.py (Industry)
- .planning/phases/02-core-rest-api/02-CONTEXT.md
</read_first>
<action>
Create `backend/apps/industries/serializers.py`:
```python
from rest_framework import serializers
from apps.industries.models import Industry


class IndustrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Industry
        fields = ["id", "name", "code", "description"]
```

Create `backend/apps/industries/views.py`:
```python
from rest_framework import generics
from rest_framework.permissions import AllowAny
from apps.industries.models import Industry
from apps.industries.serializers import IndustrySerializer


class IndustryListView(generics.ListAPIView):
    """GET /api/v1/industries/ — list active industries."""
    serializer_class = IndustrySerializer
    permission_classes = [AllowAny]
    queryset = Industry.objects.filter(is_active=True).order_by("name")
```

Update `backend/apps/industries/urls.py`:
```python
from django.urls import path
from apps.industries.views import IndustryListView

urlpatterns = [
    path("", IndustryListView.as_view(), name="industry-list"),
]
```
</action>
<acceptance_criteria>
- `backend/apps/industries/views.py` contains `class IndustryListView(generics.ListAPIView):`
- `backend/apps/industries/views.py` contains `permission_classes = [AllowAny]`
- `backend/apps/industries/urls.py` contains `path("", IndustryListView.as_view()`
- `backend/apps/industries/serializers.py` contains `class IndustrySerializer`
</acceptance_criteria>
</task>

<task id="02-02">
<title>Write tests for industries and onboarding with industry</title>
<read_first>
- backend/apps/industries/views.py
- backend/tests/factories.py
</read_first>
<action>
Create `backend/apps/industries/tests/test_api.py`:
```python
import pytest
from rest_framework.test import APIClient
from tests.factories import IndustryFactory


@pytest.mark.django_db
class TestIndustryList:
    def test_list_returns_active_industries(self):
        IndustryFactory(name="Active", is_active=True)
        IndustryFactory(name="Inactive", is_active=False)
        client = APIClient()
        response = client.get("/api/v1/industries/")
        assert response.status_code == 200
        names = [i["name"] for i in response.data["results"]]
        assert "Active" in names
        assert "Inactive" not in names

    def test_list_returns_paginated(self):
        for i in range(25):
            IndustryFactory()
        client = APIClient()
        response = client.get("/api/v1/industries/")
        assert response.status_code == 200
        assert response.data["count"] == 25
        assert len(response.data["results"]) == 20  # page_size

    def test_industry_fields(self):
        IndustryFactory(name="IT", code="it", description="IT sector")
        client = APIClient()
        response = client.get("/api/v1/industries/")
        industry = response.data["results"][0]
        assert "name" in industry
        assert "code" in industry
        assert "description" in industry
```

Update onboarding test to verify industry association:
Add to `backend/apps/accounts/tests/test_deeplink.py`:
```python
    def test_onboarding_with_industry(self):
        from apps.industries.models import Industry
        Industry.objects.create(name="IT", code="it", is_active=True)
        response = self.client.post(
            "/api/v1/bot/onboarding/",
            {"telegram_id": 99999, "name": "Dev", "company": "DevCo", "industry_code": "it"},
            format="json",
            **self.bot_headers,
        )
        assert response.status_code == 201
        from apps.accounts.models import ClientProfile
        profile = ClientProfile.objects.get(telegram_id=99999)
        assert profile.industry is not None
        assert profile.industry.code == "it"
```
</action>
<acceptance_criteria>
- `backend/apps/industries/tests/test_api.py` contains `def test_list_returns_active_industries`
- `backend/apps/industries/tests/test_api.py` contains `def test_list_returns_paginated`
- `pytest apps/industries/tests/test_api.py -x` exits 0
</acceptance_criteria>
</task>

## Verification

```bash
pytest apps/industries/tests/ apps/accounts/tests/ -x -q
```
