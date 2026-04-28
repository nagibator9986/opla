"""Сборка guide.pdf — детальный flow платформы Baqsy для клиента и админа.

Использует reportlab (pure-Python, без системных зависимостей). Запуск:

    python3 scripts/build_guide.py

Результат: docs/guide.pdf
"""
from __future__ import annotations

import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


# ─── Шрифты с поддержкой кириллицы ─────────────────────────────────────
# macOS: /System/Library/Fonts/Supplemental/Arial.ttf
# Linux: DejaVu / Liberation
def register_fonts() -> tuple[str, str]:
    """Зарегистрировать шрифты, вернуть (regular, bold)."""
    candidates = [
        ("/System/Library/Fonts/Supplemental/Arial.ttf",
         "/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
        ("/Library/Fonts/Arial.ttf", "/Library/Fonts/Arial Bold.ttf"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ("/Library/Fonts/Arial Unicode.ttf", "/Library/Fonts/Arial Unicode.ttf"),
    ]
    for reg, bold in candidates:
        if Path(reg).exists() and Path(bold).exists():
            pdfmetrics.registerFont(TTFont("BodyFont", reg))
            pdfmetrics.registerFont(TTFont("BodyFontBold", bold))
            return "BodyFont", "BodyFontBold"
    # Fallback — Arial Unicode (single file used for both)
    fallback = Path("/Library/Fonts/Arial Unicode.ttf")
    if fallback.exists():
        pdfmetrics.registerFont(TTFont("BodyFont", str(fallback)))
        pdfmetrics.registerFont(TTFont("BodyFontBold", str(fallback)))
        return "BodyFont", "BodyFont"
    raise RuntimeError("Не нашёл подходящий шрифт с поддержкой кириллицы")


REGULAR, BOLD = register_fonts()


# ─── Цвета бренда ──────────────────────────────────────────────────────
INK_950 = colors.HexColor("#020617")
INK_900 = colors.HexColor("#0f172a")
INK_700 = colors.HexColor("#334155")
INK_500 = colors.HexColor("#64748b")
INK_300 = colors.HexColor("#cbd5e1")
INK_200 = colors.HexColor("#e2e8f0")
INK_100 = colors.HexColor("#f1f5f9")
INK_50 = colors.HexColor("#f8fafc")

BRAND_500 = colors.HexColor("#f59e0b")
BRAND_600 = colors.HexColor("#d97706")
BRAND_100 = colors.HexColor("#fef3c7")
BRAND_50 = colors.HexColor("#fffbeb")

EMERALD_600 = colors.HexColor("#059669")
SKY_600 = colors.HexColor("#0284c7")
ROSE_600 = colors.HexColor("#e11d48")


# ─── Стили ─────────────────────────────────────────────────────────────
def make_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()["BodyText"]
    return {
        "h1": ParagraphStyle(
            "h1", parent=base, fontName=BOLD, fontSize=26, leading=32,
            textColor=INK_900, spaceBefore=20, spaceAfter=16, alignment=TA_LEFT,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base, fontName=BOLD, fontSize=18, leading=24,
            textColor=BRAND_600, spaceBefore=18, spaceAfter=10,
        ),
        "h3": ParagraphStyle(
            "h3", parent=base, fontName=BOLD, fontSize=14, leading=20,
            textColor=INK_900, spaceBefore=14, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "body", parent=base, fontName=REGULAR, fontSize=10.5, leading=16,
            textColor=INK_700, spaceAfter=8,
        ),
        "body_strong": ParagraphStyle(
            "body_strong", parent=base, fontName=BOLD, fontSize=10.5, leading=16,
            textColor=INK_900, spaceAfter=8,
        ),
        "small": ParagraphStyle(
            "small", parent=base, fontName=REGULAR, fontSize=9, leading=14,
            textColor=INK_500, spaceAfter=4,
        ),
        "callout": ParagraphStyle(
            "callout", parent=base, fontName=REGULAR, fontSize=10, leading=15,
            textColor=INK_900, leftIndent=10, rightIndent=10,
            spaceBefore=6, spaceAfter=10, backColor=BRAND_50,
            borderColor=BRAND_500, borderWidth=0, borderPadding=10,
        ),
        "step_label": ParagraphStyle(
            "step_label", parent=base, fontName=BOLD, fontSize=11, leading=14,
            textColor=BRAND_600, spaceAfter=2,
        ),
        "step_title": ParagraphStyle(
            "step_title", parent=base, fontName=BOLD, fontSize=14, leading=18,
            textColor=INK_900, spaceAfter=6,
        ),
        "code": ParagraphStyle(
            "code", parent=base, fontName="Courier", fontSize=9, leading=13,
            textColor=INK_900, leftIndent=10, rightIndent=10, backColor=INK_50,
            borderPadding=8, spaceBefore=4, spaceAfter=10,
        ),
        "title_main": ParagraphStyle(
            "title_main", parent=base, fontName=BOLD, fontSize=44, leading=52,
            textColor=INK_950, alignment=TA_LEFT, spaceAfter=10,
        ),
        "subtitle_main": ParagraphStyle(
            "subtitle_main", parent=base, fontName=REGULAR, fontSize=16, leading=24,
            textColor=INK_500, alignment=TA_LEFT, spaceAfter=20,
        ),
        "kicker": ParagraphStyle(
            "kicker", parent=base, fontName=BOLD, fontSize=11, leading=14,
            textColor=BRAND_600, spaceAfter=8, alignment=TA_LEFT,
        ),
    }


S = make_styles()


# ─── Хелперы для построения контента ───────────────────────────────────
def p(text: str, style_key: str = "body") -> Paragraph:
    return Paragraph(text, S[style_key])


def bullet(text: str) -> Paragraph:
    return Paragraph(f"<font color='#f59e0b'>●</font>&nbsp;&nbsp;{text}", S["body"])


def num(n: int, text: str) -> Paragraph:
    return Paragraph(
        f"<font color='#d97706'><b>{n}.</b></font>&nbsp;&nbsp;{text}", S["body"]
    )


def key_value_table(rows: list[tuple[str, str]]) -> Table:
    data = [[Paragraph(k, S["body_strong"]), Paragraph(v, S["body"])] for k, v in rows]
    t = Table(data, colWidths=[5.5 * cm, 11 * cm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, INK_100),
        ("BACKGROUND", (0, 0), (0, -1), INK_50),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def step_card(num_label: str, kicker: str, title: str, body_paragraphs: list) -> KeepTogether:
    elements = [
        p(num_label, "step_label"),
        p(title, "step_title"),
        *body_paragraphs,
        Spacer(1, 6),
    ]
    return KeepTogether(elements)


def cover_page() -> list:
    return [
        Spacer(1, 4 * cm),
        p("BAQSY · DIGITAL BAQSYLYQ", "kicker"),
        p("Платформа<br/>системного аудита", "title_main"),
        p(
            "Подробное руководство по работе платформы — пошагово "
            "для клиента и для администратора. Все экраны, кнопки, "
            "состояния, обработка ошибок.",
            "subtitle_main",
        ),
        Spacer(1, 5 * cm),
        key_value_table([
            ("Сайт", "https://baqsy.tnriazun.com/"),
            ("Админка", "https://baqsy.tnriazun.com/admin/"),
            ("AI-чат", "Baqsy AI · gpt-4o-mini · 12 специализированных ассистентов"),
            ("Доставка отчёта", "WhatsApp · 3–5 рабочих дней"),
            ("Версия документа", "v1.0 · апрель 2026"),
        ]),
        PageBreak(),
    ]


def section_overview() -> list:
    return [
        p("01. Что это и для кого", "h1"),
        p(
            "<b>Baqsy</b> — платформа системного аудита бизнеса по методологии "
            "«Код Вечного Иля» (Digital Baqsylyq). Клиент проходит "
            "адаптивную анкету в чат-формате, его ответы анализируют "
            "12 специализированных AI-ассистентов, эксперт собирает "
            "консолидированный отчёт и присылает именной PDF в WhatsApp.",
        ),
        p("Целевая аудитория", "h3"),
        bullet("Собственники компаний от 20 человек — глубокий разбор системы"),
        bullet("Топ-менеджеры — ревизия зон ответственности"),
        bullet("Менеджеры среднего звена — диагностика своего отдела"),
        p("Два формата участия", "h3"),
        Table(
            [
                [
                    p("<b>Ashıde 1</b><br/>Личный аудит", "body"),
                    p("1 сотрудник<br/>45 000 ₸<br/>25 вопросов / 38 для владельца", "body"),
                ],
                [
                    p("<b>Ashıde 2</b><br/>Командный аудит", "body"),
                    p(
                        "3–7 сотрудников · $729 (≈390 000 ₸)<br/>"
                        "Каждый участник проходит свою анкету анонимно<br/>"
                        "AI агрегирует ответы команды в общую картину системы",
                        "body",
                    ),
                ],
            ],
            colWidths=[7 * cm, 9.5 * cm],
        ).setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (-1, -1), INK_50),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, INK_200),
            ("BOX", (0, 0), (-1, -1), 0.5, INK_200),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ])) or "",
        PageBreak(),
    ]


