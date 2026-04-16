---
phase: 02-core-rest-api
plan: 03
type: execute
wave: 2
title: "Submission lifecycle API — create, next-question, answer, complete, status"
depends_on: [00, 01]
requirements: [API-05, API-06, API-07, API-08, API-09]
autonomous: true
files_modified:
  - backend/apps/submissions/serializers.py
  - backend/apps/submissions/views.py
  - backend/apps/submissions/urls.py
  - backend/apps/submissions/tests/test_api.py
nyquist_compliant: true
---

# Plan 03: Submission Lifecycle API

## Goal

Full CRUD lifecycle for Submission through REST: create submission, get next unanswered question, save answer with validation, complete questionnaire with FSM transition, get submission status. Client sees only their own submissions.

## must_haves

- POST /submissions/ creates Submission linked to active template + tariff
- GET /submissions/{id}/next-question/ returns first unanswered question or 204
- POST /submissions/{id}/answers/ validates by field_type and saves Answer
- POST /submissions/{id}/complete/ triggers FSM transition and checks all required questions answered
- GET /submissions/{id}/ returns status, progress, template info
- Client can only access their own submissions
- All 5 requirements (API-05..09) tested with full lifecycle integration test

## Tasks

<task id="03-01">
<title>Create submission serializers</title>
<read_first>
- backend/apps/submissions/models.py (Submission, Answer, FSM)
- backend/apps/industries/models.py (Question field_type, options)
- .planning/phases/02-core-rest-api/02-CONTEXT.md (serializer approach, answer validation)
</read_first>
<action>
Create `backend/apps/submissions/serializers.py`:

