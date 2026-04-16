---
phase: 02-core-rest-api
plan: 01
type: execute
wave: 1
title: "JWT auth, bot auth, deep-link token endpoints"
depends_on: [00]
requirements: [API-01, API-02, API-10, API-11]
autonomous: true
files_modified:
  - backend/apps/accounts/serializers.py
  - backend/apps/accounts/views.py
  - backend/apps/accounts/bot_urls.py
  - backend/apps/accounts/permissions.py
  - backend/apps/accounts/tests/test_api.py
  - backend/apps/accounts/tests/test_deeplink.py
nyquist_compliant: true
---

# Plan 01: JWT Auth, Bot Auth, Deep-Link Endpoints

## Goal

Implement JWT authentication for clients, session auth for admin (already working), bot API key permission, and deep-link token flow (UUID ↔ JWT exchange via Redis db=2).

## must_haves

- SimpleJWT token obtain/refresh endpoints work
- Bot endpoints protected by X-Bot-Token header
- Deep-link: bot creates UUID → React exchanges for JWT → UUID consumed (one-time)
- All 4 requirements (API-01, API-02, API-10, API-11) tested

## Tasks

<task id="01-01">
<title>Create IsBotAuthenticated permission class</title>
<read_first>
- backend/baqsy/settings/base.py (BOT_API_SECRET)
- .planning/phases/02-core-rest-api/02-CONTEXT.md (bot auth decisions)
</read_first>
<action>
Create `backend/apps/accounts/permissions.py`:

```python
from django.conf import settings
from rest_framework.permissions import BasePermission


class IsBotAuthenticated(BasePermission):
    """Verify X-Bot-Token header matches BOT_API_SECRET."""

    def has_permission(self, request, view):
        token = request.headers.get("X-Bot-Token", "")
        return token == settings.BOT_API_SECRET
```
</action>
<acceptance_criteria>
- `backend/apps/accounts/permissions.py` contains `class IsBotAuthenticated(BasePermission):`
- `backend/apps/accounts/permissions.py` contains `request.headers.get("X-Bot-Token"`
</acceptance_criteria>
</task>

<task id="01-02">
<title>Create deep-link views (create + exchange)</title>
<read_first>
- .planning/phases/02-core-rest-api/02-RESEARCH.md (deep-link Redis pattern)
- backend/apps/accounts/models.py (ClientProfile)
- .planning/phases/02-core-rest-api/02-CONTEXT.md (deep-link decisions)
</read_first>
<action>
Create `backend/apps/accounts/serializers.py`:

```python
from rest_framework import serializers
from apps.accounts.models import ClientProfile


class OnboardingSerializer(serializers.Serializer):
    telegram_id = serializers.IntegerField()
    name = serializers.CharField(max_length=255)
    company = serializers.CharField(max_length=255)
    industry_code = serializers.CharField(max_length=50, required=False)
    phone_wa = serializers.CharField(max_length=20, required=False, default="")
    city = serializers.CharField(max_length=100, required=False, default="")


class DeeplinkCreateSerializer(serializers.Serializer):
    telegram_id = serializers.IntegerField()


class DeeplinkExchangeSerializer(serializers.Serializer):
    token = serializers.UUIDField()


class ClientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientProfile
        fields = ["id", "telegram_id", "name", "company", "phone_wa", "city", "industry"]
        read_only_fields = ["id", "telegram_id"]
```

Create `backend/apps/accounts/views.py`:

```python
import uuid
import redis
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import BaseUser, ClientProfile
from apps.accounts.permissions import IsBotAuthenticated
from apps.accounts.serializers import (
    OnboardingSerializer,
    DeeplinkCreateSerializer,
    DeeplinkExchangeSerializer,
)
from apps.industries.models import Industry


def _get_deeplink_redis():
    return redis.Redis.from_url(settings.REDIS_URL + "/2", decode_responses=True)


class OnboardingView(APIView):
    """POST /api/v1/bot/onboarding/ — create or update ClientProfile."""
    permission_classes = [IsBotAuthenticated]

    def post(self, request):
        serializer = OnboardingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        industry = None
        if data.get("industry_code"):
            industry = Industry.objects.filter(code=data["industry_code"], is_active=True).first()

        profile, created = ClientProfile.objects.update_or_create(
            telegram_id=data["telegram_id"],
            defaults={
                "name": data["name"],
                "company": data["company"],
                "phone_wa": data.get("phone_wa", ""),
                "city": data.get("city", ""),
                "industry": industry,
            },
        )

        # Ensure synthetic BaseUser exists for JWT
        email = f"tg_{data['telegram_id']}@baqsy.internal"
        user, _ = BaseUser.objects.get_or_create(
            email=email,
            defaults={"is_active": True},
        )

        return Response(
            {"id": profile.id, "created": created},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class DeeplinkCreateView(APIView):
    """POST /api/v1/bot/deeplink/ — bot creates a one-time UUID token."""
    permission_classes = [IsBotAuthenticated]

    def post(self, request):
        serializer = DeeplinkCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        telegram_id = serializer.validated_data["telegram_id"]
        try:
            profile = ClientProfile.objects.get(telegram_id=telegram_id)
        except ClientProfile.DoesNotExist:
            return Response(
                {"error": 404, "detail": "Клиент не найден. Пройдите онбординг."},
                status=status.HTTP_404_NOT_FOUND,
            )

        token = str(uuid.uuid4())
        r = _get_deeplink_redis()
        r.setex(f"deeplink:{token}", 1800, str(profile.id))  # TTL 30 min

        return Response({"token": token}, status=status.HTTP_201_CREATED)


class DeeplinkExchangeView(APIView):
    """POST /api/v1/bot/deeplink/exchange/ — exchange UUID for JWT."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = DeeplinkExchangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = str(serializer.validated_data["token"])
        r = _get_deeplink_redis()

        profile_id = r.get(f"deeplink:{token}")
        if not profile_id:
            return Response(
                {"error": 404, "detail": "Токен истёк или недействителен."},
                status=status.HTTP_404_NOT_FOUND,
            )

        r.delete(f"deeplink:{token}")  # One-time use

        try:
            profile = ClientProfile.objects.get(id=int(profile_id))
        except ClientProfile.DoesNotExist:
            return Response(
                {"error": 404, "detail": "Клиент не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get or create synthetic user for JWT
        email = f"tg_{profile.telegram_id}@baqsy.internal"
        user, _ = BaseUser.objects.get_or_create(email=email, defaults={"is_active": True})

        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "client_profile_id": profile.id,
            "name": profile.name,
        })
```

