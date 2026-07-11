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


# ── Фильтр квалификации ───────────────────────────────────────────────
# По бизнес-решению владельца платформы (2026-06): аудит делаем только
# компаниям от 10 сотрудников и от 50 млн ₸ среднемесячного оборота. Ниже
# — вежливый отказ, анкета не продолжается. Тексты редактируются через
# ContentBlock'и (см. apps/content + seed_content.py).

QUALIFICATION_MIN_EMPLOYEES = 10
QUALIFICATION_MIN_REVENUE_MLN_KZT = 50.0


def _extract_number_answer(submission, *keywords: str) -> float | None:
    """Найти числовой ответ среди ответов submission по ключевым словам в тексте вопроса."""
    for a in submission.answers.select_related("question"):
        text = (a.question.text or "").lower()
        if any(kw.lower() in text for kw in keywords):
            val = a.value
            if isinstance(val, dict) and "number" in val and val["number"] is not None:
                try:
                    return float(val["number"])
                except (TypeError, ValueError):
                    continue
    return None


def check_qualification(submission) -> str | None:
    """Если клиент не прошёл фильтр квалификации — возвращает текст отказа.

    Иначе — None (клиент проходит, анкета продолжается).
    """
    employees = _extract_number_answer(submission, "количество сотрудников")
    revenue = _extract_number_answer(submission, "оборот компании", "среднемесячный оборот")

    if employees is not None and employees < QUALIFICATION_MIN_EMPLOYEES:
        return _load_rejection_text("rejection_employees", default=(
            "К сожалению, наша система forensic-аудита Digital Baqsylyq "
            "рассчитана на компании с командой от 10 человек. Спасибо за "
            "интерес — мы благодарны за время, которое вы потратили. "
            "Будем рады видеть вас, когда команда вырастет!"
        ))
    if revenue is not None and revenue < QUALIFICATION_MIN_REVENUE_MLN_KZT:
        return _load_rejection_text("rejection_revenue", default=(
            "К сожалению, наша система forensic-аудита Digital Baqsylyq "
            "ориентирована на компании со среднемесячным оборотом от 50 млн ₸. "
            "Спасибо за интерес — мы благодарны за время, которое вы потратили. "
            "Будем рады видеть вас, когда обороты вырастут!"
        ))
    return None


def _load_rejection_text(key: str, default: str) -> str:
    """Подгружает текст отказа из ContentBlock, fallback на default."""
    try:
        from apps.content.models import ContentBlock
        cb = ContentBlock.objects.filter(key=key, is_active=True).first()
        if cb and cb.content.strip():
            return cb.content
    except Exception:
        pass
    return default


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
    """Return the next unanswered question, or None when complete.

    Если клиент не прошёл фильтр квалификации — также возвращает None
    (но без перевода в `completed`). Вызывающий код должен сначала
    проверить `submission.rejection_reason` чтобы понять причину.
    """
    # Если клиент уже дисквалифицирован — анкета не продолжается.
    if (submission.rejection_reason or "").strip():
        return None

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

    После сохранения автоматически проверяет квалификацию — если ответ
    был на ключевой вопрос (сотрудники / оборот) и значение не проходит
    фильтр, выставляет `submission.rejection_reason`. После этого
    `next_question` будет возвращать None, а chat-view покажет текст отказа.
    """
    value = _coerce_answer(question, raw)

    Answer.objects.update_or_create(
        submission=submission,
        question=question,
        defaults={"value": value, "answered_at": timezone.now()},
    )

    # Перепроверяем квалификацию только если ещё не дисквалифицирован
    if not (submission.rejection_reason or "").strip():
        reason = check_qualification(submission)
        if reason:
            submission.rejection_reason = reason
            submission.save(update_fields=["rejection_reason"])
            log.info(
                "save_answer: submission=%s disqualified after Q%s",
                submission.id, question.order,
            )


def try_complete(submission: Submission) -> bool:
    """If all visible required questions are answered, advance FSM and return True.

    Дисквалифицированные клиенты (`rejection_reason` заполнен) НЕ переводятся
    в completed — анкета остаётся в `in_progress_full`, в кабинете показывается
    карточка отказа вместо обработки отчёта.
    """
    if (submission.rejection_reason or "").strip():
        return False

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
        if not url:
            if not question.required:
                return {"url": ""}
            raise ValueError("Введите ссылку или название аккаунта.")

        # Мягкая нормализация — клиент не обязан помнить про https://.
        # Принимаем: jazorda.kz / www.jazorda.kz / https://jazorda.kz /
        # @username (Instagram-like). Всё приводим к https://...
        if url.startswith("@"):
            url = "https://instagram.com/" + url[1:].lstrip("/")
        elif not re.match(r"^https?://", url, re.IGNORECASE):
            url = "https://" + url.lstrip("/")

        # Очень мягкая проверка: есть хотя бы точка или путь после https://.
        # Базовое: должен быть хост типа "имя.домен" ИЛИ "instagram.com/..."
        if not re.match(r"^https?://[^\s/]+(\.[^\s/]+|/.+)", url, re.IGNORECASE):
            raise ValueError(
                "Похоже на неправильную ссылку. Попробуйте: jazorda.kz или "
                "https://instagram.com/jazorda"
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
    # Ответы-ссылки (профили соцсетей, сайты) не прогоняем через эвристики
    # «осмысленности»: одиночный URL/@handle не имеет пробелов и «мало гласных»,
    # но это валидный ответ (напр. «https://linkedin.com/in/john», «@baqsy»).
    if re.search(r"https?://|www\.|@\w|[\w-]+\.(?:com|kz|ru|io|me|net|org|co)\b", text, re.IGNORECASE):
        return

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
