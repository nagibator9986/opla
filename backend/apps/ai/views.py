"""Public chat endpoints — consumed by the React landing widget."""
from __future__ import annotations

from django.db import transaction
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from apps.accounts.models import BaseUser, ClientProfile
from apps.ai.models import AIAssistantConfig, ChatMessage, ChatSession
from apps.ai.serializers import (
    AIConfigPublicSerializer,
    ChatCollectDataSerializer,
    ChatMessageInputSerializer,
    ChatSessionSerializer,
    ChatStartSerializer,
)
from apps.ai.services import chat_completion, extract_client_data, render_system_prompt
from apps.industries.models import Industry


class ChatRateThrottle(AnonRateThrottle):
    """Per-IP rate limit for the anon chat endpoint. 30 req/min is tolerant
    but blocks obvious abuse (the underlying OpenAI API costs real money)."""

    rate = "30/min"


class AIConfigView(APIView):
    """GET /api/v1/chat/config/ — fetch greeting + quick-replies for chat widget."""

    permission_classes = [AllowAny]

    def get(self, request):
        cfg = AIAssistantConfig.get_active()
        if cfg is None:
            return Response(
                {
                    "name": "Baqsy AI",
                    "greeting": (
                        "Здравствуйте! Я AI-ассистент Baqsy. Сейчас настраиваюсь — "
                        "напишите на info@baqsy.kz, мы ответим вручную."
                    ),
                    "quick_replies": [],
                }
            )
        return Response(AIConfigPublicSerializer(cfg).data)


class ChatStartView(APIView):
    """POST /api/v1/chat/start/ — create a new session and return its id+greeting."""

    permission_classes = [AllowAny]
    throttle_classes = [ChatRateThrottle]

    def post(self, request):
        serializer = ChatStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cfg = AIAssistantConfig.get_active()
        greeting = (cfg.greeting if cfg else "Здравствуйте!").strip()
        quick_replies = cfg.quick_replies if cfg else []

        session = ChatSession.objects.create(
            last_user_agent=(request.META.get("HTTP_USER_AGENT") or "")[:255],
            last_ip=_get_client_ip(request),
        )
        ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.ASSISTANT,
            content=greeting,
        )
        return Response(
            {
                "session_id": str(session.id),
                "greeting": greeting,
                "quick_replies": quick_replies,
            },
            status=status.HTTP_201_CREATED,
        )


class ChatMessageView(APIView):
    """POST /api/v1/chat/message/ — append user message, get assistant reply."""

    permission_classes = [AllowAny]
    throttle_classes = [ChatRateThrottle]

    def post(self, request):
        serializer = ChatMessageInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session_id = serializer.validated_data["session_id"]
        user_content = serializer.validated_data["content"].strip()
        if not user_content:
            return Response({"detail": "Пустое сообщение"}, status=400)

        try:
            session = ChatSession.objects.get(pk=session_id)
        except (ChatSession.DoesNotExist, ValueError):
            return Response({"detail": "Сессия не найдена"}, status=404)

        cfg = AIAssistantConfig.get_active()
        if cfg is None:
            return Response(
                {
                    "detail": (
                        "AI-ассистент не настроен администратором. "
                        "Напишите нам на info@baqsy.kz."
                    )
                },
                status=503,
            )

        # Opportunistic data extraction (phone number, etc.)
        collected = dict(session.collected_data or {})
        extracted = extract_client_data(user_content)
        if extracted:
            collected.update(extracted)

        # Build message history for OpenAI
        system_prompt = render_system_prompt(cfg.system_prompt, collected)
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in session.messages.all().order_by("created_at")
        ]
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_content})

        # Persist user message immediately so it's not lost if OpenAI errors
        user_msg = ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.USER,
            content=user_content,
        )

        try:
            reply_text, tokens_used = chat_completion(
                model=cfg.model,
                temperature=cfg.temperature,
                max_tokens=cfg.max_tokens,
                messages=messages,
            )
        except RuntimeError as exc:
            return Response({"detail": str(exc)}, status=502)

        reply_msg = ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.ASSISTANT,
            content=reply_text,
            tokens_used=tokens_used,
        )

        # Save any newly extracted data
        if collected != (session.collected_data or {}):
            session.collected_data = collected
            session.save(update_fields=["collected_data", "updated_at"])

        return Response(
            {
                "reply": {
                    "id": reply_msg.id,
                    "role": reply_msg.role,
                    "content": reply_msg.content,
                    "created_at": reply_msg.created_at,
                },
                "user_message_id": user_msg.id,
            }
        )


class ChatCollectView(APIView):
    """POST /api/v1/chat/collect/ — frontend pushes structured onboarding data
    when the user confirms the gathered fields in the sidebar form."""

    permission_classes = [AllowAny]
    throttle_classes = [ChatRateThrottle]

    def post(self, request):
        serializer = ChatCollectDataSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        session_id = data.pop("session_id")

        try:
            session = ChatSession.objects.get(pk=session_id)
        except (ChatSession.DoesNotExist, ValueError):
            return Response({"detail": "Сессия не найдена"}, status=404)

        collected = dict(session.collected_data or {})
        for k, v in data.items():
            if v:
                collected[k] = v
        session.collected_data = collected

        # If we now have enough to create a ClientProfile, do it
        required = ("name", "company")
        has_required = all(collected.get(r) for r in required)
        if has_required and session.client_id is None:
            industry = None
            code = collected.get("industry_code")
            if code:
                industry = Industry.objects.filter(code=code, is_active=True).first()
            client = ClientProfile.objects.create(
                name=collected["name"],
                company=collected["company"],
                phone_wa=collected.get("phone_wa", "") or "",
                city=collected.get("city", "") or "",
                industry=industry,
            )
            # Synthetic BaseUser for JWT issuance
            email = f"chat_{session.id}@baqsy.internal"
            user, _ = BaseUser.objects.get_or_create(
                email=email, defaults={"is_active": True}
            )
            client.user = user
            client.save(update_fields=["user"])
            session.client = client
            session.status = ChatSession.Status.QUALIFIED

        session.save()
        return Response(ChatSessionSerializer(session).data)


class ChatAuthTokenView(APIView):
    """POST /api/v1/chat/auth-token/ — issues JWT for a qualified session.

    The landing chat calls this after collect returns a session with a linked
    ClientProfile — lets the user jump to /cabinet with authentication.
    """

    permission_classes = [AllowAny]
    throttle_classes = [ChatRateThrottle]

    def post(self, request):
        session_id = request.data.get("session_id")
        if not session_id:
            return Response({"detail": "session_id required"}, status=400)
        try:
            session = ChatSession.objects.select_related("client").get(pk=session_id)
        except (ChatSession.DoesNotExist, ValueError):
            return Response({"detail": "Сессия не найдена"}, status=404)
        if session.client_id is None or session.client.user_id is None:
            return Response(
                {"detail": "Профиль ещё не создан — заполните данные"},
                status=400,
            )
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(session.client.user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "client_profile_id": session.client.id,
                "name": session.client.name,
            }
        )


def _get_client_ip(request) -> str | None:
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
