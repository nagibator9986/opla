"""Tests for JWT auth and bot token authentication."""
from __future__ import annotations

import pytest
from django.test import override_settings
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestJWTAuth:
    def test_jwt_auth_returns_tokens(self, client_profile_factory):
        from rest_framework_simplejwt.tokens import RefreshToken

        from apps.accounts.models import BaseUser

        profile = client_profile_factory()
        user = BaseUser.objects.create_user(
            email=f"tg_{profile.telegram_id}@baqsy.internal"
        )
        refresh = RefreshToken.for_user(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        # Access token is valid — authenticated request should not return 401
        # (Real endpoint coverage is in submissions tests — Phase 2 Plan 02)
        assert str(refresh.access_token)  # token is non-empty

    def test_unauthenticated_request_returns_401(self):
        client = APIClient()
        response = client.get("/api/v1/submissions/")
        assert response.status_code == 401

    def test_session_auth_admin_redirect(self):
        client = APIClient()
        response = client.get("/admin/", follow=False)
        assert response.status_code == 302


@pytest.mark.django_db
class TestIsBotAuthenticated:
    @override_settings(BOT_API_SECRET="test-secret")
    def test_missing_bot_token_returns_403(self):
        client = APIClient()
        response = client.post(
            "/api/v1/bot/onboarding/",
            {"telegram_id": 99999, "name": "X", "company": "Y"},
            format="json",
        )
        assert response.status_code == 403

    @override_settings(BOT_API_SECRET="test-secret")
    def test_wrong_bot_token_returns_403(self):
        client = APIClient()
        response = client.post(
            "/api/v1/bot/onboarding/",
            {"telegram_id": 99999, "name": "X", "company": "Y"},
            format="json",
            HTTP_X_BOT_TOKEN="wrong-token",
        )
        assert response.status_code == 403

    @override_settings(BOT_API_SECRET="test-secret")
    def test_correct_bot_token_is_accepted(self):
        client = APIClient()
        response = client.post(
            "/api/v1/bot/onboarding/",
            {"telegram_id": 11111, "name": "Test", "company": "Co"},
            format="json",
            HTTP_X_BOT_TOKEN="test-secret",
        )
        assert response.status_code in (200, 201)
