"""Per-parameter audit analyzer.

Идея заказчика: 12 специализированных AI-ассистентов, каждый отвечает
за свой параметр (финансы, команда, маркетинг, …). После прохождения
анкеты:

* Берём все ответы клиента, отфильтрованные по `Question.parameter`
* Подставляем их в `AuditParameter.system_prompt` как блок {{answers}}
* Шлём в OpenAI с моделью/температурой параметра
* Получаем секцию отчёта по этому параметру

Раздел отчёта возвращается строкой — админ собирает 12 кусков в
финальный документ (или в будущем мы сделаем автосборку).
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from apps.ai.services import _describe_openai_error, _get_client
from apps.industries.models import AuditParameter, Question
from apps.submissions.models import Submission

log = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    parameter_code: str
    parameter_name: str
    text: str
    tokens_used: int | None
    questions_used: int


def collect_answers_for_parameter(
    submission: Submission, parameter: AuditParameter
) -> list[tuple[Question, str]]:
    """Вернуть список (вопрос, ответ-строка) только по этому параметру."""
    answers_qs = (
        submission.answers.select_related("question")
        .filter(question__parameter=parameter)
        .order_by("question__order")
    )
    out: list[tuple[Question, str]] = []
    for ans in answers_qs:
        value = ans.value or {}
        if isinstance(value, dict):
            display = (
                value.get("text")
                or value.get("number")
                or value.get("choice")
                or ", ".join(value.get("choices") or [])
                or value.get("url")
                or ""
            )
        else:
            display = str(value)
        out.append((ans.question, str(display).strip()))
    return out


def _format_answers_block(rows: list[tuple[Question, str]]) -> str:
    if not rows:
        return "(нет ответов по этому параметру)"
    lines: list[str] = []
    for q, val in rows:
        stage = f"[{q.stage}] " if q.stage else ""
        lines.append(f"{stage}Q: {q.text}\nA: {val or '—'}")
    return "\n\n".join(lines)


def _render_prompt(template: str, *, name: str, company: str, industry: str, answers: str) -> str:
    out = template or ""
    for k, v in {"name": name, "company": company, "industry": industry, "answers": answers}.items():
        out = out.replace(f"{{{{{k}}}}}", v)
    # Если плейсхолдер {{answers}} не использован — подставим в конец
    if "{{answers}}" not in template and answers:
        out = out + "\n\n[Ответы клиента]\n" + answers
    return out


def analyze_parameter(submission: Submission, parameter: AuditParameter) -> AnalysisResult:
    """Запустить AI-ассистента для одного параметра. Raises RuntimeError."""
    rows = collect_answers_for_parameter(submission, parameter)
    answers_block = _format_answers_block(rows)

    client = submission.client
    name = client.name if client else ""
    company = client.company if client else ""
    industry = client.industry.name if client and client.industry else ""

    system_prompt = _render_prompt(
        parameter.system_prompt,
        name=name, company=company, industry=industry, answers=answers_block,
    )

    cli = _get_client()
    if cli is None:
        raise RuntimeError(
            "AI-ассистент не настроен (нет ключа OpenAI)."
        )

    try:
        resp = cli.chat.completions.create(
            model=parameter.model or "gpt-4o-mini",
            temperature=parameter.temperature,
            max_tokens=parameter.max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"Сформируй раздел отчёта по параметру «{parameter.name}» "
                        f"для компании {company or '—'}. Опирайся ТОЛЬКО на "
                        "ответы клиента ниже, не придумывай. Структура: "
                        "1) что наблюдается (2–3 предложения), "
                        "2) скрытые риски (Bün), "
                        "3) рекомендации (3–5 пунктов). "
                        "Тон — деловой, но человеческий. Без воды."
                    ),
                },
            ],
        )
    except Exception as exc:  # OpenAI SDK exception
        log.exception("analyze_parameter: OpenAI failed for parameter=%s sub=%s", parameter.code, submission.id)
        raise RuntimeError(_describe_openai_error(exc)) from exc

    choice = resp.choices[0] if resp.choices else None
    text = (choice.message.content or "").strip() if choice else ""
    usage = getattr(resp, "usage", None)
    tokens = getattr(usage, "total_tokens", None) if usage else None
    return AnalysisResult(
        parameter_code=parameter.code,
        parameter_name=parameter.name,
        text=text,
        tokens_used=tokens,
        questions_used=len(rows),
    )


def assemble_full_report(submission: Submission) -> str:
    """Прогнать ВСЕ активные параметры и собрать markdown-отчёт.

    Параметры без привязанных вопросов или без ответов клиента
    помечаются как пропущенные — не тратим токены OpenAI впустую.
    """
    sections: list[str] = []
    parameters = AuditParameter.objects.filter(is_active=True).order_by("order", "name")
    for p in parameters:
        rows = collect_answers_for_parameter(submission, p)
        if not rows:
            sections.append(
                f"## {p.order}. {p.name}\n\n"
                f"_(нет ответов клиента, привязанных к этому параметру — "
                f"свяжите вопросы с параметром в админке)_"
            )
            continue
        try:
            r = analyze_parameter(submission, p)
            sections.append(f"## {p.order}. {p.name}\n\n{r.text}")
        except RuntimeError as exc:
            sections.append(
                f"## {p.order}. {p.name}\n\n_(не удалось сгенерировать раздел: {exc})_"
            )

    if not sections:
        return "_Нет активных параметров аудита. Заведите параметры в админке: Industries → Параметры аудита._"

    intro = (
        f"# Аудит «Digital Baqsylyq» — {submission.client.company if submission.client else 'компания'}\n\n"
        f"Подготовлен по {submission.template.name}. Сформировано "
        f"{len(sections)} разделов.\n"
    )
    return intro + "\n\n" + "\n\n".join(sections)
