"""Tests for ContentBlock API views."""
import pytest
from django.urls import reverse

from apps.content.models import ContentBlock


@pytest.mark.django_db
def test_content_list_returns_active_blocks(client):
    """Active blocks appear in the response; inactive blocks are excluded."""
    ContentBlock.objects.create(key="hero_title", title="Hero Title", content="Hello World", is_active=True)
    ContentBlock.objects.create(key="hero_subtitle", title="Hero Subtitle", content="Sub text", is_active=True)
    ContentBlock.objects.create(key="hidden_block", title="Hidden", content="Secret", is_active=False)

    response = client.get("/api/v1/content/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) == 2
    assert data["hero_title"] == "Hello World"
    assert data["hero_subtitle"] == "Sub text"
    assert "hidden_block" not in data


@pytest.mark.django_db
def test_content_list_empty(client):
    """No active blocks returns empty dict."""
    response = client.get("/api/v1/content/")

    assert response.status_code == 200
    assert response.json() == {}


@pytest.mark.django_db
def test_content_list_allows_anonymous(client):
    """Anonymous requests are allowed (no auth required)."""
    ContentBlock.objects.create(key="public_key", title="Public", content="Public content", is_active=True)

    response = client.get("/api/v1/content/")

    assert response.status_code == 200
    assert "public_key" in response.json()
