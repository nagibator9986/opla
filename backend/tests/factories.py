"""factory-boy factories for all models used in API tests."""
from __future__ import annotations

import factory
from factory.django import DjangoModelFactory

from apps.accounts.models import BaseUser, ClientProfile
from apps.industries.models import Industry, Question, QuestionnaireTemplate
from apps.payments.models import Tariff
from apps.submissions.models import Submission


class UserFactory(DjangoModelFactory):
    class Meta:
        model = BaseUser

    email = factory.Sequence(lambda n: f"user{n}@baqsy.kz")
    is_active = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop("password", "testpass123")
        obj = super()._create(model_class, *args, **kwargs)
        obj.set_password(password)
        obj.save()
        return obj


class IndustryFactory(DjangoModelFactory):
    class Meta:
        model = Industry

    name = factory.Sequence(lambda n: f"Industry {n}")
    code = factory.Sequence(lambda n: f"industry-{n}")
    is_active = True


class QuestionnaireTemplateFactory(DjangoModelFactory):
    class Meta:
        model = QuestionnaireTemplate

    industry = factory.SubFactory(IndustryFactory)
    version = 1
    is_active = True
    name = factory.LazyAttribute(lambda o: f"Template {o.industry.name} v{o.version}")


class QuestionFactory(DjangoModelFactory):
    class Meta:
        model = Question

    template = factory.SubFactory(QuestionnaireTemplateFactory)
    order = factory.Sequence(lambda n: n + 1)
    text = factory.Sequence(lambda n: f"Question {n}?")
    field_type = "text"
    options = {}
    required = True
    block = "A"


class TariffFactory(DjangoModelFactory):
    class Meta:
        model = Tariff

    code = factory.Sequence(lambda n: f"tariff-{n}")
    title = factory.Sequence(lambda n: f"Tariff {n}")
    price_kzt = 45000
    is_active = True


class ClientProfileFactory(DjangoModelFactory):
    class Meta:
        model = ClientProfile

    user = factory.SubFactory(UserFactory)
    telegram_id = factory.Sequence(lambda n: 100000 + n)
    name = factory.Faker("name")
    company = factory.Faker("company")
    phone_wa = factory.Sequence(lambda n: f"+7700{n:07d}")
    city = "Алматы"
    industry = factory.SubFactory(IndustryFactory)


class SubmissionFactory(DjangoModelFactory):
    class Meta:
        model = Submission

    client = factory.SubFactory(ClientProfileFactory)
    template = factory.SubFactory(QuestionnaireTemplateFactory)
    tariff = factory.SubFactory(TariffFactory)
