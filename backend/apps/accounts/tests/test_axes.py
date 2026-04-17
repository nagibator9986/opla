import pytest
from django.test import override_settings
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestBruteForceProtection:
    @override_settings(AXES_ENABLED=True, AXES_FAILURE_LIMIT=3, AXES_COOLOFF_TIME=None)
    def test_lockout_after_failures(self, client):
        """CRM-10: N failed login attempts block IP with 429."""
        User.objects.create_superuser(email="admin@test.com", password="correct")
        login_url = "/admin/login/"
        for i in range(3):
            client.post(login_url, {"username": "admin@test.com", "password": "wrong"})
        # After AXES_FAILURE_LIMIT attempts, should be locked
        response = client.post(login_url, {"username": "admin@test.com", "password": "wrong"})
        assert response.status_code == 429
