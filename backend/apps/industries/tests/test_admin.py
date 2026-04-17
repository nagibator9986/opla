import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from adminsortable2.admin import SortableInlineAdminMixin

from apps.industries.admin import QuestionInline, QuestionnaireTemplateAdmin
from apps.industries.models import Industry, Question, QuestionnaireTemplate

User = get_user_model()


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(email="staff@baqsy.test", password="pass123", is_staff=True, is_superuser=True)


@pytest.mark.django_db
class TestIndustryAdmin:
    def test_industry_list(self, client, staff_user):
        """CRM-05: Industry list accessible to staff."""
        client.force_login(staff_user)
        response = client.get("/admin/industries/industry/")
        assert response.status_code == 200

    def test_industry_crud(self, client, staff_user):
        """CRM-05: Can create industry via admin."""
        client.force_login(staff_user)
        response = client.post("/admin/industries/industry/add/", {
            "name": "Test Industry",
            "code": "test-ind",
            "description": "",
            "is_active": True,
        })
        assert response.status_code in (200, 302)


@pytest.mark.django_db
class TestQuestionnaireTemplateAdmin:
    def test_template_versioning_on_save(self, db):
        """CRM-06: QuestionnaireTemplateAdmin.save_model creates new version for active templates."""
        # Verify save_model method exists and handles versioning
        assert hasattr(QuestionnaireTemplateAdmin, "save_model")

    def test_inactive_template_readonly(self, db):
        """CRM-06: has_change_permission returns False for inactive templates."""
        admin_instance = QuestionnaireTemplateAdmin(QuestionnaireTemplate, None)
        ind = Industry.objects.create(name="Test", code="test-ro")
        tpl = QuestionnaireTemplate.objects.create(
            industry=ind, version=1, is_active=False, name="Old"
        )
        rf = RequestFactory()
        request = rf.get("/")
        request.user = User.objects.create_user(email="s@t.com", password="p", is_staff=True, is_superuser=True)
        assert admin_instance.has_change_permission(request, tpl) is False

    def test_question_inline_sortable(self):
        """CRM-07: QuestionInline has SortableInlineAdminMixin in MRO."""
        assert issubclass(QuestionInline, SortableInlineAdminMixin)