def section_overview_simple() -> list:
    """Упрощённая версия (Table без setStyle хака)."""
    pkg_table = Table(
        [
            [
                p("<b>Ashıde 1</b> — Личный аудит", "body_strong"),
                p("1 сотрудник · 45 000 ₸ · 25 вопросов (38 для владельца)", "body"),
            ],
            [
                p("<b>Ashıde 2</b> — Командный аудит", "body_strong"),
                p(
                    "3–7 сотрудников · <b>$729</b> (≈ 390 000 ₸). Каждый "
                    "проходит свою анкету анонимно. AI агрегирует ответы "
                    "команды в общую картину системы.",
                    "body",
                ),
            ],
        ],
        colWidths=[5.5 * cm, 11 * cm],
    )
    pkg_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (0, -1), BRAND_50),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, INK_200),
        ("BOX", (0, 0), (-1, -1), 0.5, INK_200),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    return [
        p("01. Что это и для кого", "h1"),
        p(
            "<b>Baqsy</b> — платформа системного аудита бизнеса по методологии "
            "«Код Вечного Иля» (Digital Baqsylyq). Клиент проходит "
            "адаптивную анкету в чат-формате, его ответы анализируют "
            "12 специализированных AI-ассистентов, эксперт собирает "
            "консолидированный отчёт и присылает именной PDF в WhatsApp."
        ),
        p("Для кого", "h3"),
        bullet("Собственники компаний от 20 человек — глубокий разбор системы"),
        bullet("Топ-менеджеры — ревизия зон ответственности"),
        bullet("Менеджеры среднего звена — диагностика своего отдела"),
        p("Два формата участия", "h3"),
        pkg_table,
        Spacer(1, 8),
        p(
            "Оплата проходит исключительно через AI-чат (CloudPayments KZ, "
            "3-D Secure). На лендинге пакетов нет ссылок и кнопок «Купить» — "
            "это инфо-блок, а оформление — внутри Baqsy AI.",
            "callout",
        ),
        PageBreak(),
    ]


