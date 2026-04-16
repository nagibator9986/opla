"""API tests for GET /api/v1/industries/ endpoint."""
from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from tests.factories import IndustryFactory


@pytest.mark.django_db
class TestIndustryList:
    def test_list_returns_active_industries(self):
        IndustryFactory(name="Active Industry", is_active=True)
        IndustryFactory(name="Inactive Industry", is_active=False)
        client = APIClient()
        response = client.get("/api/v1/industries/")
        assert response.status_code == 200
        names = [i["name"] for i in response.data["results"]]
        assert "Active Industry" in names
        assert "Inactive Industry" not in names

    def test_list_returns_paginated(self):
        for i in range(25):
            IndustryFactory()
        client = APIClient()
        response = client.get("/api/v1/industries/")
        assert response.status_code == 200
        assert response.data["count"] == 25
        assert len(response.data["results"]) == 20  # page_size from settings

    def test_industry_fields(self):
        IndustryFactory(name="IT", code="it-sector", description="IT sector")
        client = APIClient()
        response = client.get("/api/v1/industries/")
        assert response.status_code == 200
        assert len(response.data["results"]) > 0
        industry = response.data["results"][0]
        assert "id" in industry
        assert "name" in industry
        assert "code" in industry
        assert "description" in industry

    def test_list_no_auth_required(self):
        """Industries endpoint must be public (no authentication needed)."""
        client = APIClient()
        response = client.get("/api/v1/industries/")
        # Should not return 401 or 403
        assert response.status_code == 200

    def test_list_ordered_by_name(self):
        """Industries should be returned in alphabetical order."""
        IndustryFactory(name="Ритейл", code="retail")
        IndustryFactory(name="ИТ", code="it")
        client = APIClient()
        response = client.get("/api/v1/industries/")
        assert response.status_code == 200
        # Django default ordering on Industry is ["name"], endpoint respects it
        names = [i["name"] for i in response.data["results"]]
        assert names == sorted(names)
