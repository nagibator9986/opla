"""Public chat endpoints — consumed by the React landing widget.

The widget uses the same `session_id` for the whole journey:
    1. Anonymous chat with OpenAI (mode="chat")
    2. Profile data gathered → `/chat/collect/` → JWT issued
    3. Tariff paid → `/chat/start-questionnaire/` (mode switches to "questionnaire")
    4. Each `/chat/message/` is treated as an answer to the current question;
       the bot replies with the next question until the template is complete.
"""
from __future__ import annotations

import logging

from django.db import transaction
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from apps.accounts.models import BaseUser, ClientProfile
from apps.ai.models import AIAssistantConfig, ChatMessage, ChatSession
from apps.ai.questionnaire import (
    next_question,
    render_completion,
    render_intro,
    save_answer,
    try_complete,
    visible_questions_for,
)
from apps.ai.serializers import (
    AIConfigPublicSerializer,
    ChatCollectDataSerializer,
    ChatMessageInputSerializer,
    ChatSessionSerializer,
    ChatStartSerializer,
)
from apps.ai.services import chat_completion, extract_client_data, render_system_prompt
from apps.industries.models import Industry, Question, QuestionnaireTemplate
from apps.submissions.models import Submission

log = logging.getLogger(__name__)


class ChatRateThrottle(AnonRateThrottle):
    """Per-IP rate limit for the anon chat endpoint."""

    rate = "60/min"


class AIConfigView(APIView):
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
    permission_classes = [AllowAny]
    throttle_classes = [ChatRateThrottle]

    def post(self, request):
        serializer = ChatStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cfg = AIAssistantConfig.get_active()
        client_profile = _resolve_authenticated_client(request)

        if client_profile is not None:
            greeting, quick_replies = _build_authed_chat_intro(client_profile)
        else:
            greeting = (cfg.greeting if cfg else "Здравствуйте!").strip()
            quick_replies = cfg.quick_replies if cfg else []

        session = ChatSession.objects.create(
            client=client_profile,
            last_user_agent=(request.META.get("HTTP_USER_AGENT") or "")[:255],
            last_ip=_get_client_ip(request),
        )
        if client_profile is not None:
            session.collected_data = {
                "name": client_profile.name or "",
                "company": client_profile.company or "",
                "phone_wa": client_profile.phone_wa or "",
                "city": client_profile.city or "",
            }
            session.status = ChatSession.Status.QUALIFIED
            session.save(update_fields=["collected_data", "status", "updated_at"])

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
                "mode": session.mode,
                "is_authenticated": client_profile is not None,
            },
            status=status.HTTP_201_CREATED,
        )


class ChatMessageView(APIView):
    """POST /api/v1/chat/message/ — dispatches to chat OR questionnaire mode."""

    permission_classes = [AllowAny]
    throttle_classes = [ChatRateThrottle]

    def post(self, request):
        serializer = ChatMessageInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session_id = serializer.validated_data["session_id"]
        user_content = serializer.validated_data["content"]

        try:
            session = ChatSession.objects.select_related("submission", "client").get(pk=session_id)
        except (ChatSession.DoesNotExist, ValueError):
            return Response({"detail": "Сессия не найдена"}, status=404)

        if session.mode == ChatSession.Mode.QUESTIONNAIRE and session.submission_id:
            return _questionnaire_answer(session, user_content)

        return _freeform_chat(session, user_content)


class ChatCollectView(APIView):
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

        # Регистрация = Этап I (паспорт компании) + Этап II (роль)
        # JWT выдаём только когда клиент прошёл оба этапа целиком.
        required = (
            "name", "company", "industry_field", "city",
            "employees_count", "company_age", "role",
        )
        if all(collected.get(r) for r in required) and session.client_id is None:
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


