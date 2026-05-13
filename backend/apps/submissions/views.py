"""Views for Submission lifecycle API."""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import ClientProfile
from apps.core.models import SiteSettings
from apps.industries.models import Industry, QuestionnaireTemplate
from apps.payments.models import Tariff
from apps.submissions.models import Submission, Answer
from apps.submissions.serializers import (
    SubmissionCreateSerializer,
    SubmissionDetailSerializer,
    QuestionSerializer,
    AnswerCreateSerializer,
)


def _get_client_profile(user):
    """Get ClientProfile linked to the JWT-authenticated user.

    Supports both legacy tg_<id>@baqsy.internal emails (bot era) and the new
    chat_<uuid>@baqsy.internal identities issued by the AI chat flow. Primary
    lookup is the reverse OneToOne from BaseUser → ClientProfile.
    """
    if not getattr(user, "is_authenticated", False):
        return None
    # Preferred path: direct FK
    profile = getattr(user, "client_profile", None)
    if profile is not None:
        return profile
    # Legacy fallback: bot-era email encoding still works for existing users
    email = getattr(user, "email", "") or ""
    if email.startswith("tg_") and email.endswith("@baqsy.internal"):
        telegram_id = email.replace("tg_", "").replace("@baqsy.internal", "")
        try:
            return ClientProfile.objects.get(telegram_id=int(telegram_id))
        except (ClientProfile.DoesNotExist, ValueError):
            return None
    return None


class SubmissionCreateView(APIView):
    """POST /api/v1/submissions/ — create a new submission."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        client = _get_client_profile(request.user)
        if not client:
            return Response(
                {"error": 403, "detail": "Профиль клиента не найден."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = SubmissionCreateSerializer(
            data=request.data,
            context={"client": client},
        )
        serializer.is_valid(raise_exception=True)
        submission = serializer.save()
        return Response(
            SubmissionDetailSerializer(submission).data,
            status=status.HTTP_201_CREATED,
        )


class StartFreeSubmissionView(APIView):
    """POST /api/v1/submissions/start-free/ — старт аудита БЕЗ оплаты.

    Доступен только когда админ выключил платёжную систему в Настройках
    платформы (SiteSettings.payments_enabled = False). Создаёт Submission
    сразу в статусе `paid` и переводит в `in_progress_full` — клиент
    может приступать к анкете.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        settings_ = SiteSettings.get_solo()
        if settings_.payments_enabled:
            return Response(
                {
                    "detail": (
                        "Свободный режим выключен. Оформите оплату через "
                        "стандартный флоу /tariffs."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        client = _get_client_profile(request.user)
        if not client:
            return Response(
                {"detail": "Профиль клиента не найден."},
                status=status.HTTP_403_FORBIDDEN,
            )

        tariff_code = (request.data.get("tariff_code") or "").strip()
        if not tariff_code:
            return Response(
                {"detail": "Не указан tariff_code."}, status=400,
            )
        try:
            tariff = Tariff.objects.get(code=tariff_code, is_active=True)
        except Tariff.DoesNotExist:
            return Response({"detail": "Тариф не найден."}, status=404)

        # Если у клиента уже есть активный заказ — возвращаем его, новый не создаём.
        existing = (
            Submission.objects.filter(client=client)
            .exclude(status__in=[Submission.Status.DELIVERED])
            .order_by("-created_at")
            .first()
        )
        if existing is not None:
            return Response(SubmissionDetailSerializer(existing).data)

        # Выбор шаблона анкеты: индустрия клиента → активный template.
        # Если индустрия не задана, берём первый активный шаблон.
        industry = client.industry
        template = None
        if industry:
            template = QuestionnaireTemplate.objects.filter(
                industry=industry, is_active=True
            ).first()
        if not template:
            template = QuestionnaireTemplate.objects.filter(is_active=True).first()
        if not template:
            return Response(
                {"detail": "В системе нет активной анкеты. Обратитесь в поддержку."},
                status=503,
            )

        submission = Submission.objects.create(
            client=client,
            template=template,
            tariff=tariff,
        )
        # Двигаем FSM: created → in_progress_basic → paid → in_progress_full
        try:
            submission.start_onboarding()
            submission.mark_paid()
            submission.start_questionnaire()
            submission.save()
        except Exception:
            # Если FSM-переход не удался — оставляем как есть, клиент сам стартанёт через чат
            pass

        return Response(
            SubmissionDetailSerializer(submission).data,
            status=status.HTTP_201_CREATED,
        )


class SubmissionDetailView(APIView):
    """GET /api/v1/submissions/{id}/ — get submission status."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        client = _get_client_profile(request.user)
        if not client:
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            submission = Submission.objects.get(id=pk, client=client)
        except Submission.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(SubmissionDetailSerializer(submission).data)


class NextQuestionView(APIView):
    """GET /api/v1/submissions/{id}/next-question/ — next unanswered question."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        client = _get_client_profile(request.user)
        if not client:
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            submission = Submission.objects.get(id=pk, client=client)
        except Submission.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        answered_ids = submission.answers.values_list("question_id", flat=True)
        next_q = (
            submission.template.questions
            .exclude(id__in=answered_ids)
            .order_by("order")
            .first()
        )

        if not next_q:
            return Response(status=status.HTTP_204_NO_CONTENT)

        total = submission.template.questions.filter(required=True).count()
        answered = submission.answers.count()
        data = QuestionSerializer(next_q).data
        data["progress"] = f"{answered}/{total}"
        return Response(data)


class AnswerCreateView(APIView):
    """POST /api/v1/submissions/{id}/answers/ — save an answer."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        client = _get_client_profile(request.user)
        if not client:
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            submission = Submission.objects.get(id=pk, client=client)
        except Submission.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = AnswerCreateSerializer(
            data=request.data,
            context={"submission": submission},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        total = submission.template.questions.filter(required=True).count()
        answered = submission.answers.count()
        return Response(
            {"progress": f"{answered}/{total}"},
            status=status.HTTP_201_CREATED,
        )


class MySubmissionView(APIView):
    """GET /api/v1/submissions/my/ — get the latest submission of the authenticated client."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        client = _get_client_profile(request.user)
        if not client:
            return Response(status=status.HTTP_403_FORBIDDEN)
        sub = Submission.objects.filter(client=client).order_by("-created_at").first()
        if not sub:
            return Response(
                {"detail": "Нет активных заказов."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(SubmissionDetailSerializer(sub).data)


class SubmissionCompleteView(APIView):
    """POST /api/v1/submissions/{id}/complete/ — mark questionnaire complete."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        client = _get_client_profile(request.user)
        if not client:
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            submission = Submission.objects.get(id=pk, client=client)
        except Submission.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # Check all required questions answered
        required_ids = set(
            submission.template.questions
            .filter(required=True)
            .values_list("id", flat=True)
        )
        answered_ids = set(submission.answers.values_list("question_id", flat=True))
        missing = required_ids - answered_ids
        if missing:
            return Response(
                {"error": 400, "detail": f"Не отвечено на {len(missing)} обязательных вопрос(ов)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            submission.complete_questionnaire()
            submission.save()
        except Exception as e:
            return Response(
                {"error": 400, "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(SubmissionDetailSerializer(submission).data)
