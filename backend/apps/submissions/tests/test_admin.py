import pytest
from django.contrib.auth import get_user_model

from apps.submissions.admin import SubmissionAdmin

User = get_user_model()


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(email="staff@baqsy.test", password="pass123", is_staff=True, is_superuser=True)


@pytest.mark.django_db
class TestSubmissionAdmin:
    def test_submission_list(self, client, staff_user):
        """CRM-03: Submission list accessible to staff."""
        client.force_login(staff_user)
        response = client.get("/admin/submissions/submission/")
        assert response.status_code == 200

    def test_submission_list_has_search(self, client, staff_user):
        """CRM-03: Submission list has search fields."""
        client.force_login(staff_user)
        response = client.get("/admin/submissions/submission/?q=test")
        assert response.status_code == 200

    def test_submission_admin_has_approve_action(self):
        """CRM-04: SubmissionAdmin has approve_and_send in actions_detail."""
        assert "approve_and_send" in SubmissionAdmin.actions_detail
