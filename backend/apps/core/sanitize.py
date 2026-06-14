"""HTML-санитайзер для пользовательского rich-текста (CKEditor 5).

Контент-блоки, тело кейсов и статей редактируются администраторами через
CKEditor. Несмотря на доверенный источник, храним в БД только очищенный HTML —
защита от XSS и от случайной «грязной» разметки (скрипты, inline-обработчики,
iframe). Второй слой защиты — DOMPurify на фронте (SafeHtml.tsx).

Используется ``nh3`` (обёртка над Rust-библиотекой ammonia): быстрый и
безопасный по умолчанию.
"""

from __future__ import annotations

import nh3

# Теги, которые умеет выдавать настроенная панель CKEditor (см.
# CKEDITOR_5_CONFIGS["content_block"] в settings): заголовки, базовое
# форматирование, списки, цитата, таблица, ссылка, код.
ALLOWED_TAGS: set[str] = {
    "p", "br", "hr",
    "strong", "b", "em", "i", "u", "s",
    "h2", "h3", "h4",
    "ul", "ol", "li",
    "a",
    "blockquote",
    "table", "thead", "tbody", "tr", "th", "td",
    "code", "pre",
    "span",
}

# NB: "rel" намеренно НЕ в списке — им управляет параметр link_rel ниже
# (nh3 запрещает указывать оба одновременно).
ALLOWED_ATTRIBUTES: dict[str, set[str]] = {
    "a": {"href", "title", "target"},
}


def sanitize_html(value: str | None) -> str:
    """Вернуть безопасный HTML. Пустое/None → пустая строка.

    Идемпотентна: повторный прогон не меняет уже очищенный результат.
    Ссылки получают ``rel="noopener noreferrer"`` и сохраняют только http(s).
    """
    if not value:
        return ""
    return nh3.clean(
        value,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        link_rel="noopener noreferrer",
        url_schemes={"http", "https", "mailto", "tel"},
    )
