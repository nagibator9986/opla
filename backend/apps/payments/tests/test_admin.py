import pytest
from django.contrib.auth import get_user_model

from apps.payments.admin import TariffAdmin

User = get_user_model()


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(email="staff@baqsy.test", password="pass123", is_staff=True, is_superuser=True)


@pytest.mark.django_db
class TestTariffAdmin:
    def test_tariff_list_editable(self):
        """CRM-08: TariffAdmin has price_kzt and is_active in list_editable."""
        assert "price_kzt" in TariffAdmin.list_editable
        assert "is_active" in TariffAdmin.list_editable

    def test_tariff_list(self, client, staff_user):
        """CRM-08: Tariff list accessible to staff."""
        client.force_login(staff_user)
        response = client.get("/admin/payments/tariff/")
        assert response.status_code == 200