def section_client_flow() -> list:
    return [
        p("02. Путь клиента — от лендинга до PDF", "h1"),
        p(
            "Клиент проходит линейный сценарий: открывает лендинг → "
            "общается с AI → заполняет паспорт → видит пакеты и кейсы → "
            "оплачивает → проходит анкету → получает отчёт.",
        ),

        # Шаг 1
        step_card(
            "ШАГ 1", "Захождение на сайт",
            "Открывается лендинг baqsy.tnriazun.com",
            [
                p(
                    "Hero-блок на тёмном фоне с рунным паттерном. Главный CTA — "
                    "<b>«Открыть Baqsy AI»</b>. В правом нижнем углу — закреплённое "
                    "окошко агента (карточка чата), которое следует за скроллом.",
                ),
                p(
                    "Минимум блоков: Hero → Пакеты (заперты) → Блог/глоссарий → "
                    "Кейсы (заперты) → FAQ → Footer. Без шоумена.",
                ),
            ],
        ),

        # Шаг 2
        step_card(
            "ШАГ 2", "Открытие чата",
            "Клиент жмёт «Открыть Baqsy AI»",
            [
                p(
                    "Чат разворачивается в полноэкранный модал на мобайле / "
                    "большую модалку на десктопе. Шапка: «Baqsy AI · Онлайн · "
                    "отвечает мгновенно». Первое сообщение — приветствие "
                    "из админки (поле <b>greeting</b>).",
                ),
                p(
                    "Под приветствием — 4 кнопки быстрых ответов: «Расскажи про "
                    "аудит», «Сколько это стоит», «Сроки и формат», "
                    "«Безопасность данных». Все настраиваются админом.",
                ),
            ],
        ),

        # Шаг 3
        step_card(
            "ШАГ 3", "Знакомство и предварительные вопросы",
            "AI ведёт живой диалог",
            [
                p(
                    "Клиент задаёт вопросы текстом или жмёт quick-replies. "
                    "Каждое сообщение отправляется на <code>POST /api/v1/chat/message/</code>, "
                    "Django передаёт всю историю + system_prompt в OpenAI "
                    "(gpt-4o-mini, температура 0.5, max 800 токенов).",
                ),
                p(
                    "AI спрашивает имя, компанию, отрасль, город, WhatsApp — "
                    "по одному вопросу за раз, в естественной форме.",
                ),
            ],
        ),

        # Шаг 4
        step_card(
            "ШАГ 4", "Заполнение паспорта компании",
            "= регистрация → разблокирует доступ к пакетам и кейсам",
            [
                p(
                    "Над полем ввода в чате есть быстрая ссылка «Быстро "
                    "заполнить профиль и перейти к оплате» — открывает "
                    "встроенную форму (имя · компания · город · WhatsApp).",
                ),
                p(
                    "При сохранении создаётся <b>ClientProfile</b> + "
                    "<b>BaseUser</b>, выдаётся JWT (access + refresh, "
                    "сохраняются в localStorage). Сессия становится "
                    "<i>qualified</i>.",
                ),
                p(
                    "После сохранения автоматически снимаются «замки» с "
                    "секций <b>Пакеты</b> и <b>Кейсы мировых компаний</b>. "
                    "Клиент видит детали: цена, что входит, разборы.",
                    "callout",
                ),
            ],
        ),

        # Шаг 5
        step_card(
            "ШАГ 5", "Выбор пакета",
            "Ashıde 1 или Ashıde 2",
            [
                p(
                    "<b>Ashıde 1</b> — для одного человека. Прайс в тенге. "
                    "25 вопросов (для менеджера) или 38 (для владельца / "
                    "топ-менеджера) — анкета адаптивная, ветвится по роли.",
                ),
                p(
                    "<b>Ashıde 2</b> — групповой формат. $729. Инициатор "
                    "оплачивает, AI спрашивает «Сколько участников (3–7)?», "
                    "клиент вводит ФИО / Email / WhatsApp каждого. Система "
                    "генерирует уникальные ссылки <code>/invite/&lt;token&gt;</code> "
                    "и автоматически рассылает email-приглашения. На WhatsApp "
                    "доступна wa.me-ссылка для ручной пересылки.",
                ),
            ],
        ),

        # Шаг 6
        step_card(
            "ШАГ 6", "Оплата",
            "CloudPayments KZ Widget",
            [
                p(
                    "Внутри чата открывается виджет CloudPayments. 3-D Secure "
                    "обязателен. Реквизиты карты на стороне Baqsy не "
                    "хранятся — обрабатывает CloudPayments.",
                ),
                p(
                    "После успеха CloudPayments шлёт webhook "
                    "<code>POST /api/v1/payments/cloudpayments/pay/</code>. "
                    "Django проверяет HMAC-подпись, идемпотентно создаёт "
                    "<b>Payment</b>, продвигает <b>Submission</b> в статус "
                    "<i>paid</i>, асинхронно — в <i>in_progress_full</i>.",
                ),
            ],
        ),

        # Шаг 7
        step_card(
            "ШАГ 7", "Прохождение анкеты",
            "Бот задаёт по одному вопросу",
            [
                p(
                    "Чат переключается в режим <b>questionnaire</b>. Появляется "
                    "прогресс-бар вверху: «X из 25», стадия (этап I, II, III). "
                    "Каждый вопрос — отдельное сообщение от AI.",
                ),
                p(
                    "Типы вопросов: текст (короткий / длинный), число, URL, "
                    "выбор одного варианта (кнопки), множественный выбор. "
                    "Условная логика: например, для роли «Менеджер» "
                    "пропускается этап III и блок II владельца.",
                ),
                p(
                    "Каждый ответ сохраняется в <b>Answer</b>. Клиент может "
                    "закрыть вкладку, прогресс не теряется — при возврате "
                    "по тому же session_id чат продолжает с последнего вопроса.",
                ),
            ],
        ),

        # Шаг 8 (для Ashide 2)
        step_card(
            "ШАГ 8 (только для Ashıde 2)", "Кворум коллег",
            "Каждый участник проходит свою анкету",
            [
                p(
                    "Каждый коллега получает email + WhatsApp ссылку. Открывает "
                    "<code>/invite/&lt;token&gt;</code> (без логина), видит "
                    "интро от инициатора и проходит ту же анкету анонимно.",
                ),
                p(
                    "Ответы каждого участника сохраняются в его собственный "
                    "<b>Submission</b>, привязанный к <b>AuditGroup</b>. "
                    "Эксперт видит все ответы группы для агрегации.",
                ),
                p(
                    "Когда все 3–7 анкет заполнены, в админке "
                    "<code>/admin/submissions/auditgroup/</code> плашка "
                    "становится зелёной X/Y ✓.",
                    "callout",
                ),
            ],
        ),

        # Шаг 9
        step_card(
            "ШАГ 9", "Ожидание отчёта",
            "Кабинет клиента",
            [
                p(
                    "Клиент видит <code>/cabinet</code> со статус-баром: "
                    "Оплачено → Анкета → Аудит → Готово. Срок — 3–5 рабочих "
                    "дней. Прогресс анкеты обновляется в реальном времени.",
                ),
            ],
        ),

        # Шаг 10
        step_card(
            "ШАГ 10", "Получение PDF",
            "WhatsApp",
            [
                p(
                    "Когда эксперт отметил отчёт «отправлен», PDF приходит "
                    "сообщением в WhatsApp клиента — с ссылкой на файл и "
                    "сопроводительным текстом. PDF именной: имя и компания "
                    "клиента на обложке.",
                ),
                p(
                    "Клиент может скачать PDF снова из <code>/cabinet</code> "
                    "в любое время — ссылка не истекает.",
                ),
            ],
        ),

        PageBreak(),
    ]