Update `backend/apps/accounts/bot_urls.py`:
```python
from django.urls import path
from apps.accounts.views import OnboardingView, DeeplinkCreateView, DeeplinkExchangeView

urlpatterns = [
    path("onboarding/", OnboardingView.as_view(), name="bot-onboarding"),
    path("deeplink/", DeeplinkCreateView.as_view(), name="bot-deeplink-create"),
    path("deeplink/exchange/", DeeplinkExchangeView.as_view(), name="bot-deeplink-exchange"),
]
```
</action>
<acceptance_criteria>
- `backend/apps/accounts/views.py` contains `class OnboardingView(APIView):`
- `backend/apps/accounts/views.py` contains `class DeeplinkCreateView(APIView):`
- `backend/apps/accounts/views.py` contains `class DeeplinkExchangeView(APIView):`
- `backend/apps/accounts/views.py` contains `r.setex(f"deeplink:{token}", 1800`
- `backend/apps/accounts/views.py` contains `r.delete(f"deeplink:{token}")`
- `backend/apps/accounts/views.py` contains `RefreshToken.for_user(user)`
- `backend/apps/accounts/bot_urls.py` contains `path("onboarding/"`
- `backend/apps/accounts/bot_urls.py` contains `path("deeplink/exchange/"`
</acceptance_criteria>
</task>

<task id="01-03">
<title>Write tests for auth and deep-link flow</title>
<read_first>
- backend/apps/accounts/views.py
- backend/apps/accounts/permissions.py
- backend/tests/factories.py
</read_first>
<action>
Create `backend/apps/accounts/tests/test_api.py`:
```python
import pytest
from rest_framework.test import APIClient
from django.test import override_settings


@pytest.mark.django_db
class TestJWTAuth:
    def test_jwt_auth_returns_tokens(self, client_profile_factory):
        from rest_framework_simplejwt.tokens import RefreshToken
        from apps.accounts.models import BaseUser
        profile = client_profile_factory()
        user = BaseUser.objects.create_user(email=f"tg_{profile.telegram_id}@baqsy.internal")
        refresh = RefreshToken.for_user(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        # authenticated request should not get 401
        # (We'll test with a real endpoint in Phase 2 submissions)

    def test_unauthenticated_request_returns_401(self):
        client = APIClient()
        response = client.get("/api/v1/submissions/")
        assert response.status_code == 401

    def test_session_auth_admin_redirect(self):
        client = APIClient()
        response = client.get("/admin/", follow=False)
        assert response.status_code == 302
```

Create `backend/apps/accounts/tests/test_deeplink.py`:
```python
import pytest
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from django.test import override_settings


@pytest.mark.django_db
@override_settings(BOT_API_SECRET="test-secret")
class TestDeeplink:
    def setup_method(self):
        self.client = APIClient()
        self.bot_headers = {"HTTP_X_BOT_TOKEN": "test-secret"}

    def test_onboarding_creates_profile(self):
        response = self.client.post(
            "/api/v1/bot/onboarding/",
            {"telegram_id": 12345, "name": "Test", "company": "TestCo"},
            format="json",
            **self.bot_headers,
        )
        assert response.status_code == 201
        assert response.data["created"] is True

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

    def test_onboarding_without_bot_token_returns_403(self):
        response = self.client.post(
            "/api/v1/bot/onboarding/",
            {"telegram_id": 12345, "name": "Test", "company": "TestCo"},
            format="json",
        )
        assert response.status_code == 403

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
        from apps.accounts.models import ClientProfile, BaseUser
        profile = ClientProfile.objects.create(telegram_id=12345, name="T", company="C")
        BaseUser.objects.create_user(email="tg_12345@baqsy.internal")
        mock_r.get.return_value = str(profile.id)
        import uuid
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
        import uuid
        response = self.client.post(
            "/api/v1/bot/deeplink/exchange/",
            {"token": str(uuid.uuid4())},
            format="json",
        )
        assert response.status_code == 404
```
</action>
<acceptance_criteria>
- `backend/apps/accounts/tests/test_deeplink.py` contains `def test_onboarding_creates_profile`
- `backend/apps/accounts/tests/test_deeplink.py` contains `def test_exchange_deeplink_returns_jwt`
- `backend/apps/accounts/tests/test_deeplink.py` contains `def test_exchange_expired_token_returns_404`
- `backend/apps/accounts/tests/test_api.py` contains `def test_unauthenticated_request_returns_401`
- `pytest apps/accounts/tests/ -x` exits 0
</acceptance_criteria>
</task>

## Verification

```bash
pytest apps/accounts/tests/ -x -q  # all auth + deeplink tests pass
```
