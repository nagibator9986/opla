"""Accounts views — quick login by WhatsApp number (no verification, MVP).

Public endpoints:

* ``POST /api/v1/auth/quick-login/`` — найти ClientProfile по phone_wa,
  выдать JWT-пару. Без верификации (нет SMS/WhatsApp confirmation) —
  это MVP, защита только троттлингом по IP.

AI-chat onboarding endpoints — в ``apps.ai.views``.
"""
from __future__ import annotations

import logging
import re

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import ClientProfile

log = logging.getLogger(__name__)


class _QuickLoginThrottle(AnonRateThrottle):
    """5 запросов в минуту с одного IP — защита от перебора."""

    rate = "5/min"


def _normalize_phone(raw: str) -> str:
    """KZ-форматы → 7XXXXXXXXXX (только цифры)."""
    if not raw:
        return ""
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return ""
    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]
    return digits


class QuickLoginView(APIView):
    """POST /api/v1/auth/quick-login/  body: { "phone_wa": "+7 ..." }

    MVP — без верификации. Ищет последний привязанный к юзеру
    ClientProfile с этим номером (в нескольких форматах). Возвращает
    JWT-пару + имя клиента.

    Если профиля нет — 404, чтобы фронт мог предложить регистрацию.
    """

    permission_classes = [AllowAny]
    throttle_classes = [_QuickLoginThrottle]

    def post(self, request):
        raw = (request.data.get("phone_wa") or "").strip()
        normalized = _normalize_phone(raw)
        if not normalized or len(normalized) < 10:
            return Response(
                {"detail": "Введите корректный номер WhatsApp."},
                status=400,
            )

        # Ищем по нескольким возможным форматам хранения
        candidates = {normalized, "+" + normalized}
        if normalized.startswith("7"):
            candidates.add("8" + normalized[1:])
            candidates.add("+7" + normalized[1:])

        client = (
            ClientProfile.objects.filter(
                phone_wa__in=list(candidates), user__isnull=False
            )
            .order_by("-id")
            .first()
        )

        if client is None:
            return Response(
                {
                    "detail": (
                        "Не нашли профиль с таким номером. Пройдите регистрацию "
                        "в чате — это займёт пару минут."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        refresh = RefreshToken.for_user(client.user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "client_profile_id": client.id,
                "name": client.name,
            }
        )
