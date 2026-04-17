import pytest
from django.contrib.auth import get_user_model

from apps.reports.admin import AuditReportAdmin
from apps.reports.models import AuditReport

User = get_user_model()


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(email="staff@baqsy.test", password="pass123", is_staff=True, is_superuser=True)


@pytest.mark.django_db
class TestAuditReportAdmin:
    def test_actions_detail_has_approve(self):
        """CRM-04: AuditReportAdmin has approve_and_send in actions_detail."""
        assert "approve_and_send" in AuditReportAdmin.actions_detail

    def test_report_list(self, client, staff_user):
        """CRM-04: AuditReport list accessible to staff."""
        client.force_login(staff_user)
        response = client.get("/admin/reports/auditreport/")
        assert response.status_code == 200

    def test_approve_calls_view_as_view(self):
        """CRM-04: approve_and_send uses ApproveReportView.as_view() (not direct .post())."""
        import inspect
        import apps.reports.admin as admin_module

        # Inspect the module source to confirm as_view() pattern is used
        # (the @action decorator wraps the function, but source of the module is reliable)
        source = inspect.getsource(admin_module)
        assert "as_view()" in source, (
            "approve_and_send must use ApproveReportView.as_view() for proper DRF request wrapping"
        )
