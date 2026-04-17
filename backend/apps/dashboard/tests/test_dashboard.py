import pytest
from django.test import RequestFactory
from django.contrib.auth import get_user_model

from apps.dashboard.views import dashboard_callback, dashboard_stats_partial
from apps.submissions.models import Submission
from apps.payments.models import Payment

User = get_user_model()


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(email="admin@baqsy.test", password="pass123", is_staff=True)


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.mark.django_db
class TestDashboardCallback:
    def test_stats_counters(self, rf, staff_user):
        """CRM-01: dashboard_callback returns 4 stat keys."""
        request = rf.get("/admin/")
        request.user = staff_user
        context = dashboard_callback(request, {})
        assert "stats" in context
        stats = context["stats"]
        assert "total" in stats
        assert "in_progress" in stats
        assert "delivered" in stats
        assert "revenue" in stats

    def test_filter_by_industry(self, rf, staff_user):
        """CRM-02: dashboard_callback filters by industry GET param."""
        request = rf.get("/admin/", {"industry": "999"})
        request.user = staff_user
        context = dashboard_callback(request, {})
        # With non-existent industry, all counters should be 0
        assert context["stats"]["total"] == 0

    def test_filter_by_tariff(self, rf, staff_user):
        """CRM-02: dashboard_callback filters by tariff GET param."""
        request = rf.get("/admin/", {"tariff": "999"})
        request.user = staff_user
        context = dashboard_callback(request, {})
        # With non-existent tariff, all counters should be 0
        assert context["stats"]["total"] == 0

    def test_filter_by_date_range(self, rf, staff_user):
        """CRM-02: dashboard_callback filters by date_from and date_to."""
        request = rf.get("/admin/", {"date_from": "2099-01-01", "date_to": "2099-12-31"})
        request.user = staff_user
        context = dashboard_callback(request, {})
        assert context["stats"]["total"] == 0

    def test_context_has_filter_options(self, rf, staff_user):
        """CRM-02: context includes filter_industries and filter_tariffs."""
        request = rf.get("/admin/")
        request.user = staff_user
        context = dashboard_callback(request, {})
        assert "filter_industries" in context
        assert "filter_tariffs" in context


@pytest.mark.django_db
class TestDashboardStatsPartial:
    def test_htmx_endpoint_requires_staff(self, client):
        """HTMX endpoint requires staff login."""
        response = client.get("/admin/dashboard/stats/")
        assert response.status_code in (302, 403)

    def test_htmx_endpoint_returns_html(self, client, staff_user):
        """HTMX endpoint returns HTML fragment for staff."""
        client.force_login(staff_user)
        response = client.get("/admin/dashboard/stats/")
        assert response.status_code == 200
        assert b"stats" in response.content or b"\xd0\x92\xd1\x81\xd0\xb5\xd0\xb3\xd0\xbe" in response.content
