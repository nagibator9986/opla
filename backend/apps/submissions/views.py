"""Views for Submission lifecycle API."""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import ClientProfile
from apps.submissions.models import Submission, Answer
from apps.submissions.serializers import (
    SubmissionCreateSerializer,
    SubmissionDetailSerializer,
    QuestionSerializer,
    AnswerCreateSerializer,
)


def _get_client_profile(user):
    """Get ClientProfile for JWT-authenticated user (tg_*@baqsy.internal)."""
    email = user.email
    if not email.startswith("tg_") or not email.endswith("@baqsy.internal"):
        return None
    telegram_id = email.replace("tg_", "").replace("@baqsy.internal", "")
    try:
        return ClientProfile.objects.get(telegram_id=int(telegram_id))
    except (ClientProfile.DoesNotExist, ValueError):
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