def section_admin_flow() -> list:
    return [
        p("03. Путь администратора", "h1"),
        p(
            "Админ-панель построена на Django Admin + Unfold. Полный "
            "доступ к контенту, AI-конфигурации, заявкам, генерации "
            "отчётов и доставке.",
        ),
        p(
            "<b>URL</b>: https://baqsy.tnriazun.com/admin/<br/>"
            "<b>Логин</b>: admin@baqsy.tnriazun.com",
            "callout",
        ),

        # Дашборд
        step_card(
            "АДМИН · 01", "Дашборд",
            "Что видно при входе",
            [
                p(
                    "На главной — фильтры (отрасль, тариф, город, даты) + "
                    "4 карточки KPI (всего заказов, в работе, завершённых, "
                    "выручка) + 6 плиток быстрых действий (заказы, тексты "
                    "лендинга, тарифы, клиенты, анкеты, отчёты).",
                ),
            ],
        ),

        # Контент
        step_card(
            "АДМИН · 02", "Тексты лендинга",
            "/admin/content/contentblock/",
            [
                p(
                    "21 блок: hero_title, hero_subtitle, method_title, "
                    "tariff_section_title, cases_title, faq_1_q/a … faq_5_q/a "
                    "и т.д. Любой блок — изменяемый.",
                ),
                p(
                    "Плашки секций (Hero / Метод / Кейсы / FAQ) для удобной "
                    "навигации. Превью текста в списке. Кнопка «✏️ Изменить» "
                    "в каждой строке.",
                ),
                p(
                    "<b>Важно</b>: фронт кеширует на 5 минут — изменения "
                    "видны на сайте через 5 мин или после hard-refresh.",
                ),
            ],
        ),

        # Кейсы
        step_card(
            "АДМИН · 03", "Кейсы мировых компаний",
            "/admin/cases/case/",
            [
                p(
                    "Slug, заголовок, описание, компания, отрасль, логотип "
                    "(image), обложка, метрика («+15%»), accent-цвет, "
                    "короткий текст для карточки, полный текст для деталки.",
                ),
                p(
                    "Кейсы видны на лендинге в секции «Кейсы мировых "
                    "компаний» (заперты до регистрации) и на отдельных "
                    "страницах /cases/&lt;slug&gt;.",
                ),
            ],
        ),

        # Блог
        step_card(
            "АДМИН · 04", "Блог · Глоссарий",
            "/admin/blog/blogpost/",
            [
                p(
                    "Slug, заголовок, краткое описание, тело, обложка, "
                    "категория (Статья / Глоссарий / Философия), время "
                    "чтения, флаг «Опубликовать», порядок.",
                ),
                p(
                    "Используйте для разогрева аудитории и расшифровки "
                    "терминологии Кода Вечного Иля.",
                ),
            ],
        ),

        # AI Chat
        step_card(
            "АДМИН · 05", "AI-ассистент чата",
            "/admin/ai/aiassistantconfig/",
            [
                p(
                    "Главный AI, который ведёт первичный диалог с клиентом "
                    "на лендинге. Параметры:",
                ),
                bullet("<b>greeting</b> — первое приветствие в чате"),
                bullet("<b>system_prompt</b> — характер ассистента, фокус, тон"),
                bullet("<b>quick_replies</b> — 4 кнопки быстрых ответов (JSON)"),
                bullet("<b>model</b> — gpt-4o-mini для скорости / gpt-4o для качества"),
                bullet("<b>temperature, max_tokens</b> — настройки генерации"),
                bullet("<b>tariff_prompt</b> — текст про переход к оплате"),
            ],
        ),

        # 12 ассистентов
        step_card(
            "АДМИН · 06", "12 параметров аудита (12 AI-ассистентов)",
            "/admin/industries/auditparameter/",
            [
                p("<b>Главная фича системы.</b>", "body_strong"),
                p(
                    "12 специализированных ассистентов — каждый со своим "
                    "system_prompt, своей моделью, своей температурой. "
                    "Каждый отвечает за анализ ответов в своей теме.",
                ),
                p(
                    "Стартовый набор (можно переименовать / удалить / добавить):"
                ),
                bullet("01. Паспорт компании"),
                bullet("02. Роль руководителя в системе"),
                bullet("03. Стратегия и цели"),
                bullet("04. Операционная эффективность"),
                bullet("05. Качество команды"),
                bullet("06. Контроль и отчётность"),
                bullet("07. Финансовая дисциплина"),
                bullet("08. Родственные узлы и непотизм"),
                bullet("09. Теневое влияние"),
                bullet("10. Образ жизни и репутация"),
                bullet("11. Личная устойчивость основателя"),
                bullet("12. Внешние зависимости"),
                p(
                    "Каждый параметр имеет промпт типа: «Ты — стратегический "
                    "консультант. Оцени, есть ли у компании осознанная "
                    "стратегия. Найди разрыв между декларируемыми целями и "
                    "реальностью». В конце автоматически подставляются "
                    "ответы клиента, относящиеся к этому параметру.",
                ),
            ],
        ),

        # Привязка вопросов
        step_card(
            "АДМИН · 07", "Привязка вопросов к параметрам",
            "/admin/industries/question/",
            [
                p(
                    "В анкете 100 вопросов, к каждому нужно прикрепить один "
                    "из 12 параметров. От этого зависит, какой ИИ-ассистент "
                    "будет анализировать ответ.",
                ),
                p("<b>Как делать массово</b> (10 минут на 100 вопросов):", "body_strong"),
                num(1, "Включите фильтр «Параметр» → выберите «–» (без параметра)"),
                num(2, "Выделите чекбоксами 10–15 вопросов одной темы"),
                num(3, "В выпадающем списке Action — «Привязать к параметру: <название>»"),
                num(4, "Нажмите Go"),
                num(5, "Повторите для следующей темы"),
                p(
                    "В выпадашке 12 экшенов — по одному на каждый параметр. "
                    "Также можно прямо в списке менять колонку <b>Параметр</b> "
                    "у каждого вопроса (list_editable).",
                    "callout",
                ),
            ],
        ),

        # Приём заказа
        step_card(
            "АДМИН · 08", "Заказы и анкеты",
            "/admin/submissions/submission/",
            [
                p(
                    "Список всех заявок. Фильтрация по статусу, тарифу, отрасли. "
                    "Внутри карточки заказа: данные клиента, FSM-статус, "
                    "ответы клиента (inline) и связанный AuditReport.",
                ),
                p(
                    "Когда статус заказа = <i>completed</i> (анкета "
                    "пройдена), в кейсе отображается inline-форма "
                    "AuditReport — там пишется текст аудита.",
                ),
            ],
        ),

        # Группы аудита
        step_card(
            "АДМИН · 09", "Групповой аудит (Ashıde 2)",
            "/admin/submissions/auditgroup/",
            [
                p(
                    "Список всех групп. Цветная плашка X/Y показывает кворум "
                    "(сколько участников из 3–7 завершили анкету).",
                ),
                p(
                    "Внутри группы — inline участников с прямыми ссылками "
                    "<code>/invite/&lt;token&gt;</code>, статусом каждого, "
                    "временем приглашения и завершения. Можно перепослать "
                    "email одной кнопкой.",
                ),
            ],
        ),

        # Генерация отчёта
        step_card(
            "АДМИН · 10", "Генерация черновика отчёта",
            "Главная кнопка для эксперта",
            [
                p("<b>Шаг 1.</b> Открыть AuditReport (создаётся автоматически когда заказ переходит в completed)."),
                p("<b>Шаг 2.</b> Нажать кнопку «<b>Сгенерировать черновик отчёта (12 ИИ-ассистентов)</b>»."),
                p(
                    "Что происходит за кулисами: для каждого из 12 активных "
                    "параметров запускается отдельный вызов OpenAI с "
                    "параметр-специфичным system_prompt и подмножеством "
                    "ответов клиента. ~30 секунд → markdown-черновик из "
                    "12 секций в поле <b>admin_text</b>."
                ),
                p("<b>Шаг 3.</b> Эксперт читает, корректирует, добавляет свои наблюдения."),
                p("<b>Шаг 4.</b> Нажимает «Подтвердить и отправить PDF» → Celery рендерит PDF через WeasyPrint, выгружает в MinIO, заполняет pdf_url."),
            ],
        ),

        # Отправка
        step_card(
            "АДМИН · 11", "Отправка клиенту",
            "WhatsApp вручную",
            [
                p(
                    "Когда pdf_url заполнен, в списке отчётов появляется "
                    "зелёная кнопка <b>«💬 Отправить клиенту»</b>. Клик "
                    "открывает wa.me-ссылку с pre-filled текстом: имя "
                    "клиента, название компании, ссылка на PDF.",
                ),
                p(
                    "Эксперт проверяет / дополняет текст в WhatsApp Web и "
                    "отправляет. Возвращается в админку, нажимает кнопку "
                    "<b>«Отметить доставленным»</b> — статус заказа "
                    "становится <i>delivered</i>, история закрыта.",
                ),
            ],
        ),

        PageBreak(),
    ]


