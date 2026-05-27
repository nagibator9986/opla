"""Привести БД к единому состоянию: универсальная анкета Baqsylyq — единственная активная.

Применение на сервере после деплоя:
    python manage.py activate_baqsylyq

Что делает (идемпотентно, безопасно повторять):
    1. Деактивирует все per-industry демо-шаблоны (name начинается с "Демо-анкета:").
    2. Если шаблона Baqsylyq нет в БД — подсказывает выполнить ``seed_baqsylyq``.
    3. Гарантирует, что активная версия Baqsylyq — последняя (max version).
    4. Печатает сводку: какие шаблоны активны сейчас, сколько вопросов в каждом.
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.industries.models import QuestionnaireTemplate


class Command(BaseCommand):
    help = "Сделать универсальную анкету Baqsylyq единственной активной (деактивирует демо-шаблоны)."

    @transaction.atomic
    def handle(self, *args, **options):
        # 1. Деактивируем устаревшие демо-шаблоны
        demo_q = QuestionnaireTemplate.objects.filter(
            name__startswith="Демо-анкета:", is_active=True
        )
        demo_count = demo_q.update(is_active=False)
        if demo_count:
            self.stdout.write(
                self.style.WARNING(
                    f"  Деактивировано демо-шаблонов: {demo_count}"
                )
            )
        else:
            self.stdout.write("  Активных демо-шаблонов не было — ок.")

        # 2. Проверяем наличие Baqsylyq
        baqsylyq_qs = QuestionnaireTemplate.objects.filter(
            industry__code="baqsylyq"
        ).order_by("-version")
        if not baqsylyq_qs.exists():
            self.stdout.write(
                self.style.ERROR(
                    "  Шаблон Baqsylyq не найден. Выполните: python manage.py seed_baqsylyq"
                )
            )
            return

        # 3. Активируем только последнюю версию Baqsylyq
        latest = baqsylyq_qs.first()
        baqsylyq_qs.exclude(pk=latest.pk).update(is_active=False)
        if not latest.is_active:
            latest.is_active = True
            latest.save(update_fields=["is_active"])
            self.stdout.write(
                self.style.SUCCESS(
                    f"  Активирована последняя версия Baqsylyq v{latest.version}"
                )
            )
        else:
            self.stdout.write(
                f"  Baqsylyq v{latest.version} уже активна (вопросов: {latest.questions.count()})."
            )

        # 4. Сводка по всем активным шаблонам
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("Активные шаблоны после миграции:"))
        active = QuestionnaireTemplate.objects.filter(is_active=True).select_related("industry")
        if not active:
            self.stdout.write(self.style.ERROR("  Нет активных шаблонов!"))
            return
        for tpl in active:
            self.stdout.write(
                f"  • {tpl.industry.name} → {tpl.name} v{tpl.version} "
                f"({tpl.questions.count()} вопросов)"
            )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Готово. Новые заявки пойдут в Baqsylyq."))
