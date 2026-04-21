"""Seed / upsert the full set of ContentBlocks used by the landing page.

Idempotent: running repeatedly will create missing blocks and update titles of
existing ones, but WILL NOT overwrite content an admin has edited. The admin
can edit any block from /admin/content/contentblock/ afterwards.

Run: python manage.py seed_content
"""
from django.core.management.base import BaseCommand

from apps.content.models import ContentBlock


# ─── Landing page content blocks ────────────────────────────────────────────
# The `key` field matches what the React frontend fetches from /api/v1/content/.
# `title` is shown in the admin list so the editor knows what they're editing.
# `default` seeds the first value; blank-by-default blocks let the frontend
# use its hardcoded fallback until the admin writes a value.

BLOCKS = [
    # --- HERO ---
    ("hero_title",       "Главная: заголовок hero-секции",
     "Аудит бизнеса, который ведёт к росту"),
    ("hero_subtitle",    "Главная: подзаголовок hero-секции",
     "Заполните отраслевую анкету в Telegram-боте, получите именной PDF-отчёт с "
     "анализом ключевых параметров за 3–5 дней."),
    ("hero_cta",         "Главная: текст кнопки hero-секции",
     "Выбрать тариф"),

    # --- МЕТОД ---
    ("method_title",     "Секция «Метод»: заголовок",
     "Наш метод"),
    ("method_text",      "Секция «Метод»: описание",
     "Три простых шага от первого сообщения в Telegram до готового отчёта "
     "с разбором ключевых параметров бизнеса."),

    # --- ТАРИФЫ ---
    ("tariff_section_title", "Секция «Тарифы»: заголовок",
     "Выберите глубину аудита"),

    # --- КЕЙСЫ ---
    ("cases_title",      "Секция «Кейсы»: заголовок",
     "Результаты наших клиентов"),
    ("case_1_title",     "Кейс 1: заголовок",
     "Ритейл-компания"),
    ("case_1_text",      "Кейс 1: описание",
     "Оптимизация бизнес-процессов привела к росту маржинальности на 15%."),
    ("case_2_title",     "Кейс 2: заголовок",
     "IT-стартап"),
    ("case_2_text",      "Кейс 2: описание",
     "Аудит помог выявить узкие места и ускорить найм вдвое."),

    # --- FAQ ---
    ("faq_1_q",          "FAQ 1: вопрос",
     "Сколько времени занимает аудит?"),
    ("faq_1_a",          "FAQ 1: ответ",
     "От получения анкеты до готового отчёта — 3–5 рабочих дней."),
    ("faq_2_q",          "FAQ 2: вопрос",
     "Какие данные нужны для аудита?"),
    ("faq_2_a",          "FAQ 2: ответ",
     "Вы заполняете анкету из 27 вопросов в Telegram-боте. "
     "Дополнительных документов не требуется."),
    ("faq_3_q",          "FAQ 3: вопрос",
     "Можно ли обновить тариф?"),
    ("faq_3_a",          "FAQ 3: ответ",
     "Да, с Ashıde 1 можно перейти на Ashıde 2 из личного кабинета с доплатой."),
    ("faq_4_q",          "FAQ 4: вопрос",
     "Безопасно ли передавать данные?"),
    ("faq_4_a",          "FAQ 4: ответ",
     "Ответы анкеты шифруются и доступны только эксперту, готовящему отчёт. "
     "Мы не передаём их третьим лицам и не используем в рассылках."),
    ("faq_5_q",          "FAQ 5: вопрос",
     "В какой валюте принимается оплата?"),
    ("faq_5_a",          "FAQ 5: ответ",
     "В тенге, через CloudPayments KZ. 3-D Secure обязателен, реквизиты карты "
     "на стороне сервиса не хранятся."),
]


class Command(BaseCommand):
    help = "Create (or update title on) all landing ContentBlock entries."

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Also overwrite existing block content with defaults "
                 "(DESTRUCTIVE — will clobber admin edits).",
        )

    def handle(self, *args, overwrite: bool = False, **options):
        created = 0
        updated = 0
        skipped = 0
        for key, title, default in BLOCKS:
            block, was_created = ContentBlock.objects.get_or_create(
                key=key,
                defaults={
                    "title": title,
                    "content": default,
                    "content_type": ContentBlock.ContentType.TEXT,
                    "is_active": True,
                },
            )
            if was_created:
                created += 1
                continue
            # Always refresh title so admin list stays in sync with this file.
            changed_fields = []
            if block.title != title:
                block.title = title
                changed_fields.append("title")
            if overwrite and block.content != default:
                block.content = default
                changed_fields.append("content")
            if changed_fields:
                block.save(update_fields=changed_fields)
                updated += 1
            else:
                skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f"ContentBlocks: created={created}, updated={updated}, skipped={skipped}"
        ))
