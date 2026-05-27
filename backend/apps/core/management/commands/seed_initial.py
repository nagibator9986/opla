import os
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import BaseUser
from apps.industries.models import Industry, QuestionnaireTemplate
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

class Command(BaseCommand):
    help = "Seed initial data: superuser, industries, tariffs (без устаревших демо-анкет)"

    @transaction.atomic
    def handle(self, *args, **options):
        self._create_superuser()
        self._create_industries()
        self._create_tariffs()
        # Демо-шаблоны (9 вопросов) больше не создаются — единственный
        # источник истины — универсальная анкета Baqsylyq (38 вопросов).
        # Чтобы её засеять, выполните: python manage.py seed_baqsylyq
        self._cleanup_legacy_demo_templates()
        self.stdout.write(self.style.SUCCESS("Seed complete."))

    def _cleanup_legacy_demo_templates(self):
        """Деактивирует устаревшие per-industry демо-шаблоны.

        Сохраняет их в БД (на случай исторических Submission), но снимает
        is_active, чтобы новые заявки шли только в Baqsylyq.
        """
        legacy = QuestionnaireTemplate.objects.filter(
            name__startswith="Демо-анкета:", is_active=True
        )
        count = legacy.update(is_active=False)
        if count:
            self.stdout.write(f"  Деактивировано устаревших демо-шаблонов: {count}")

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

