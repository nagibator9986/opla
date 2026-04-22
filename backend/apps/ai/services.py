"""OpenAI integration. Keeps raw API calls isolated so the rest of the app
can stay ignorant of SDK specifics."""
from __future__ import annotations

import logging
import re
from typing import Iterable

from django.conf import settings

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover — package optional at build time
    OpenAI = None  # type: ignore[assignment]

log = logging.getLogger(__name__)

_client: "OpenAI | None" = None


def _get_client() -> "OpenAI | None":
    """Singleton OpenAI client. Returns None if SDK missing or key unset."""
    global _client
    if _client is not None:
        return _client
    if OpenAI is None:
        log.warning("openai package is not installed — chat will not function")
        return None
    api_key = getattr(settings, "OPENAI_API_KEY", "") or ""
    if not api_key:
        log.warning("OPENAI_API_KEY is empty — chat will not function")
        return None
    _client = OpenAI(api_key=api_key)
    return _client


def render_system_prompt(template: str, collected: dict) -> str:
    """Fill {{name}}/{{company}}/{{industry}} placeholders with collected data."""
    def repl(match: "re.Match[str]") -> str:
        key = match.group(1).strip()
        val = collected.get(key, "")
        return str(val) if val else ""

    rendered = re.sub(r"\{\{\s*(\w+)\s*\}\}", repl, template or "")
    # Append collected context so the model always has the latest data,
    # even if the template doesn't use placeholders.
    if collected:
        ctx_lines = [f"- {k}: {v}" for k, v in collected.items() if v]
        if ctx_lines:
            rendered += (
                "\n\n[Уже известная информация о клиенте]\n" + "\n".join(ctx_lines)
            )
    return rendered


def chat_completion(
    *,
    model: str,
    temperature: float,
    max_tokens: int,
    messages: Iterable[dict],
) -> tuple[str, int | None]:
    """Call OpenAI chat.completions. Returns (text, tokens_used).

    Raises RuntimeError on any failure — caller translates into a user-facing
    message. Never exposes raw SDK exceptions to the API surface.
    """
    client = _get_client()
    if client is None:
        raise RuntimeError(
            "AI-ассистент временно недоступен: платформа не настроена. "
            "Напишите нам на info@baqsy.kz — мы ответим лично."
        )
    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=list(messages),
        )
    except Exception as exc:  # SDK exceptions subclass OpenAIError
        log.exception("OpenAI chat.completions failed")
        raise RuntimeError(
            "AI-ассистент сейчас не отвечает. Попробуйте через минуту или "
            "напишите нам на info@baqsy.kz."
        ) from exc

    choice = resp.choices[0] if resp.choices else None
    text = (choice.message.content or "").strip() if choice else ""
    usage = getattr(resp, "usage", None)
    tokens = getattr(usage, "total_tokens", None) if usage else None
    return text, tokens


def extract_client_data(raw_text: str) -> dict:
    """Heuristic extractor — the assistant often mentions name/company/phone
    in conversation. We don't rely on function-calling here to keep it simple;
    frontend can also push structured updates via a dedicated endpoint.
    """
    data: dict[str, str] = {}
    # Phone number: +7..., 7..., 8..., 10–12 digits total
    m = re.search(r"(\+?7|8)[\s\-\(]*\d{3}[\s\-\)]*\d{3}[\s\-]*\d{2}[\s\-]*\d{2}", raw_text or "")
    if m:
        data["phone_wa"] = re.sub(r"\D", "", m.group(0))
    return data
