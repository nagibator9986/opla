"""Seed the default AI assistant config. Idempotent — only creates if missing."""
from django.core.management.base import BaseCommand

from apps.ai.models import AIAssistantConfig


DEFAULT_SYSTEM_PROMPT = """Ты — Baqsy AI, персональный консультант-эксперт по бизнес-аудиту \
для компаний Казахстана. Твоя задача:

1) Познакомить клиента с методологией Baqsy — это глубокий, человеческий \
аудит бизнеса по 27 параметрам, который делает живой эксперт, а не автомат.

2) Собрать основные данные: имя, название компании, отрасль, город, \
WhatsApp для доставки результата. Задавай по одному вопросу за раз, живым \
языком, без формальностей.

3) Коротко (2-4 предложения) отвечать на вопросы о продукте, тарифах, \
сроках (3–5 рабочих дней), безопасности данных.

4) Когда у тебя собраны имя, компания, WhatsApp и город — предложи перейти к \
выбору тарифа: «Если вы готовы — давайте подберём тариф. Нажмите кнопку ниже, \
чтобы посмотреть варианты».

Правила:
* Пиши на «вы», тон — тёплый, по-казахстански дружелюбный, без канцелярита.
* Отвечай коротко. Без длинных абзацев и маркированных списков.
* Не обещай того, чего нет (гарантии ROI, сроков вне 3–5 дней и т.п.).
* Не проси номера карт, CVV, паспортные данные — оплата идёт через отдельный \
защищённый виджет CloudPayments.
* Если клиент пишет не про бизнес — мягко вернись к теме аудита.
"""

DEFAULT_GREETING = (
    "Здравствуйте! Я Baqsy AI — помогу подобрать формат бизнес-аудита под "
    "вашу компанию. Расскажите в двух словах, чем занимаетесь — и я подскажу, "
    "какой разбор подойдёт."
)

DEFAULT_QUICK_REPLIES = [
    {"label": "Расскажи про аудит", "payload": "Расскажи подробнее про Baqsy-аудит"},
    {"label": "Сколько это стоит", "payload": "Какие у вас тарифы и что входит?"},
    {"label": "Сроки и формат", "payload": "Сколько по времени и как получу отчёт?"},
    {"label": "Безопасность данных", "payload": "Как вы защищаете мои ответы и данные компании?"},
]


class Command(BaseCommand):
    help = "Create a default AIAssistantConfig if no active one exists."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite the active config with defaults (DESTRUCTIVE).",
        )

    def handle(self, *args, force: bool = False, **options):
        active = AIAssistantConfig.get_active()
        if active and not force:
            self.stdout.write(
                self.style.WARNING(
                    f"Active config already exists ({active.name}). "
                    "Use --force to overwrite."
                )
            )
            return

        if active and force:
            active.system_prompt = DEFAULT_SYSTEM_PROMPT
            active.greeting = DEFAULT_GREETING
            active.quick_replies = DEFAULT_QUICK_REPLIES
            active.save()
            self.stdout.write(self.style.SUCCESS(f"Overwritten {active.name}"))
            return

        cfg = AIAssistantConfig.objects.create(
            name="Baqsy AI",
            model="gpt-4o-mini",
            temperature=0.5,
            max_tokens=800,
            system_prompt=DEFAULT_SYSTEM_PROMPT,
            greeting=DEFAULT_GREETING,
            quick_replies=DEFAULT_QUICK_REPLIES,
            is_active=True,
        )
        self.stdout.write(self.style.SUCCESS(f"Created {cfg.name} (id={cfg.id})"))
