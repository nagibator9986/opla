"""Views for accounts app: onboarding and deep-link token flow."""
from __future__ import annotations

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
    DeeplinkCreateSerializer,
    DeeplinkExchangeSerializer,
    OnboardingSerializer,
)
from apps.industries.models import Industry


def _get_deeplink_redis():
    """Return a synchronous Redis client for deep-link token storage (db=2)."""
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=2,
        decode_responses=True,
    )


class OnboardingView(APIView):
    """POST /api/v1/bot/onboarding/ — create or update ClientProfile."""

    # Bot endpoints use API key auth, not JWT — bypass default auth pipeline
    authentication_classes = []
    permission_classes = [IsBotAuthenticated]

    def post(self, request):
        serializer = OnboardingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        industry = None
        if data.get("industry_code"):
            industry = Industry.objects.filter(
                code=data["industry_code"], is_active=True
            ).first()

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

        # Ensure synthetic BaseUser exists for JWT issuance, link to profile
        if profile.user is None:
            email = f"tg_{data['telegram_id']}@baqsy.internal"
            user, _ = BaseUser.objects.get_or_create(
                email=email,
                defaults={"is_active": True},
            )
            profile.user = user
            profile.save(update_fields=["user"])

        return Response(
            {"id": profile.id, "created": created},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class DeeplinkCreateView(APIView):
    """POST /api/v1/bot/deeplink/ — bot creates a one-time UUID token."""

    # Bot endpoints use API key auth, not JWT — bypass default auth pipeline
    authentication_classes = []
    permission_classes = [IsBotAuthenticated]

    def post(self, request):
        serializer = DeeplinkCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        telegram_id = serializer.validated_data["telegram_id"]
        try:
            profile = ClientProfile.objects.get(telegram_id=telegram_id)
        except ClientProfile.DoesNotExist:
            return Response(
                {"error": "not_found", "detail": "Клиент не найден. Пройдите онбординг."},
                status=status.HTTP_404_NOT_FOUND,
            )

        token = str(uuid.uuid4())
        r = _get_deeplink_redis()
        r.setex(f"deeplink:{token}", 1800, str(profile.id))  # TTL 30 min

        return Response({"token": token}, status=status.HTTP_201_CREATED)


class DeeplinkExchangeView(APIView):
    """POST /api/v1/bot/deeplink/exchange/ — exchange UUID for JWT pair."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = DeeplinkExchangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = str(serializer.validated_data["token"])
        r = _get_deeplink_redis()

        profile_id = r.get(f"deeplink:{token}")
        if not profile_id:
            return Response(
                {"error": "not_found", "detail": "Токен истёк или недействителен."},
                status=status.HTTP_404_NOT_FOUND,
            )

        r.delete(f"deeplink:{token}")  # One-time use

        try:
            profile = ClientProfile.objects.get(id=int(profile_id))
        except ClientProfile.DoesNotExist:
            return Response(
                {"error": "not_found", "detail": "Клиент не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get or create synthetic user for JWT
        email = f"tg_{profile.telegram_id}@baqsy.internal"
        user, _ = BaseUser.objects.get_or_create(email=email, defaults={"is_active": True})

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "client_profile_id": profile.id,
                "name": profile.name,
            }
        )
