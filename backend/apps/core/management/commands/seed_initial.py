import os
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import BaseUser
from apps.industries.models import Industry, QuestionnaireTemplate, Question
from apps.payments.models import Tariff


INDUSTRIES = [
    {"name": "Ритейл", "code": "retail", "description": "Розничная торговля"},
    {"name": "IT/Digital", "code": "it-digital", "description": "IT и цифровые технологии"},
    {"name": "Производство", "code": "manufacturing", "description": "Производственные предприятия"},
    {"name": "Услуги", "code": "services", "description": "Сфера услуг"},
    {"name": "F&B", "code": "food-beverage", "description": "Еда и напитки, HoReCa"},
]

TARIFFS = [
    {"code": "ashide_1", "title": "Ashıde 1", "price_kzt": 45000, "description": "Базовый аудит — 7-9 параметров"},
    {"code": "ashide_2", "title": "Ashıde 2", "price_kzt": 135000, "description": "Расширенный аудит — 18-24 параметра"},
    {"code": "upsell", "title": "Upsell Ashıde 1→2", "price_kzt": 90000, "description": "Доплата за переход с Ashıde 1 на Ashıde 2"},
]

# Demo questions: 5 block A (common) + 1 block B + 3 block C = 9 total
DEMO_QUESTIONS = [
    {"order": 1, "text": "Официальное название предприятия и бренд", "field_type": "text", "block": "A"},
    {"order": 2, "text": "Ссылки на сайт и соцсети", "field_type": "text", "block": "A"},
    {"order": 3, "text": "Страна и город", "field_type": "text", "block": "A"},
    {"order": 4, "text": "Масштаб (оборот)", "field_type": "choice",
     "options": {"choices": ["До 100к$", "До 1М$", "До 10М$", "Выше 10М$"]}, "block": "A"},
    {"order": 5, "text": "Общее количество сотрудников", "field_type": "number", "block": "A"},
    {"order": 6, "text": "Краткое описание деятельности (3-4 предложения)", "field_type": "text", "block": "B"},
    {"order": 7, "text": "Опишите вашу текущую маркетинговую стратегию", "field_type": "text", "block": "C"},
    {"order": 8, "text": "Какие каналы продаж вы используете?", "field_type": "multichoice",
     "options": {"choices": ["Офлайн точки", "Сайт", "Маркетплейсы", "Социальные сети", "Другое"]}, "block": "C"},
    {"order": 9, "text": "Основные конкуренты и ваши отличия от них", "field_type": "text", "block": "C"},
]


class Command(BaseCommand):
    help = "Seed initial data: superuser, industries, tariffs, demo templates"

    @transaction.atomic
    def handle(self, *args, **options):
        self._create_superuser()
        self._create_industries()
        self._create_tariffs()
        self._create_demo_templates()
        self.stdout.write(self.style.SUCCESS("Seed complete."))

    def _create_superuser(self):
        email = os.getenv("DJANGO_SUPERUSER_EMAIL", "admin@baqsy.kz")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "admin")
        if not BaseUser.objects.filter(email=email).exists():
            BaseUser.objects.create_superuser(email=email, password=password)
            self.stdout.write(f"  Created superuser: {email}")
        else:
            self.stdout.write(f"  Superuser exists: {email}")

    def _create_industries(self):
        for data in INDUSTRIES:
            obj, created = Industry.objects.get_or_create(
                code=data["code"],
                defaults={"name": data["name"], "description": data["description"]},
            )
            status = "created" if created else "exists"
            self.stdout.write(f"  Industry {obj.name}: {status}")

    def _create_tariffs(self):
        for data in TARIFFS:
            obj, created = Tariff.objects.get_or_create(
                code=data["code"],
                defaults={"title": data["title"], "price_kzt": data["price_kzt"], "description": data["description"]},
            )
            status = "created" if created else "exists"
            self.stdout.write(f"  Tariff {obj.title}: {status}")

    def _create_demo_templates(self):
        for industry in Industry.objects.all():
            if QuestionnaireTemplate.objects.filter(industry=industry).exists():
                self.stdout.write(f"  Template for {industry.name}: exists")
                continue
            template = QuestionnaireTemplate.objects.create(
                industry=industry,
                version=1,
                is_active=True,
                name=f"Демо-анкета: {industry.name}",
            )
            for q_data in DEMO_QUESTIONS:
                Question.objects.create(
                    template=template,
                    order=q_data["order"],
                    text=q_data["text"],
                    field_type=q_data["field_type"],
                    options=q_data.get("options", {}),
                    required=True,
                    block=q_data["block"],
                )
            self.stdout.write(
                f"  Template for {industry.name}: created ({template.questions.count()} questions)"
            )
