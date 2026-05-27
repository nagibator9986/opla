"""Adaptive-questionnaire engine that drives the chat bot.

Responsibilities:
    • pick the next question for a Submission, respecting conditional rules
    • validate + persist the user's answer
    • render question text + quick-reply choice buttons for the frontend
    • detect completion and advance the Submission FSM

Kept in ``apps.ai`` because it only ever runs inside the chat flow — the
legacy JWT-based next-question API remains unchanged.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.industries.models import Question, QuestionnaireTemplate
from apps.submissions.models import Answer, Submission

log = logging.getLogger(__name__)


@dataclass
class RenderedQuestion:
    question_id: int
    order: int
    stage: str
    text: str
    field_type: str
    placeholder: str
    choices: list[str]
    progress_done: int
    progress_total: int

    def to_payload(self) -> dict:
        return {
            "question_id": self.question_id,
            "order": self.order,
            "stage": self.stage,
            "text": self.text,
            "field_type": self.field_type,
            "placeholder": self.placeholder,
            "choices": self.choices,
            "progress": {"done": self.progress_done, "total": self.progress_total},
        }


def visible_questions_for(submission: Submission) -> list[Question]:
    """Return the subset of questions the user will actually see, ordered.

    Runs conditionals against the answers already saved for this submission.
    """
    all_questions = list(submission.template.questions.order_by("order"))
    answers = {
        a.question_id: _normalised_value(a.value)
        for a in submission.answers.select_related("question")
    }

    # Iterate in order, adding each question to the result if its precondition
    # is satisfied by already-saved answers.
    visible: list[Question] = []
    answered_so_far: dict[int, Any] = {}
    for q in all_questions:
        if q.is_visible_for(answered_so_far):
            visible.append(q)
        # Simulate the answer being recorded so downstream conditionals work
        if q.id in answers:
            answered_so_far[q.id] = answers[q.id]
    return visible


def next_question(submission: Submission) -> RenderedQuestion | None:
    """Return the next unanswered question, or None when complete."""
    visible = visible_questions_for(submission)
    answered_ids = set(submission.answers.values_list("question_id", flat=True))

    for q in visible:
        if q.id not in answered_ids:
            return _render(q, done=len([x for x in visible if x.id in answered_ids]), total=len(visible))

    return None


def render_intro(template: QuestionnaireTemplate, submission: Submission, total: int) -> str:
    """Intro message shown before the first question. Applies placeholders."""
    client = submission.client
    return _render_placeholders(
        template.intro_text,
        name=client.name if client else "",
        company=client.company if client else "",
        total=total,
    )


def render_completion(template: QuestionnaireTemplate, submission: Submission, total: int) -> str:
    client = submission.client
    return _render_placeholders(
        template.completion_text,
        name=client.name if client else "",
        company=client.company if client else "",
        total=total,
    )


@transaction.atomic
def save_answer(submission: Submission, question: Question, raw: str | list[str]) -> None:
    """Persist the client's answer.

    Validates based on question.field_type. Raises ValueError with a
    user-safe message on invalid input.
    """
    value = _coerce_answer(question, raw)

    Answer.objects.update_or_create(
        submission=submission,
        question=question,
        defaults={"value": value, "answered_at": timezone.now()},
    )


def try_complete(submission: Submission) -> bool:
    """If all visible required questions are answered, advance FSM and return True."""
    visible = visible_questions_for(submission)
    required_ids = {q.id for q in visible if q.required}
    answered_ids = set(submission.answers.values_list("question_id", flat=True))
    if not required_ids.issubset(answered_ids):
        return False
    try:
        submission.complete_questionnaire()
        submission.save()
        log.info("questionnaire: submission=%s → completed", submission.id)
        return True
    except Exception as exc:
        log.warning(
            "questionnaire: complete_questionnaire failed for sub=%s: %s",
            submission.id,
            exc,
        )
        return False


# ── internal helpers ────────────────────────────────────────────────────


def _render(q: Question, *, done: int, total: int) -> RenderedQuestion:
    choices = []
    if q.field_type in (Question.FieldType.CHOICE, Question.FieldType.MULTICHOICE):
        choices = list((q.options or {}).get("choices") or [])
    return RenderedQuestion(
        question_id=q.id,
        order=q.order,
        stage=q.stage,
        text=q.text,
        field_type=q.field_type,
        placeholder=q.placeholder,
        choices=choices,
        progress_done=done,
        progress_total=total,
    )


def _normalised_value(raw: dict) -> Any:
    """Turn Answer.value JSON into a primitive for conditional checks."""
    if not isinstance(raw, dict):
        return raw
    if "choice" in raw:
        return raw["choice"]
    if "choices" in raw:
        return raw["choices"]
    if "text" in raw:
        return raw["text"]
    if "number" in raw:
        return raw["number"]
    if "url" in raw:
        return raw["url"]
    return next(iter(raw.values()), None)


def _coerce_answer(question: Question, raw: str | list[str]) -> dict:
    ft = question.field_type

    if ft == Question.FieldType.NUMBER:
        if isinstance(raw, list):
            raise ValueError("Пожалуйста, введите одно число.")
        text = (raw or "").strip().replace(",", ".").replace(" ", "")
        if not text and not question.required:
            return {"number": None}
        try:
            num = float(text)
            if num.is_integer():
                num = int(num)
        except (TypeError, ValueError):
            raise ValueError("Нужен число. Введите, пожалуйста, цифрами.")
        return {"number": num}

    if ft == Question.FieldType.URL:
        url = (raw if isinstance(raw, str) else "").strip()
        if not url and not question.required:
            return {"url": ""}
        if not re.match(r"^https?://", url):
            raise ValueError(
                "Нужна корректная ссылка — начните с https:// или http://"
            )
        return {"url": url}

    if ft == Question.FieldType.CHOICE:
        choice = (raw if isinstance(raw, str) else "").strip()
        allowed = (question.options or {}).get("choices") or []
        if choice not in allowed:
            raise ValueError(
                "Выберите один из предложенных вариантов (кнопкой или напишите точно)."
            )
        return {"choice": choice}

    if ft == Question.FieldType.MULTICHOICE:
        if isinstance(raw, str):
            raw = [s.strip() for s in raw.split(",") if s.strip()]
        allowed = set((question.options or {}).get("choices") or [])
        picked = [c for c in raw if c in allowed]
        if question.required and not picked:
            raise ValueError(
                "Выберите один или несколько вариантов из списка."
            )
        return {"choices": picked}

    # text / longtext — stored as plain text
    text = (raw if isinstance(raw, str) else "").strip()
    if question.required and not text:
        raise ValueError("Поле не может быть пустым.")
    if text:
        _validate_text_meaningful(question, text)
    return {"text": text}


# Гласные RU/KZ/EN для проверки "осмысленности" текста
_VOWELS = set("аеёиоуыэюяəіөүaeiouy")


def _validate_text_meaningful(question: Question, text: str) -> None:
    """Фильтр от «белиберды» — отлавливает случайный набор символов.

    Эвристики настроены так, чтобы не блокировать короткие легитимные
    ответы ("ИП", "Алматы", "5 лет"), но отбрасывать набор клавиш
    типа «куруерукреу» или «ааааааа».

    Бросает ``ValueError`` с понятным сообщением — вызывающий код (чат-бот)
    покажет его клиенту и повторит вопрос.
    """
    n = len(text)
    is_longtext = question.field_type == Question.FieldType.LONGTEXT

    # 1) Содержательная длина для longtext (вопросы аудита)
    if is_longtext and n < 15:
        raise ValueError(
            "Слишком короткий ответ. Опишите подробнее (хотя бы 15 символов) — "
            "это нужно эксперту для качественного анализа."
        )

    # 2) Длинные повторы одного символа: «ааааа», «11111», «.....»
    if re.search(r"(.)\1{4,}", text, re.UNICODE):
        raise ValueError(
            "Похоже на случайный набор символов (слишком много повторов). "
            "Попробуйте ответить осмысленно."
        )

    # 3) Для longtext — минимум 2 слова через пробел
    if is_longtext and len(text.split()) < 2:
        raise ValueError(
            "Развёрнутый ответ из одного слова обычно недостаточен — "
            "опишите хотя бы парой предложений."
        )

    # Дальше анализируем только буквенную часть (без цифр, знаков, пробелов).
    # Короткие ответы (< 5 букв) — пропускаем целиком, чтобы не мешать
    # абревиатурам и коротким локациям ("ИП", "ТОО", "Yes", "Алма").
    letters = [ch for ch in text if ch.isalpha()]
    if len(letters) < 5:
        return

    # 4) Доля уникальных букв — отлавливает «куруерукреу куруерукреу»
    unique_ratio = len({ch.lower() for ch in letters}) / len(letters)
    threshold = 0.22 if is_longtext else 0.18
    if unique_ratio < threshold:
        raise ValueError(
            "В ответе мало уникальных букв — похоже на случайный набор. "
            "Опишите, пожалуйста, по сути вопроса."
        )

    # 5) Соотношение гласных/согласных (для 6+ букв) — отлавливает
    # «фывапролд», «гггггггг» и похожие наборы.
    if len(letters) >= 6:
        vowel_count = sum(1 for ch in letters if ch.lower() in _VOWELS)
        vowel_ratio = vowel_count / len(letters)
        if vowel_ratio < 0.15 or vowel_ratio > 0.85:
            raise ValueError(
                "В ответе странное соотношение гласных и согласных — "
                "похоже на набор случайных букв. Попробуйте ещё раз."
            )


def _render_placeholders(template: str, **vars) -> str:
    def repl(match: "re.Match[str]") -> str:
        key = match.group(1).strip()
        return str(vars.get(key, ""))

    return re.sub(r"\{\{\s*(\w+)\s*\}\}", repl, template or "")
