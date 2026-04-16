"""Integration tests for Submission lifecycle API (Plan 03)."""
import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import BaseUser, ClientProfile
from apps.industries.models import Industry, QuestionnaireTemplate, Question
from apps.payments.models import Tariff
from apps.submissions.models import Submission


def _advance_to_in_progress_full(submission):
    """Advance submission FSM from CREATED → IN_PROGRESS_FULL for testing complete flow."""
    submission.start_onboarding()
    submission.save()
    submission.mark_paid()
    submission.save()
    submission.start_questionnaire()
    submission.save()
    return submission


@pytest.fixture
def authenticated_client(db):
    """Create a ClientProfile with JWT-authenticated APIClient and test data."""
    industry = Industry.objects.create(name="IT", code="it", is_active=True)
    template = QuestionnaireTemplate.objects.create(
        industry=industry, version=1, is_active=True, name="IT v1"
    )
    Question.objects.create(
        template=template, order=1, text="Name?", field_type="text",
        block="A", required=True,
    )
    Question.objects.create(
        template=template, order=2, text="Revenue?", field_type="choice",
        block="A", required=True,
        options={"choices": ["<100k", "100k-1M", ">1M"]},
    )
    Question.objects.create(
        template=template, order=3, text="Describe", field_type="text",
        block="B", required=False,
    )

    Tariff.objects.create(code="ashide_1", title="Ashide 1", price_kzt=45000, is_active=True)

    profile = ClientProfile.objects.create(
        telegram_id=12345, name="Test", company="TestCo", industry=industry,
    )
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
        resp = client.post(
            "/api/v1/submissions/",
            {"industry_code": "it", "tariff_code": "ashide_1"},
            format="json",
        )
        sub_id = resp.data["id"]
        resp = client.get(f"/api/v1/submissions/{sub_id}/next-question/")
        assert resp.status_code == 200
        assert resp.data["order"] == 1
        assert resp.data["progress"] == "0/2"

    def test_save_answer(self, authenticated_client):
        client, profile = authenticated_client
        resp = client.post(
            "/api/v1/submissions/",
            {"industry_code": "it", "tariff_code": "ashide_1"},
            format="json",
        )
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
        resp = client.post(
            "/api/v1/submissions/",
            {"industry_code": "it", "tariff_code": "ashide_1"},
            format="json",
        )
        sub_id = resp.data["id"]

        # Advance FSM to IN_PROGRESS_FULL (simulates payment flow)
        submission = Submission.objects.get(id=sub_id)
        _advance_to_in_progress_full(submission)

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
            client.post(
                f"/api/v1/submissions/{sub_id}/answers/",
                {"question_id": q_id, "value": value},
                format="json",
            )

        resp = client.post(f"/api/v1/submissions/{sub_id}/complete/", format="json")
        assert resp.status_code == 200
        assert resp.data["status"] == "completed"

    def test_get_submission_status(self, authenticated_client):
        client, profile = authenticated_client
        resp = client.post(
            "/api/v1/submissions/",
            {"industry_code": "it", "tariff_code": "ashide_1"},
            format="json",
        )
        sub_id = resp.data["id"]
        resp = client.get(f"/api/v1/submissions/{sub_id}/")
        assert resp.status_code == 200
        assert "status" in resp.data
        assert "total_questions" in resp.data

    def test_cannot_access_other_client_submission(self, authenticated_client):
        client, profile = authenticated_client
        # Create another profile's submission
        other_profile = ClientProfile.objects.create(
            telegram_id=99999, name="Other", company="OtherCo",
        )
        template = QuestionnaireTemplate.objects.first()
        other_sub = Submission.objects.create(client=other_profile, template=template)
        resp = client.get(f"/api/v1/submissions/{other_sub.id}/")
        assert resp.status_code == 404

    def test_complete_without_all_answers_returns_400(self, authenticated_client):
        client, profile = authenticated_client
        resp = client.post(
            "/api/v1/submissions/",
            {"industry_code": "it", "tariff_code": "ashide_1"},
            format="json",
        )
        sub_id = resp.data["id"]

        # Advance FSM to IN_PROGRESS_FULL so FSM doesn't block; missing answers should block
        submission = Submission.objects.get(id=sub_id)
        _advance_to_in_progress_full(submission)

        resp = client.post(f"/api/v1/submissions/{sub_id}/complete/", format="json")
        assert resp.status_code == 400

    def test_duplicate_answer_returns_400(self, authenticated_client):
        client, profile = authenticated_client
        resp = client.post(
            "/api/v1/submissions/",
            {"industry_code": "it", "tariff_code": "ashide_1"},
            format="json",
        )
        sub_id = resp.data["id"]
        q = client.get(f"/api/v1/submissions/{sub_id}/next-question/")
        q_id = q.data["id"]
        client.post(
            f"/api/v1/submissions/{sub_id}/answers/",
            {"question_id": q_id, "value": {"text": "answer"}},
            format="json",
        )
        resp = client.post(
            f"/api/v1/submissions/{sub_id}/answers/",
            {"question_id": q_id, "value": {"text": "again"}},
            format="json",
        )
        assert resp.status_code == 400

    def test_next_question_returns_204_when_all_answered(self, authenticated_client):
        client, profile = authenticated_client
        resp = client.post(
            "/api/v1/submissions/",
            {"industry_code": "it", "tariff_code": "ashide_1"},
            format="json",
        )
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
            client.post(
                f"/api/v1/submissions/{sub_id}/answers/",
                {"question_id": q_id, "value": value},
                format="json",
            )
        resp = client.get(f"/api/v1/submissions/{sub_id}/next-question/")
        assert resp.status_code == 204