def section_architecture() -> list:
    return [
        p("04. Архитектура — что под капотом", "h1"),
        p("Технологический стек", "h3"),
        key_value_table([
            ("Frontend", "React 19 + Vite + TanStack Query · TypeScript · Tailwind CSS 4"),
            ("Backend", "Django 5.2 · DRF · Celery · django-fsm-2"),
            ("AI", "OpenAI Python SDK · gpt-4o-mini / gpt-4o"),
            ("PDF-рендер", "WeasyPrint + Jinja2 (шаблоны в стиле «Вечный Иль»)"),
            ("База данных", "PostgreSQL 16"),
            ("Очередь задач", "Celery + Redis"),
            ("Файлы", "MinIO (S3-совместимое хранилище)"),
            ("Платежи", "CloudPayments KZ · 3-D Secure · HMAC webhooks"),
            ("Email", "Django SMTP — приглашения участников Ashıde 2"),
            ("Web-сервер", "host nginx + gunicorn (Docker)"),
            ("TLS", "Let's Encrypt · автопродление через certbot.timer"),
            ("Деплой", "Docker Compose · 6 сервисов · uptime 99.5%+"),
        ]),
        Spacer(1, 12),
        p("Сервисы Docker", "h3"),
        bullet("<b>web</b> — Django + gunicorn (порт 8000, 127.0.0.1 only)"),
        bullet("<b>worker</b> — Celery worker (PDF-рендер, рассылки)"),
        bullet("<b>beat</b> — Celery beat scheduler (напоминания)"),
        bullet("<b>db</b> — PostgreSQL 16"),
        bullet("<b>redis</b> — кеш + брокер Celery"),
        bullet("<b>minio</b> — S3-совместимое хранилище для PDF и логотипов"),
        Spacer(1, 12),
        p("Безопасность", "h3"),
        bullet("HTTPS обязателен · HSTS на год"),
        bullet("X-Frame-Options DENY (защита от clickjacking)"),
        bullet("X-Content-Type-Options nosniff"),
        bullet("Referrer-Policy strict-origin-when-cross-origin"),
        bullet("django-axes — защита от брутфорса (5 попыток → блокировка IP)"),
        bullet("CSRF-cookie + Session-cookie с флагом Secure"),
        bullet("CORS только для разрешённых доменов"),
        bullet("Rate-limit на чат: 60 запросов в минуту с IP"),
        bullet("CloudPayments webhook проверяет HMAC-подпись"),
        PageBreak(),
    ]


