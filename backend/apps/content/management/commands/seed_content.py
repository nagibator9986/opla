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
    ("hero_badge",       "Главная · Hero: бейдж сверху",
     "Digital Baqsylyq · Код Вечного Иля"),
    ("hero_title",       "Главная · Hero: заголовок",
     "Аудит бизнеса по Коду Вечного Иля"),
    ("hero_subtitle",    "Главная · Hero: подзаголовок",
     "Заполните анкету, выберите тариф и получите именной PDF-отчёт с "
     "анализом ключевых параметров за 1–2 дней."),
    ("hero_cta",         "Главная · Hero: текст кнопки (не используется)",
     "Выбрать тариф"),
    ("hero_pkg1_label",  "Главная · Hero: подпись Пакет 1",
     "Пакет 1"),
    ("hero_pkg1_title",  "Главная · Hero: название Пакет 1",
     "Ashide 1 (1 сотрудник)"),
    ("hero_pkg1_price",  "Главная · Hero: цена Пакет 1",
     "199$"),
    ("hero_pkg2_label",  "Главная · Hero: подпись Пакет 2",
     "Пакет 2"),
    ("hero_pkg2_title",  "Главная · Hero: название Пакет 2",
     "Ashino + Ashide (3–7 сотрудников)"),
    ("hero_pkg2_price",  "Главная · Hero: цена Пакет 2",
     "799$"),
    ("hero_pkg_cta_authed", "Главная · Hero: подпись на карточке для зарегистрированного (CTA)",
     "Заказать аудит →"),
    ("hero_stat1_value", "Главная · Hero: цифра статистики #1",
     "27"),
    ("hero_stat1_label", "Главная · Hero: подпись статистики #1",
     "параметров"),
    ("hero_stat2_value", "Главная · Hero: цифра статистики #2",
     "3–5"),
    ("hero_stat2_label", "Главная · Hero: подпись статистики #2",
     "рабочих дней"),
    ("hero_stat3_value", "Главная · Hero: цифра статистики #3",
     "до 7"),
    ("hero_stat3_label", "Главная · Hero: подпись статистики #3",
     "участников в группе"),

    # --- CASES (главная) ---
    ("cases_landing_caption", "Главная · Кейсы: подпись над лого-стрипом",
     "Среди разборов"),
    ("cases_landing_button", "Главная · Кейсы: текст кнопки",
     "Смотреть кейсы мировых компаний"),

    # --- ЧАТ (приветствие зарегистрированного клиента) ---
    ("chat_greeting_authed", "Чат: приветствие для зарегистрированного клиента (плейсхолдеры {{name}}, {{company}})",
     "Здравствуйте, {{name}}! Я Baqsy AI — ваш персональный помощник по "
     "Коду Вечного Иля. Профиль уже настроен, я знаю всё про «{{company}}». "
     "Чем могу помочь — подробнее рассказать про метод, ответить на вопрос "
     "или сразу перейти к заказу аудита?"),

    # --- BLOG (главная) ---
    ("blog_badge",       "Главная · Статьи: бейдж",
     "Информационный блок"),
    ("blog_title",       "Главная · Статьи: заголовок",
     "Статьи"),
    ("blog_subtitle",    "Главная · Статьи: подзаголовок",
     "Материалы о методе Baqsy и Коде Вечного Иля — для тех, кто хочет "
     "понять подход глубже перед аудитом."),
    ("blog_link_all",    "Главная · Статьи: ссылка ‹Все материалы›",
     "Все материалы"),

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