```python
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.industries.models import Industry, QuestionnaireTemplate, Question
from apps.payments.models import Tariff
from apps.submissions.models import Submission, Answer


class SubmissionCreateSerializer(serializers.Serializer):
    industry_code = serializers.CharField(max_length=50)
    tariff_code = serializers.CharField(max_length=50)

    def validate_industry_code(self, value):
        try:
            return Industry.objects.get(code=value, is_active=True)
        except Industry.DoesNotExist:
            raise serializers.ValidationError("Отрасль не найдена.")

    def validate_tariff_code(self, value):
        try:
            return Tariff.objects.get(code=value, is_active=True)
        except Tariff.DoesNotExist:
            raise serializers.ValidationError("Тариф не найден.")

    def create(self, validated_data):
        industry = validated_data["industry_code"]
        tariff = validated_data["tariff_code"]
        client = self.context["client"]

        template = QuestionnaireTemplate.objects.filter(
            industry=industry, is_active=True
        ).first()
        if not template:
            raise serializers.ValidationError(
                {"industry_code": "Для этой отрасли нет активной анкеты."}
            )

        return Submission.objects.create(
            client=client,
            template=template,
            tariff=tariff,
        )


class SubmissionDetailSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source="template.name", read_only=True)
    industry_name = serializers.CharField(source="template.industry.name", read_only=True)
    total_questions = serializers.SerializerMethodField()
    answered_count = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = [
            "id", "status", "template_name", "industry_name",
            "total_questions", "answered_count",
            "created_at", "completed_at",
        ]
        read_only_fields = fields

    def get_total_questions(self, obj):
        return obj.template.questions.filter(required=True).count()

    def get_answered_count(self, obj):
        return obj.answers.count()


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "order", "text", "field_type", "options", "block", "required"]
        read_only_fields = fields


class AnswerCreateSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    value = serializers.JSONField()

    def validate(self, data):
        submission = self.context["submission"]
        try:
            question = submission.template.questions.get(id=data["question_id"])
        except Question.DoesNotExist:
            raise serializers.ValidationError(
                {"question_id": "Вопрос не принадлежит этой анкете."}
            )

        # Check duplicate
        if Answer.objects.filter(submission=submission, question=question).exists():
            raise serializers.ValidationError(
                {"question_id": "Ответ на этот вопрос уже сохранён."}
            )

        # Validate value by field_type
        value = data["value"]
        ft = question.field_type

        if ft == "text":
            if not isinstance(value, dict) or "text" not in value:
                raise serializers.ValidationError(
                    {"value": 'Ожидается формат {"text": "..."}'}
                )
        elif ft == "number":
            if not isinstance(value, dict) or "number" not in value:
                raise serializers.ValidationError(
                    {"value": 'Ожидается формат {"number": N}'}
                )
            if not isinstance(value["number"], (int, float)):
                raise serializers.ValidationError(
                    {"value": "number должен быть числом."}
                )
        elif ft == "choice":
            if not isinstance(value, dict) or "choice" not in value:
                raise serializers.ValidationError(
                    {"value": 'Ожидается формат {"choice": "option"}'}
                )
            valid_choices = question.options.get("choices", [])
            if valid_choices and value["choice"] not in valid_choices:
                raise serializers.ValidationError(
                    {"value": f"Выбор должен быть одним из: {valid_choices}"}
                )
        elif ft == "multichoice":
            if not isinstance(value, dict) or "choices" not in value:
                raise serializers.ValidationError(
                    {"value": 'Ожидается формат {"choices": ["a", "b"]}'}
                )
            if not isinstance(value["choices"], list):
                raise serializers.ValidationError(
                    {"value": "choices должен быть списком."}
                )
            valid_choices = question.options.get("choices", [])
            if valid_choices:
                invalid = set(value["choices"]) - set(valid_choices)
                if invalid:
                    raise serializers.ValidationError(
                        {"value": f"Недопустимые варианты: {invalid}"}
                    )

        data["question"] = question
        return data

    def create(self, validated_data):
        return Answer.objects.create(
            submission=self.context["submission"],
            question=validated_data["question"],
            value=validated_data["value"],
        )
```
</action>
<acceptance_criteria>
- `backend/apps/submissions/serializers.py` contains `class SubmissionCreateSerializer`
- `backend/apps/submissions/serializers.py` contains `class SubmissionDetailSerializer`
- `backend/apps/submissions/serializers.py` contains `class AnswerCreateSerializer`
- `backend/apps/submissions/serializers.py` contains `class QuestionSerializer`
- `backend/apps/submissions/serializers.py` contains `if ft == "text":`
- `backend/apps/submissions/serializers.py` contains `if ft == "choice":`
</acceptance_criteria>
</task>

<task id="03-02">
<title>Create submission views</title>
<read_first>
- backend/apps/submissions/serializers.py
- backend/apps/submissions/models.py (FSM transitions)
- backend/apps/accounts/models.py (ClientProfile)
</read_first>
<action>
Create `backend/apps/submissions/views.py`:

```python
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
```

Update `backend/apps/submissions/urls.py`:
```python
from django.urls import path
from apps.submissions.views import (
    SubmissionCreateView,
    SubmissionDetailView,
    NextQuestionView,
    AnswerCreateView,
    SubmissionCompleteView,
)

urlpatterns = [
    path("", SubmissionCreateView.as_view(), name="submission-create"),
    path("<uuid:pk>/", SubmissionDetailView.as_view(), name="submission-detail"),
    path("<uuid:pk>/next-question/", NextQuestionView.as_view(), name="submission-next-question"),
    path("<uuid:pk>/answers/", AnswerCreateView.as_view(), name="submission-answer"),
    path("<uuid:pk>/complete/", SubmissionCompleteView.as_view(), name="submission-complete"),
]
```
</action>
<acceptance_criteria>
- `backend/apps/submissions/views.py` contains `class SubmissionCreateView(APIView):`
- `backend/apps/submissions/views.py` contains `class NextQuestionView(APIView):`
- `backend/apps/submissions/views.py` contains `class AnswerCreateView(APIView):`
- `backend/apps/submissions/views.py` contains `class SubmissionCompleteView(APIView):`
- `backend/apps/submissions/urls.py` contains `<uuid:pk>`
- `backend/apps/submissions/urls.py` contains `path("", SubmissionCreateView`
</acceptance_criteria>
</task>