def section_technical() -> list:
    return [
        p("05. Технические детали для оператора", "h1"),
        p("URLs", "h3"),
        key_value_table([
            ("Сайт", "https://baqsy.tnriazun.com/"),
            ("Лендинг", "/"),
            ("Личный кабинет", "/cabinet"),
            ("Кейс", "/cases/<slug>"),
            ("Блог-пост", "/blog/<slug>"),
            ("Страница участника группы", "/invite/<token>"),
            ("Админка", "/admin/"),
            ("Health check", "/health/"),
        ]),
        Spacer(1, 8),
        p("Доступ к админке", "h3"),
        key_value_table([
            ("Email", "admin@baqsy.tnriazun.com"),
            ("Пароль", "4aOTBV8X2ZkYu4ZUMrQD"),
            ("Рекомендация", "Сменить пароль при первом входе"),
        ]),
        Spacer(1, 8),
        p("API эндпойнты (публичные)", "h3"),
        bullet("<b>GET /api/v1/chat/config/</b> — конфигурация AI-чата"),
        bullet("<b>POST /api/v1/chat/start/</b> — начать чат-сессию"),
        bullet("<b>POST /api/v1/chat/message/</b> — отправить сообщение"),
        bullet("<b>POST /api/v1/chat/collect/</b> — сохранить профиль"),
        bullet("<b>POST /api/v1/chat/auth-token/</b> — получить JWT"),
        bullet("<b>POST /api/v1/chat/start-questionnaire/</b> — начать анкету (после оплаты)"),
        bullet("<b>GET /api/v1/cases/</b> — список кейсов"),
        bullet("<b>GET /api/v1/blog/</b> — список статей"),
        bullet("<b>GET /api/v1/content/</b> — текстовые блоки"),
        bullet("<b>GET /api/v1/payments/tariffs/</b> — список тарифов"),
        bullet("<b>POST /api/v1/audit-groups/</b> — создать группу (Ashıde 2)"),
        bullet("<b>GET /api/v1/invite/&lt;token&gt;/</b> — контекст для участника"),
        bullet("<b>POST /api/v1/invite/&lt;token&gt;/answer/</b> — сохранить ответ"),
        Spacer(1, 8),
        p("Полезные команды на сервере", "h3"),
        Paragraph(
            "ssh debian@78.40.108.112<br/>"
            "cd /opt/baqsy<br/>"
            "<br/>"
            "# Перезапуск backend<br/>"
            "docker compose -f docker/docker-compose.prod.yml --env-file .env restart web<br/>"
            "<br/>"
            "# Пересборка фронта (после правки кода)<br/>"
            "cd /opt/baqsy/frontend &amp;&amp; npm run build<br/>"
            "<br/>"
            "# Применить миграции<br/>"
            "docker compose -f docker/docker-compose.prod.yml exec -T web python manage.py migrate<br/>"
            "<br/>"
            "# Подсыпать стартовые данные<br/>"
            "docker compose -f docker/docker-compose.prod.yml exec -T web python manage.py seed_audit_parameters<br/>"
            "docker compose -f docker/docker-compose.prod.yml exec -T web python manage.py seed_baqsylyq<br/>"
            "<br/>"
            "# Логи всех контейнеров<br/>"
            "docker compose -f docker/docker-compose.prod.yml logs --tail 100 -f",
            S["code"],
        ),
        PageBreak(),
    ]


