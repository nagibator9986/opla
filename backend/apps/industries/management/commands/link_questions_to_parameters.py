"""Авто-привязка вопросов Baqsylyq к 12 параметрам аудита по ключевым словам.

Без этой привязки 12 AI-ассистентов не получают данные клиента — итоговый
отчёт собирается из 12 секций, каждая секция склеивается из ответов,
помеченных соответствующим ``Question.parameter``.

Команда идемпотентна:
    • не перетирает уже привязанные вопросы (ручные правки админа в безопасности);
    • запуск без аргументов — dry-run + отчёт;
    • с флагом ``--apply`` сохраняет привязки.

Применение:
    python manage.py link_questions_to_parameters            # dry-run
    python manage.py link_questions_to_parameters --apply    # реально сохранить
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.industries.models import AuditParameter, Question, QuestionnaireTemplate


# Маппинг: param.code → список ключевых фраз (case-insensitive substring match).
# Порядок имеет значение — первый match выигрывает.
# Фразы взяты из текстов вопросов в seed_baqsylyq.py.
RULES: list[tuple[str, list[str]]] = [
    ("company-passport", [
        "название компании",
        "ссылка на сайт",
        "сфера деятельности",
        "локация компании",
        "количество сотрудников",
        "среднемесячный оборот",
        "оборот компании",
        "срок существования",
        "головной компании",
    ]),
    ("leadership-role", [
        "уровень ответственности",
        "ваше фио",
        "ссылки на ваши личные",
        "ссылки на ваш личный профиль",
        "отойдёте от дел",
        "отключить связь без риска",
        "если вы отойдёте",
        "если вы отойдете",
    ]),
    ("strategy-goals", [
        "исчезнет завтра",  # бизнес/подразделение исчезнет
        "цели компании за прошлый год",
        "3 задачи вашего отдела",
        "технологический или рыночный сдвиг",
        "план «б»",
        "план б",
        "цели по прибыли",
        "продукт ненужным",
        "система прожить ещё 50",
        "30% дороже",
        "преданности вашему бренду",
        "агрессивного захвата",
        "финансовый рост за последний год",
    ]),
    ("operations", [
        "20% ваших",
        "20% ваших текущих",
        "задержек, конфликтов",
        "теряется больше всего энергии",
        "критический процесс",
        "звене вашей компании",
        "модные",  # «модные» управленческие/цифровые решения (Agile, бирюзовые…)
        "чужеродным кодом",
        "смежные подразделения",
        "скрытую смуту",
    ]),
    ("team-quality", [
        "не взяли на работу сегодня",
        "один партнёр «сияет»",
        "один партнёр",
        "сияет за счёт",
    ]),
    ("control-reporting", [
        "сглаживать",  # «сглаживать» в кавычках или без — оба ловим
        "проверяете, что отчёты",
        "проверяете, что отчеты",
        "до его полной реализации",
        "до её полной реализации",
        "уровней согласования",
        "разделены роли",
        "заблокировать ваше решение",
        "исполнитель сам оценивает",
        "исполнитель контролирует сам",
    ]),
    ("money-discipline", [
        "личные деньги владельцев",
        "касса бизнеса",
        "оборотные средства",
    ]),
    ("kinship-network", [
        "родством с руководством",
        "родственников",
        "родственники",
        "по праву крови",
        "наняты ли они за компетенции",
    ]),
    ("shadow-influence", [
        "официально не несут ответственности",
        "не несут официальной ответственности",
        "«друзья детства»",
        "друзья детства",
        "связь со старшим",
        "конфликтов, которые систематически забирают",
        "пойти во власть",
        "политический трамплин",
    ]),
    ("lifestyle-reputation", [
        "соревнования в роскоши",
        "в соцсетях образ жизни",
        "поддержание статуса",
        "демонстрацию статуса",
        "ценности",
        "транслируете коллегам",
        "транслируете публично",
    ]),
    ("personal-stability", [
        "падения продуктивности",
        "«отключки» от задач",
        "отключки от задач",
        "вылета» из управления",
        "вылета из управления",
        "операционного вылета",
        "без «головы»",
        "запои",
        "депрессии",
        "токсичным» узлом",
        "токсичным узлом",
    ]),
    ("external-dependency", [
        "одного уникального сотрудника",
        "одного внешнего поставщика",
        "одного ключевого клиента",
        "одного ключевого клиента, поставщика",
        "госконтракта",
        "облачному провайдеру",
    ]),
]


def _find_param_code(question_text: str) -> str | None:
    text_lower = question_text.lower()
    for code, phrases in RULES:
        for phrase in phrases:
            if phrase.lower() in text_lower:
                return code
    return None


class Command(BaseCommand):
    help = (
        "Авто-привязать вопросы анкеты Baqsylyq к 12 параметрам аудита "
        "по ключевым словам. По умолчанию dry-run; --apply сохраняет."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Реально сохранить привязки (по умолчанию — только показать diff).",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Перепривязать даже те вопросы, которые уже имеют параметр.",
        )

    @transaction.atomic
    def handle(self, *args, apply: bool = False, overwrite: bool = False, **opts):
        # 1. Кэшируем все параметры
        params = {p.code: p for p in AuditParameter.objects.all()}
        missing = [code for code, _ in RULES if code not in params]
        if missing:
            self.stdout.write(self.style.ERROR(
                f"Не хватает параметров в БД: {missing}. Запустите seed_audit_parameters."
            ))
            return

        # 2. Берём вопросы из активного Baqsylyq шаблона
        template = QuestionnaireTemplate.objects.filter(
            industry__code="baqsylyq", is_active=True
        ).first()
        if not template:
            self.stdout.write(self.style.ERROR(
                "Активный шаблон Baqsylyq не найден. Запустите activate_baqsylyq."
            ))
            return

        questions = list(template.questions.order_by("order"))
        self.stdout.write(f"Вопросов в активной анкете: {len(questions)}")

        # 3. Собираем план привязок
        plan: dict[int, str] = {}  # question_id -> new param.code
        skipped_has_param: list[Question] = []
        unmatched: list[Question] = []

        for q in questions:
            if q.parameter_id and not overwrite:
                skipped_has_param.append(q)
                continue
            code = _find_param_code(q.text)
            if code:
                plan[q.id] = code
            else:
                unmatched.append(q)

        # 4. Отчёт
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("План привязок:"))
        by_param: dict[str, int] = {}
        for q_id, code in plan.items():
            by_param[code] = by_param.get(code, 0) + 1
        for p in AuditParameter.objects.order_by("order"):
            n = by_param.get(p.code, 0)
            marker = "✓" if n else " "
            self.stdout.write(f"  {marker} {p.order:2}. {p.name:35} {n:>3} вопросов")

        if skipped_has_param:
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING(
                    f"Пропущено (уже привязано вручную, без --overwrite): "
                    f"{len(skipped_has_param)}"
                )
            )

        if unmatched:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING(
                f"Не подобран параметр для {len(unmatched)} вопросов "
                f"(оставить без привязки или дописать правила):"
            ))
            for q in unmatched:
                self.stdout.write(f"  · Q{q.order}: {q.text[:75]}")

        # 5. Применить
        if not apply:
            self.stdout.write("")
            self.stdout.write(self.style.NOTICE(
                "Это был dry-run. Запустите с --apply чтобы сохранить."
            ))
            return

        applied = 0
        for q_id, code in plan.items():
            param = params[code]
            Question.objects.filter(id=q_id).update(parameter=param)
            applied += 1
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Привязано: {applied} вопросов. "
            f"Уже было привязано (не трогали): {len(skipped_has_param)}. "
            f"Без привязки осталось: {len(unmatched)}."
        ))