class StartQuestionnaireView(APIView):
    """POST /api/v1/chat/start-questionnaire/ — начинает пошаговый опросник.

    Ожидает:
        session_id — UUID сессии чата клиента
        submission_id — id оплаченной заявки (из /submissions/my/)

    Проверяет, что Submission действительно оплачен (status in paid /
    in_progress_full) и принадлежит тому же ClientProfile. Переключает
    режим чата в «questionnaire», выдаёт intro-сообщение + первый вопрос.
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [ChatRateThrottle]

    @transaction.atomic
    def post(self, request):
        session_id = request.data.get("session_id")
        submission_id = request.data.get("submission_id")
        if not session_id or not submission_id:
            return Response(
                {"detail": "session_id и submission_id обязательны."}, status=400
            )

        try:
            session = ChatSession.objects.select_for_update().get(pk=session_id)
        except (ChatSession.DoesNotExist, ValueError):
            return Response({"detail": "Сессия не найдена."}, status=404)

        try:
            submission = Submission.objects.select_related(
                "client", "template"
            ).get(pk=submission_id)
        except (Submission.DoesNotExist, ValueError):
            return Response({"detail": "Заявка не найдена."}, status=404)

        if session.client_id != submission.client_id:
            return Response(
                {"detail": "Заявка не принадлежит этой сессии."}, status=403
            )

        allowed_start = {
            Submission.Status.PAID,
            Submission.Status.IN_PROGRESS_FULL,
        }
        if submission.status not in allowed_start:
            return Response(
                {
                    "detail": (
                        "Анкету можно начать только после оплаты тарифа. "
                        f"Текущий статус заказа: {submission.get_status_display()}."
                    )
                },
                status=400,
            )

        if submission.status == Submission.Status.PAID:
            try:
                submission.start_questionnaire()
                submission.save()
            except Exception as exc:
                log.warning(
                    "start-questionnaire: FSM transition failed sub=%s: %s",
                    submission.id, exc,
                )

        session.mode = ChatSession.Mode.QUESTIONNAIRE
        session.submission = submission
        session.status = ChatSession.Status.QUESTIONNAIRE
        session.save(update_fields=["mode", "submission", "status", "updated_at"])

        total = len(visible_questions_for(submission))
        intro = render_intro(submission.template, submission, total)
        ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.ASSISTANT,
            content=intro,
        )

        current = next_question(submission)
        next_payload = current.to_payload() if current else None
        if current:
            prefix = f"[{current.stage}] " if current.stage else ""
            ChatMessage.objects.create(
                session=session,
                role=ChatMessage.Role.ASSISTANT,
                content=prefix + current.text,
            )

        return Response(
            {
                "session_id": str(session.id),
                "intro": intro,
                "mode": session.mode,
                "submission_id": str(submission.id),
                "next_question": next_payload,
            }
        )


# ──────────────────────────────────────────────────────────────────────────


def _freeform_chat(session: ChatSession, user_content: str):
    """Original OpenAI-driven chat path."""
    user_content = (user_content or "").strip()
    if not user_content:
        return Response({"detail": "Пустое сообщение"}, status=400)

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

    collected = dict(session.collected_data or {})
    extracted = extract_client_data(user_content)
    if extracted:
        collected.update(extracted)

    system_prompt = render_system_prompt(cfg.system_prompt, collected)

    # Расширенный контекст для зарегистрированного клиента: мы знаем имя,
    # компанию, роль — значит GPT не должен повторно собирать первичные
    # данные. Должен вести экспертный диалог и направлять к оплате.
    is_registered = session.client_id is not None or bool(collected.get("role"))
    if is_registered:
        client_name = (
            (collected.get("name") or "")
            or (session.client.name if session.client else "")
        ).strip()
        first_name = client_name.split()[0] if client_name else ""
        client_company = (
            (collected.get("company") or "")
            or (session.client.company if session.client else "")
        ).strip()
        client_role = (collected.get("role") or "").strip()
        client_industry = (collected.get("industry_field") or "").strip()
        system_prompt += (
            "\n\n[РЕЖИМ: ЗАРЕГИСТРИРОВАННЫЙ КЛИЕНТ — экспертный диалог]\n"
            f"Клиент уже прошёл регистрацию: имя — {client_name or '—'}, "
            f"компания — «{client_company or '—'}», роль — {client_role or '—'}, "
            f"сфера — {client_industry or '—'}.\n"
            "ВАЖНЫЕ ПРАВИЛА:\n"
            "1. НЕ собирай первичные данные заново (имя, компанию, роль, сферу — "
            "ты их уже знаешь). НЕ говори «давайте познакомимся» или «как вас зовут».\n"
            f"2. Обращайся к клиенту по имени ({first_name or 'коллега'}).\n"
            "3. Веди экспертный диалог по методу Baqsy / Коду Вечного Иля. "
            "Отвечай развёрнуто на любые вопросы про:\n"
            "   — суть метода (12 параметров аудита, Bün — скрытые сбои, ТҢРІ — равновесие);\n"
            "   — что входит в финальный PDF-отчёт (анализ по 27 параметрам, риски, рекомендации);\n"
            "   — сроки (3–5 рабочих дней от оплаты до получения отчёта в WhatsApp);\n"
            "   — отрасли (метод адаптируется под ритейл, IT, производство, услуги, F&B);\n"
            "   — формат анкеты (бот задаёт ~100 вопросов по одному, можно прерывать).\n"
            "4. Когда клиент готов оплатить или спрашивает про цены — мягко "
            "направляй к покупке: «Перейдите на страницу /tariffs — там обе опции "
            "доступны» или «нажмите кнопку \"Заказать аудит\" в верхней части чата».\n"
            "5. Доступные пакеты:\n"
            "   • Ashide 1 — 199$ — для одного руководителя, 7–9 ключевых параметров;\n"
            "   • Ashino + Ashide — 799$ — для команды 3–7 человек, 18–24 параметра, "
            "групповая динамика и сравнение мнений.\n"
            "6. Если клиент задаёт нетипичный вопрос — отвечай профессионально, "
            "опирайся на философию метода, но без фантазий: если не уверен — "
            "предложи связаться с экспертом через кнопку «Личный кабинет».\n"
            "7. Тон — деловой, тёплый, без воды. Не более 4–5 абзацев на ответ."
        )
    history = [
        {"role": msg.role, "content": msg.content}
        for msg in session.messages.all().order_by("created_at")
    ]
    messages = [{"role": "system", "content": system_prompt}] + history + [
        {"role": "user", "content": user_content}
    ]

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
        # 503 = service unavailable. Used when OpenAI isn't configured, SDK not
        # installed, or OpenAI returned an error. The message in `exc` is already
        # a user-facing Russian string set in apps/ai/services.py.
        return Response({"detail": str(exc)}, status=503)

    reply_msg = ChatMessage.objects.create(
        session=session,
        role=ChatMessage.Role.ASSISTANT,
        content=reply_text,
        tokens_used=tokens_used,
    )

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
            "mode": session.mode,
        }
    )


def _questionnaire_answer(session: ChatSession, raw_content):
    """Handle the user's answer to the current question and return the next one."""
    submission = session.submission
    if not submission:
        return Response({"detail": "Сессия не привязана к заявке."}, status=400)

    current = next_question(submission)
    if current is None:
        # Already complete — send closing message if not yet sent.
        total = len(visible_questions_for(submission))
        closing = render_completion(submission.template, submission, total)
        return Response(
            {
                "mode": session.mode,
                "next_question": None,
                "completed": True,
                "reply": {"role": "assistant", "content": closing},
            }
        )

    # Parse/coerce
    try:
        question = submission.template.questions.get(pk=current.question_id)
    except Question.DoesNotExist:
        return Response({"detail": "Вопрос не найден."}, status=500)

    try:
        save_answer(submission, question, raw_content)
    except ValueError as exc:
        # Keep user message visible + echo back the validation issue
        ChatMessage.objects.create(
            session=session, role=ChatMessage.Role.USER,
            content=_stringify_answer(raw_content),
        )
        note = ChatMessage.objects.create(
            session=session, role=ChatMessage.Role.ASSISTANT,
            content=f"{exc} Попробуйте ещё раз — вот тот же вопрос:",
        )
        return Response(
            {
                "mode": session.mode,
                "validation_error": str(exc),
                "reply": {
                    "role": "assistant",
                    "id": note.id,
                    "content": note.content,
                },
                "next_question": current.to_payload(),
            }
        )

    # Record the user's answer in chat history
    ChatMessage.objects.create(
        session=session, role=ChatMessage.Role.USER,
        content=_stringify_answer(raw_content),
    )

    # Completed?
    if try_complete(submission):
        total = len(visible_questions_for(submission))
        closing = render_completion(submission.template, submission, total)
        ChatMessage.objects.create(
            session=session, role=ChatMessage.Role.ASSISTANT, content=closing,
        )
        session.status = ChatSession.Status.COMPLETED
        session.save(update_fields=["status", "updated_at"])
        return Response(
            {
                "mode": session.mode,
                "completed": True,
                "reply": {"role": "assistant", "content": closing},
                "next_question": None,
            }
        )

    # Otherwise, serve next question
    upcoming = next_question(submission)
    if upcoming is None:
        # Edge: required answered, but non-required remain. Treat as complete.
        closing = render_completion(
            submission.template, submission, len(visible_questions_for(submission))
        )
        return Response(
            {
                "mode": session.mode,
                "completed": True,
                "reply": {"role": "assistant", "content": closing},
                "next_question": None,
            }
        )

    prefix = f"[{upcoming.stage}] " if upcoming.stage else ""
    bot_msg = ChatMessage.objects.create(
        session=session,
        role=ChatMessage.Role.ASSISTANT,
        content=prefix + upcoming.text,
    )
    return Response(
        {
            "mode": session.mode,
            "completed": False,
            "reply": {
                "role": "assistant",
                "id": bot_msg.id,
                "content": bot_msg.content,
            },
            "next_question": upcoming.to_payload(),
        }
    )