def section_checklist() -> list:
    return [
        p("06. Чек-лист запуска", "h1"),
        p("Что должно быть настроено перед публикацией для клиентов:", "body_strong"),
        Spacer(1, 6),
        p("Бэкенд / инфраструктура", "h3"),
        bullet("✓ Все 6 контейнеров healthy (web, worker, beat, db, redis, minio)"),
        bullet("✓ Let's Encrypt сертификат (автопродление включено)"),
        bullet("✓ DNS A-запись baqsy.tnriazun.com → 78.40.108.112"),
        bullet("✓ Все миграции применены"),
        bullet("✓ OpenAI ключ — пополнен баланс"),
        bullet("☐ CloudPayments PUBLIC_ID и API_SECRET в .env"),
        bullet("☐ EMAIL_HOST настроен (для приглашений Ashıde 2)"),
        Spacer(1, 8),
        p("Контент", "h3"),
        bullet("✓ 21 текстовый блок лендинга (можно править)"),
        bullet("✓ 12 параметров аудита с промптами"),
        bullet("✓ 100 вопросов анкеты «Digital Baqsylyq»"),
        bullet("✓ 2 демо-кейса (нужно заменить на реальные)"),
        bullet("☐ Привязать 100 вопросов к 12 параметрам (через bulk-action)"),
        bullet("☐ Загрузить логотипы реальных кейсов"),
        bullet("☐ Опубликовать первые 3 статьи блога"),
        Spacer(1, 8),
        p("AI-настройки", "h3"),
        bullet("✓ AIAssistantConfig (главный чат-ассистент) — заполнен"),
        bullet("✓ 12 AuditParameter — стартовые промпты"),
        bullet("☐ Отшлифовать промпты под свой бренд"),
        bullet("☐ Решить — gpt-4o-mini везде или для важных параметров — gpt-4o"),
        Spacer(1, 8),
        p("UX финиш", "h3"),
        bullet("☐ Сменить дефолтный пароль админки"),
        bullet("☐ Создать второй staff-аккаунт (на случай блокировки axes)"),
        bullet("☐ Прогнать end-to-end сценарий — от лендинга до получения PDF"),
        bullet("☐ Настроить мониторинг (uptime + ошибки в логах)"),
        PageBreak(),
    ]