<task id="03-03">
<title>Write full lifecycle integration test</title>
<read_first>
- backend/apps/submissions/views.py
- backend/apps/submissions/serializers.py
- backend/tests/factories.py
</read_first>
<action>
Create `backend/apps/submissions/tests/test_api.py`:

```python
import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import BaseUser, ClientProfile
from apps.industries.models import Industry, QuestionnaireTemplate, Question
from apps.payments.models import Tariff


@pytest.fixture
def authenticated_client(db):
    """Create a client profile with JWT-authenticated APIClient."""
    industry = Industry.objects.create(name="IT", code="it", is_active=True)
    template = QuestionnaireTemplate.objects.create(
        industry=industry, version=1, is_active=True, name="IT v1"
    )
    Question.objects.create(template=template, order=1, text="Name?", field_type="text", block="A", required=True)
    Question.objects.create(template=template, order=2, text="Revenue?", field_type="choice", block="A", required=True,
                            options={"choices": ["<100k", "100k-1M", ">1M"]})
    Question.objects.create(template=template, order=3, text="Describe", field_type="text", block="B", required=False)

    Tariff.objects.create(code="ashide_1", title="Ashide 1", price_kzt=45000, is_active=True)

    profile = ClientProfile.objects.create(telegram_id=12345, name="Test", company="TestCo", industry=industry)
    user = BaseUser.objects.create_user(email="tg_12345@baqsy.internal")
    refresh = RefreshToken.for_user(user)

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client, profile


@pytest.mark.django_db
class TestSubmissionLifecycle:
    def test_create_submission(self, authenticated_client):
        client, profile = authenticated_client
        response = client.post(
            "/api/v1/submissions/",
            {"industry_code": "it", "tariff_code": "ashide_1"},
            format="json",
        )
        assert response.status_code == 201
        assert response.data["status"] == "created"
        assert response.data["total_questions"] == 2  # only required

    def test_next_question(self, authenticated_client):
        client, profile = authenticated_client
        resp = client.post("/api/v1/submissions/", {"industry_code": "it", "tariff_code": "ashide_1"}, format="json")
        sub_id = resp.data["id"]
        resp = client.get(f"/api/v1/submissions/{sub_id}/next-question/")
        assert resp.status_code == 200
        assert resp.data["order"] == 1
        assert resp.data["progress"] == "0/2"

    def test_save_answer(self, authenticated_client):
        client, profile = authenticated_client
        resp = client.post("/api/v1/submissions/", {"industry_code": "it", "tariff_code": "ashide_1"}, format="json")
        sub_id = resp.data["id"]
        q_resp = client.get(f"/api/v1/submissions/{sub_id}/next-question/")
        q_id = q_resp.data["id"]
        resp = client.post(
            f"/api/v1/submissions/{sub_id}/answers/",
            {"question_id": q_id, "value": {"text": "My Company"}},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["progress"] == "1/2"

    def test_complete_submission(self, authenticated_client):
        client, profile = authenticated_client
        resp = client.post("/api/v1/submissions/", {"industry_code": "it", "tariff_code": "ashide_1"}, format="json")
        sub_id = resp.data["id"]

        # Answer all required questions
        for _ in range(2):
            q = client.get(f"/api/v1/submissions/{sub_id}/next-question/")
            if q.status_code == 204:
                break
            q_id = q.data["id"]
            ft = q.data["field_type"]
            if ft == "text":
                value = {"text": "answer"}
            elif ft == "choice":
                value = {"choice": q.data["options"]["choices"][0]}
            else:
                value = {"text": "fallback"}
            client.post(f"/api/v1/submissions/{sub_id}/answers/", {"question_id": q_id, "value": value}, format="json")

        resp = client.post(f"/api/v1/submissions/{sub_id}/complete/", format="json")
        assert resp.status_code == 200
        assert resp.data["status"] == "completed"

    def test_get_submission_status(self, authenticated_client):
        client, profile = authenticated_client
        resp = client.post("/api/v1/submissions/", {"industry_code": "it", "tariff_code": "ashide_1"}, format="json")
        sub_id = resp.data["id"]
        resp = client.get(f"/api/v1/submissions/{sub_id}/")
        assert resp.status_code == 200
        assert "status" in resp.data
        assert "total_questions" in resp.data

    def test_cannot_access_other_client_submission(self, authenticated_client):
        client, profile = authenticated_client
        # Create another profile's submission
        other_profile = ClientProfile.objects.create(telegram_id=99999, name="Other", company="OtherCo")
        from apps.submissions.models import Submission
        from apps.industries.models import QuestionnaireTemplate
        template = QuestionnaireTemplate.objects.first()
        other_sub = Submission.objects.create(client=other_profile, template=template)
        resp = client.get(f"/api/v1/submissions/{other_sub.id}/")
        assert resp.status_code == 404

    def test_complete_without_all_answers_returns_400(self, authenticated_client):
        client, profile = authenticated_client
        resp = client.post("/api/v1/submissions/", {"industry_code": "it", "tariff_code": "ashide_1"}, format="json")
        sub_id = resp.data["id"]
        resp = client.post(f"/api/v1/submissions/{sub_id}/complete/", format="json")
        assert resp.status_code == 400

    def test_duplicate_answer_returns_400(self, authenticated_client):
        client, profile = authenticated_client
        resp = client.post("/api/v1/submissions/", {"industry_code": "it", "tariff_code": "ashide_1"}, format="json")
        sub_id = resp.data["id"]
        q = client.get(f"/api/v1/submissions/{sub_id}/next-question/")
        q_id = q.data["id"]
        client.post(f"/api/v1/submissions/{sub_id}/answers/", {"question_id": q_id, "value": {"text": "answer"}}, format="json")
        resp = client.post(f"/api/v1/submissions/{sub_id}/answers/", {"question_id": q_id, "value": {"text": "again"}}, format="json")
        assert resp.status_code == 400

    def test_next_question_returns_204_when_all_answered(self, authenticated_client):
        client, profile = authenticated_client
        resp = client.post("/api/v1/submissions/", {"industry_code": "it", "tariff_code": "ashide_1"}, format="json")
        sub_id = resp.data["id"]
        # Answer all 3 questions (2 required + 1 optional)
        for _ in range(3):
            q = client.get(f"/api/v1/submissions/{sub_id}/next-question/")
            if q.status_code == 204:
                break
            q_id = q.data["id"]
            ft = q.data["field_type"]
            if ft == "text":
                value = {"text": "ans"}
            elif ft == "choice":
                value = {"choice": q.data["options"]["choices"][0]}
            else:
                value = {"text": "fallback"}
            client.post(f"/api/v1/submissions/{sub_id}/answers/", {"question_id": q_id, "value": value}, format="json")
        resp = client.get(f"/api/v1/submissions/{sub_id}/next-question/")
        assert resp.status_code == 204
```
</action>
<acceptance_criteria>
- `backend/apps/submissions/tests/test_api.py` contains `def test_create_submission`
- `backend/apps/submissions/tests/test_api.py` contains `def test_next_question`
- `backend/apps/submissions/tests/test_api.py` contains `def test_save_answer`
- `backend/apps/submissions/tests/test_api.py` contains `def test_complete_submission`
- `backend/apps/submissions/tests/test_api.py` contains `def test_get_submission_status`
- `backend/apps/submissions/tests/test_api.py` contains `def test_cannot_access_other_client_submission`
- `backend/apps/submissions/tests/test_api.py` contains `def test_complete_without_all_answers_returns_400`
- `pytest apps/submissions/tests/test_api.py -x` exits 0
</acceptance_criteria>
</task>

## Verification

```bash
pytest apps/ -x -q  # all Phase 1 + Phase 2 tests pass
```
