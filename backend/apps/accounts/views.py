"""Auth endpoints — magic-link login by WhatsApp.

The legacy Telegram-bot endpoints (onboarding, deeplink, JWT issuance) were
removed when the product switched to AI-chat onboarding. The current public
endpoints are:

* ``POST /api/v1/auth/login-link/``      — request a one-time login link by phone_wa
* ``GET  /api/v1/auth/magic/<token>/``   — verify token, issue JWT pair
* AI-chat onboarding lives in ``apps.ai.views``.
"""
from __future__ import annotations

import logging
import re

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import ClientProfile, MagicLink

log = logging.getLogger(__name__)


class _LoginThrottle(AnonRateThrottle):
    """Жёсткий per-IP лимит на запрос magic-link, чтобы не спамить WhatsApp."""

    rate = "10/hour"


def _normalize_phone(raw: str) -> str:
    """Convert any WhatsApp-ish input to canonical 7XXXXXXXXXX (digits only).

    Accepts: "+7 700 225 91 84", "8 700 225 91 84", "77002259184", etc.
    """
    if not raw:
        return ""
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return ""
    # KZ: 8XXXXXXXXXX → 7XXXXXXXXXX
    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]
    return digits


def _get_client_ip(request) -> str | None:
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _build_magic_url(token: str) -> str:
    base = getattr(settings, "PUBLIC_SITE_URL", "https://baqsy.tnriazun.com").rstrip("/")
    return f"{base}/auth/magic/{token}"


def _send_magic_link_via_whatsapp(client: ClientProfile, magic_url: str) -> str:
    """Отправка через Wazzup24. Возвращает 'whatsapp' / 'fallback' (никогда не raise)."""
    api_key = getattr(settings, "WAZZUP_API_KEY", "") or ""
    channel_id = getattr(settings, "WAZZUP_CHANNEL_ID", "") or ""
    if not (api_key and channel_id and client.phone_wa):
        log.info("magic-link: WA delivery skipped (no key/channel/phone) for client=%s", client.id)
        return "fallback"
    try:
        from apps.delivery.providers.wazzup24 import Wazzup24Provider

        provider = Wazzup24Provider(api_key=api_key, channel_id=channel_id)
        text = (
            f"Здравствуйте, {client.name}! Это Baqsy — для входа на сайт "
            f"перейдите по ссылке (действительна 15 минут):\n\n{magic_url}\n\n"
            f"Если вы не запрашивали вход — просто проигнорируйте сообщение."
        )
        provider.send_text(client.phone_wa, text)
        return "whatsapp"
    except Exception:
        log.exception("magic-link: WA delivery failed for client=%s", client.id)
        return "fallback"


class LoginLinkRequestView(APIView):
    """POST /api/v1/auth/login-link/  body: { "phone_wa": "+7 ..." }

    Возвращает 200 даже если профиль не найден — чтобы не утекали данные о
    зарегистрированных номерах. На клиенте показываем единое сообщение
    «Если номер зарегистрирован — ссылка отправлена в WhatsApp».
    """

    permission_classes = [AllowAny]
    throttle_classes = [_LoginThrottle]

    def post(self, request):
        raw = (request.data.get("phone_wa") or "").strip()
        normalized = _normalize_phone(raw)
        if not normalized or len(normalized) < 10:
            return Response(
                {"detail": "Введите корректный номер WhatsApp."},
                status=400,
            )

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
            return Response({"sent": True, "delivered_via": "noop"})

        magic = MagicLink.objects.create(
            client=client,
            requested_ip=_get_client_ip(request),
        )
        magic_url = _build_magic_url(magic.token)
        delivered_via = _send_magic_link_via_whatsapp(client, magic_url)
        magic.delivered_via = delivered_via
        magic.save(update_fields=["delivered_via", "updated_at"])

        payload = {"sent": True, "delivered_via": delivered_via}
        if delivered_via == "fallback" and getattr(settings, "DEBUG", False):
            payload["debug_url"] = magic_url
        return Response(payload)


class MagicLinkVerifyView(APIView):
    """GET /api/v1/auth/magic/<token>/

    Однократная валидация: после успешной проверки ссылка помечается
    использованной, далее клиент получает JWT-пару.
    """

    permission_classes = [AllowAny]

    def get(self, request, token: str):
        try:
            magic = MagicLink.objects.select_related("client", "client__user").get(token=token)
        except MagicLink.DoesNotExist:
            return Response({"detail": "Ссылка недействительна."}, status=404)
        if not magic.is_valid:
            reason = "expired" if magic.is_expired else "used"
            return Response(
                {
                    "detail": (
                        "Ссылка уже использована. Запросите новую."
                        if reason == "used"
                        else "Срок действия ссылки истёк (15 минут). Запросите новую."
                    ),
                    "reason": reason,
                },
                status=410,
            )
        client = magic.client
        if client.user is None:
            return Response(
                {"detail": "Профиль клиента не привязан к учётной записи."},
                status=409,
            )
        magic.used_at = timezone.now()
        magic.save(update_fields=["used_at", "updated_at"])

        refresh = RefreshToken.for_user(client.user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "client_profile_id": client.id,
                "name": client.name,
            },
            status=status.HTTP_200_OK,
        )