def _stringify_answer(raw) -> str:
    if isinstance(raw, list):
        return ", ".join(str(x) for x in raw)
    return str(raw)


def _get_client_ip(request) -> str | None:
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _resolve_authenticated_client(request):
    """Try to identify ClientProfile from JWT in Authorization header.

    Endpoint is `permission_classes=[AllowAny]`, so DRF won't authenticate
    automatically — but if a Bearer token is present and valid, we can resolve
    it manually. Returns ClientProfile or None.
    """
    try:
        from rest_framework_simplejwt.authentication import JWTAuthentication
    except ImportError:
        return None
    auth = JWTAuthentication()
    try:
        result = auth.authenticate(request)
    except Exception:  # invalid / expired token
        return None
    if result is None:
        return None
    user, _token = result
    if not user or not getattr(user, "is_authenticated", False):
        return None
    return ClientProfile.objects.filter(user=user).first()


def _build_authed_chat_intro(client) -> tuple[str, list[dict]]:
    """Build personalized greeting + quick-replies for a registered client.

    Greeting is editable in admin via ContentBlock `chat_greeting_authed`
    with placeholders {{name}}, {{company}}.
    """
    from apps.content.models import ContentBlock

    block = ContentBlock.objects.filter(
        key="chat_greeting_authed", is_active=True
    ).first()
    template = (
        block.content
        if block and block.content
        else (
            "Здравствуйте, {{name}}! Я Baqsy AI — ваш персональный помощник по "
            "Коду Вечного Иля. Профиль уже настроен, я знаю всё про «{{company}}». "
            "Чем могу помочь — подробнее рассказать про метод, ответить на вопрос "
            "или сразу перейти к заказу аудита?"
        )
    )
    name = (client.name or "").strip()
    first_name = name.split()[0] if name else ""
    company = (client.company or "—").strip()
    greeting = (
        template.replace("{{name}}", first_name or name or "коллега")
        .replace("{{company}}", company)
    )

    quick_replies = [
        {"label": "Заказать аудит", "payload": "/tariffs", "action": "navigate"},
        {"label": "Что входит в отчёт?", "payload": "Расскажи подробно, что входит в итоговый PDF-отчёт по аудиту.", "action": "message"},
        {"label": "Сколько по времени?", "payload": "Сколько времени занимает подготовка аудита от оплаты до получения отчёта?", "action": "message"},
        {"label": "Чем Ashide 1 отличается от Ashino + Ashide?", "payload": "Чем Ashide 1 отличается от пакета Ashino + Ashide и кому что подходит?", "action": "message"},
        {"label": "Личный кабинет", "payload": "/cabinet", "action": "navigate"},
    ]
    return greeting, quick_replies