def section_outro() -> list:
    return [
        p("07. Дальнейшее развитие", "h1"),
        p("Что заложено в архитектуру для будущего", "h3"),
        p(
            "<b>Mini-сервер с локальными моделями</b> — каждый из 12 "
            "параметров в админке имеет поле <code>model</code>. Замена "
            "OpenAI на собственный inference-сервер (например, vLLM с "
            "Llama-3.3) — это правка одной настройки, без изменений в коде.",
        ),
        p(
            "<b>Параллельная обработка</b> — analyze_parameter() уже "
            "написан изолированно: каждый параметр можно гонять в "
            "отдельном Celery-task'е, чтобы все 12 секций отчёта "
            "генерировались параллельно (~5 сек вместо 30).",
        ),
        p(
            "<b>WhatsApp Auto-delivery</b> — Wazzup24 интеграция в коде "
            "уже есть (<code>apps/delivery/tasks.py</code>), нужно лишь "
            "купить тариф у Wazzup и прописать <code>WAZZUP24_API_KEY</code>. "
            "После этого PDF будет уходить клиенту автоматически.",
        ),
        p(
            "<b>Email-верификация</b> — для добавления полноценной "
            "регистрации с подтверждением email (а не только через чат) "
            "нужно дописать страницу <code>/verify/&lt;token&gt;</code> и "
            "соответствующий backend-эндпойнт.",
        ),
        p(
            "<b>A/B тестирование промптов</b> — модель AIAssistantConfig "
            "уже имеет <code>is_active</code> с уникальным ограничением "
            "(только один активный одновременно). Чтобы тестировать новые "
            "промпты — создаёте копию с <code>is_active=False</code>, "
            "правите, переключаете флаг.",
        ),
        Spacer(1, 12),
        p("Контакты для поддержки", "h3"),
        key_value_table([
            ("Email", "info@baqsy.kz"),
            ("Сервер", "78.40.108.112 (Debian, Docker 29.4)"),
            ("Репозиторий", "github.com/nagibator9986/opla"),
        ]),
        Spacer(1, 24),
        p(
            "Документ актуален на дату генерации. По мере развития "
            "платформы детали могут меняться — всегда сверяйтесь с "
            "/admin/ и актуальным README в репозитории.",
            "small",
        ),
    ]


# ─── Сборка ────────────────────────────────────────────────────────────
def build():
    out_dir = Path("/Users/a1111/Desktop/projects/oplata project/docs")
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "guide.pdf"

    doc = SimpleDocTemplate(
        str(out),
        pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title="Baqsy · Digital Baqsylyq · Guide",
        author="Baqsy System",
    )

    story: list = []
    story += cover_page()
    story += section_overview_simple()
    story += section_client_flow()
    story += section_admin_flow()
    story += section_architecture()
    story += section_technical()
    story += section_checklist()
    story += section_outro()

    def on_page(canvas, doc):
        canvas.saveState()
        page_num = canvas.getPageNumber()
        if page_num > 1:
            canvas.setFont(REGULAR, 8)
            canvas.setFillColor(INK_500)
            canvas.drawRightString(
                A4[0] - 2 * cm, 1.2 * cm,
                f"Baqsy · Digital Baqsylyq · стр. {page_num}",
            )
            # Top stripe
            canvas.setFillColor(BRAND_500)
            canvas.rect(0, A4[1] - 2 * mm, A4[0], 2 * mm, fill=1, stroke=0)
        canvas.restoreState()

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    size_kb = os.path.getsize(out) / 1024
    print(f"Generated: {out} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    build()
