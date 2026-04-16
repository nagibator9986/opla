"""Tests for deep-link token creation and exchange flow."""
from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

BOT_SECRET = "test-secret"


@pytest.mark.django_db
class TestDeeplink:
    def setup_method(self):
        self.client = APIClient()
        self.bot_headers = {"HTTP_X_BOT_TOKEN": BOT_SECRET}

    @override_settings(BOT_API_SECRET=BOT_SECRET)
    def test_onboarding_creates_profile(self):
        response = self.client.post(
            "/api/v1/bot/onboarding/",
            {"telegram_id": 12345, "name": "Test", "company": "TestCo"},
            format="json",
            **self.bot_headers,
        )
        assert response.status_code == 201
        assert response.data["created"] is True

    @override_settings(BOT_API_SECRET=BOT_SECRET)
    def test_onboarding_updates_existing(self):
        self.client.post(
            "/api/v1/bot/onboarding/",
            {"telegram_id": 12345, "name": "Test", "company": "TestCo"},
            format="json",
            **self.bot_headers,
        )
        response = self.client.post(
            "/api/v1/bot/onboarding/",
            {"telegram_id": 12345, "name": "Updated", "company": "NewCo"},
            format="json",
            **self.bot_headers,
        )
        assert response.status_code == 200

    def test_onboarding_without_bot_token_returns_401_or_403(self):
        """Without bot token, DRF returns 401 (unauthenticated) before permission check."""
        response = self.client.post(
            "/api/v1/bot/onboarding/",
            {"telegram_id": 12345, "name": "Test", "company": "TestCo"},
            format="json",
        )
        assert response.status_code in (401, 403)

    @override_settings(BOT_API_SECRET=BOT_SECRET)
    @patch("apps.accounts.views._get_deeplink_redis")
    def test_create_deeplink_returns_uuid(self, mock_redis):
        mock_r = MagicMock()
        mock_redis.return_value = mock_r
        from apps.accounts.models import ClientProfile

        ClientProfile.objects.create(telegram_id=12345, name="T", company="C")
        response = self.client.post(
            "/api/v1/bot/deeplink/",
            {"telegram_id": 12345},
            format="json",
            **self.bot_headers,
        )
        assert response.status_code == 201
        assert "token" in response.data
        mock_r.setex.assert_called_once()

    @patch("apps.accounts.views._get_deeplink_redis")
    def test_exchange_deeplink_returns_jwt(self, mock_redis):
        mock_r = MagicMock()
        mock_redis.return_value = mock_r
        from apps.accounts.models import BaseUser, ClientProfile

        profile = ClientProfile.objects.create(telegram_id=12345, name="T", company="C")
        BaseUser.objects.create_user(email="tg_12345@baqsy.internal")
        mock_r.get.return_value = str(profile.id)
        token = str(uuid.uuid4())
        response = self.client.post(
            "/api/v1/bot/deeplink/exchange/",
            {"token": token},
            format="json",
        )
        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data
        mock_r.delete.assert_called_once()

    @patch("apps.accounts.views._get_deeplink_redis")
    def test_exchange_expired_token_returns_404(self, mock_redis):
        mock_r = MagicMock()
        mock_redis.return_value = mock_r
        mock_r.get.return_value = None
        response = self.client.post(
            "/api/v1/bot/deeplink/exchange/",
            {"token": str(uuid.uuid4())},
            format="json",
        )
        assert response.status_code == 404

    @override_settings(BOT_API_SECRET=BOT_SECRET)
    @patch("apps.accounts.views._get_deeplink_redis")
    def test_create_deeplink_for_unknown_client_returns_404(self, mock_redis):
        mock_r = MagicMock()
        mock_redis.return_value = mock_r
        response = self.client.post(
            "/api/v1/bot/deeplink/",
            {"telegram_id": 99999},
            format="json",
            **self.bot_headers,
        )
        assert response.status_code == 404

    @override_settings(BOT_API_SECRET=BOT_SECRET)
    def test_onboarding_with_industry(self):
        from apps.accounts.models import ClientProfile
        from apps.industries.models import Industry

        Industry.objects.create(name="IT", code="it", is_active=True)
        response = self.client.post(
            "/api/v1/bot/onboarding/",
            {"telegram_id": 99999, "name": "Dev", "company": "DevCo", "industry_code": "it"},
            format="json",
            **self.bot_headers,
        )
        assert response.status_code == 201
        profile = ClientProfile.objects.get(telegram_id=99999)
        assert profile.industry is not None
        assert profile.industry.code == "it"
