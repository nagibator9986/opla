# Phase 3: Telegram Bot - Research

**Researched:** 2026-04-16
**Domain:** aiogram 3.27 FSM bot — thin REST client over Django API
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Структура бота:**
- `bot/handlers/start.py` — `/start`, определение нового vs вернувшегося клиента
- `bot/handlers/onboarding.py` — FSM-сценарий 5 базовых вопросов
- `bot/handlers/questionnaire.py` — FSM-сценарий прохождения анкеты
- `bot/handlers/commands.py` — `/status`, `/help`
- `bot/states/` — FSM-состояния (StatesGroup для onboarding и questionnaire)
- `bot/services/api_client.py` — httpx-обёртка над Django REST API
- `bot/keyboards/` — InlineKeyboardMarkup-билдеры
- `bot/config.py` — чтение env через `python-decouple`
- `bot/main.py` — инициализация Bot, Dispatcher, RedisStorage, подключение handlers

**FSM-состояния:**
```python
class OnboardingStates(StatesGroup):
    waiting_name = State()
    waiting_company = State()
    waiting_industry = State()    # inline keyboard
    waiting_phone = State()
    waiting_city = State()

class QuestionnaireStates(StatesGroup):
    answering = State()           # generic state, question data in FSM data
```

**API-клиент (httpx):**
- `bot/services/api_client.py` — async httpx.AsyncClient
- Base URL: `API_BASE_URL=http://web:8000/api/v1`
- Заголовок `X-Bot-Token: {BOT_API_SECRET}` для bot-эндпоинтов
- Методы: `onboard()`, `create_deeplink()`, `get_industries()`, `create_submission()`,
  `get_next_question()`, `save_answer()`, `complete_submission()`, `get_submission_status()`
- Error handling: httpx.HTTPStatusError → «Ошибка, попробуйте позже»

**Онбординг:** 5 вопросов (имя, компания, отрасль inline KB, WhatsApp, город) → POST /bot/onboarding/ → POST /bot/deeplink/ → URL на сайт

**Анкета:** триггер через deep-link `/start questionnaire_{submission_id}`, цикл next-question → answer → repeat, 204 → complete

**Вопросы по field_type:**
- `text` → обычный ввод
- `number` → валидация int/float
- `choice` → InlineKeyboard с вариантами
- `multichoice` → toggle-кнопки (✅/❌), кнопка «Готово»

**Команды:** `/start` (new/returning), `/status`, `/help`

**Восстановление:** при `/start` проверяем Submission `in_progress_full` через Django API

**24h-напоминание:** Celery beat каждые 6 часов, sync `requests` к Telegram Bot API

**Redis:** `RedisStorage.from_url(AIOGRAM_REDIS_URL)` где `AIOGRAM_REDIS_URL=redis://redis:6379/1`

**Long-polling** в dev, webhook в prod (Phase 8)

**Bot container:** `depends_on: web: condition: service_healthy`

### Claude's Discretion
- Точные тексты сообщений бота (русский язык)
- Обработка невалидного ввода (retry vs skip)
- Timeout для ответов пользователя
- Emoji в сообщениях бота
- Порядок кнопок в inline-клавиатуре отраслей
- Точная структура `/help` текста

### Deferred Ideas (OUT OF SCOPE)
- Webhook mode для production — Phase 8 (HARD-06)
- Отправка PDF через бота — Phase 6 (DLV-01)
- Inline-mode для поиска — не в скоупе
- Групповой чат поддержки — не в скоупе
- Мультиязычность бота — v2
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| BOT-01 | Бот стартует через `docker-compose up`, aiogram 3.27 + Redis FSM storage (db=1) | RedisStorage.from_url pattern, bot/main.py skeleton replacement |
| BOT-02 | Команда `/start` запускает FSM-сценарий онбординга | CommandStart() filter, FSMContext, OnboardingStates pattern |
| BOT-03 | Онбординг: 5 вопросов — имя, компания, отрасль (inline KB), WhatsApp, город | State-per-question pattern, InlineKeyboardBuilder for industries |
| BOT-04 | После онбординга бот выдаёт deep-link на сайт с тарифами | POST /bot/onboarding/ → POST /bot/deeplink/ → InlineKeyboardButton url= |
| BOT-05 | Реагирует на сигнал об оплате и начинает анкету | CommandStart(deep_link=True), decode_payload(), QuestionnaireStates |
| BOT-06 | Каждый ответ сразу отправляется в Django API | httpx.AsyncClient.post() per answer, no local cache |
| BOT-07 | Прогресс-индикатор «Вопрос N/M» в каждом сообщении | NextQuestion API returns progress field, embed in message text |
| BOT-08 | Команда `/status` показывает статус заказа | GET /submissions/{id}/, format status for user |
| BOT-09 | Команда `/help` показывает справку | Simple message handler, no API call |
| BOT-10 | При обрыве FSM восстанавливает прогресс из Django | GET /submissions/ filter in_progress_full by telegram_id, resume flow |
| BOT-11 | Напоминание через 24h если анкета не завершена (Celery beat) | Celery beat periodic task, direct HTTP to Telegram Bot API via requests |
</phase_requirements>

---

## Summary

Phase 3 реализует aiogram 3.27 Telegram-бот как тонкий REST-клиент Django API. Вся бизнес-логика уже живёт в Django (фазы 1 и 2). Бот — это только диалоговый слой: он собирает ответы пользователя через FSM и проксирует их в API.

Стек уже установлен в `bot/pyproject.toml`: aiogram 3.27.0, httpx 0.27.0, redis 5.3.0, python-decouple, structlog. Django API-эндпоинты (все 8) реализованы в Phase 2 и готовы. Skeleton `bot/main.py` нужно заменить на полноценный Dispatcher с RedisStorage и подключёнными роутерами.

Ключевые технические паттерны: aiogram Router + StatesGroup + RedisStorage (db=1), httpx.AsyncClient с базовым URL и заголовком X-Bot-Token, CommandStart(deep_link=True) с decode_payload для `/start questionnaire_...`, InlineKeyboardBuilder с CallbackData для выбора отраслей и multichoice-вопросов, sync `requests` в Celery beat для 24h-напоминаний.

**Primary recommendation:** Построить бота по принципу «один роутер — один хендлер-файл», FSM-данные хранить минимально (submission_id + jwt_token + question_index), каждый шаг анкеты сохранять немедленно в API — бот должен быть crash-safe.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| aiogram | 3.27.0 | Telegram bot framework | Уже установлен. Производительный async, встроенный FSM, RedisStorage, Router API |
| redis (py) | 5.3.0 | FSM state storage backend | Уже установлен. aiogram 3 использует этот пакет напрямую (не aioredis) |
| httpx | 0.27.0 | Async HTTP клиент к Django API | Уже установлен. Нативный async, поддержка connection pooling, таймаутов |
| python-decouple | ^3.8 | Чтение env переменных | Уже установлен. Типизированный .env reader |
| structlog | 25.5.0 | Структурированные логи | Уже установлен. JSON в prod, colorized в dev |

### Supporting (для Celery beat задачи в backend/)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| requests | (stdlib-like, уже в Django) | Sync HTTP в Celery beat для Telegram Bot API | BOT-11: 24h-напоминание из Celery worker |
| django-celery-beat | 2.7.0 | Периодические задачи | Хранит расписание в БД, управляется из Admin |

### Тестирование бота

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest-asyncio | ^0.23 | Async тесты для bot handlers | Нужно добавить в dev deps бота |
| pytest-mock | ^3.14 | Мокинг httpx.AsyncClient | Изоляция bot handler тестов от реального API |

**Добавить в bot/pyproject.toml dev deps:**
```toml
[tool.poetry.group.dev.dependencies]
pytest = "^8.3"
pytest-asyncio = "^0.23"
pytest-mock = "^3.14"
```

**Installation (bot dev deps):**
```bash
cd bot && poetry add --group dev pytest pytest-asyncio pytest-mock
```

---

## Architecture Patterns

### Recommended Project Structure

```
bot/
├── main.py               # Bot + Dispatcher + RedisStorage + include_router
├── config.py             # python-decouple settings
├── handlers/
│   ├── __init__.py
│   ├── start.py          # /start — new vs returning, deep-link dispatch
│   ├── onboarding.py     # OnboardingStates FSM (5 steps)
│   ├── questionnaire.py  # QuestionnaireStates FSM (N questions loop)
│   └── commands.py       # /status, /help
├── states/
│   ├── __init__.py
│   ├── onboarding.py     # OnboardingStates(StatesGroup)
│   └── questionnaire.py  # QuestionnaireStates(StatesGroup)
├── keyboards/
│   ├── __init__.py
│   ├── industry.py       # InlineKeyboardBuilder for industry selection
│   └── questionnaire.py  # choice/multichoice builders
├── services/
│   └── api_client.py     # httpx.AsyncClient wrapper
├── pyproject.toml        # aiogram 3.27, httpx, redis already here
└── Dockerfile            # ready, no changes needed
```

### Pattern 1: main.py — Dispatcher + RedisStorage + Startup

**What:** Инициализация Bot, Dispatcher, подключение RedisStorage (db=1), регистрация роутеров через `dp.include_router()`, запуск long-polling.

**Source:** aiogram 3.27 official docs — https://docs.aiogram.dev/en/latest/dispatcher/finite_state_machine/storages.html

```python
# bot/main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from decouple import config

from bot.handlers.start import router as start_router
from bot.handlers.onboarding import router as onboarding_router
from bot.handlers.questionnaire import router as questionnaire_router
from bot.handlers.commands import router as commands_router

async def main() -> None:
    bot = Bot(token=config("TELEGRAM_BOT_TOKEN"))
    storage = RedisStorage.from_url(
        url=config("AIOGRAM_REDIS_URL", default="redis://redis:6379/1"),
        state_ttl=86400 * 7,   # 7 days
        data_ttl=86400 * 7,
    )
    dp = Dispatcher(storage=storage)
    dp.include_router(start_router)
    dp.include_router(onboarding_router)
    dp.include_router(questionnaire_router)
    dp.include_router(commands_router)

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
```

**Key points:**
- `RedisStorage.from_url()` принимает `state_ttl` и `data_ttl` как int (секунды)
- `dp.resolve_used_update_types()` — автоматически определяет нужные update types из зарегистрированных handlers (эффективнее чем `["message", "callback_query"]`)
- DB=1 — изолировано от Celery (DB=0) и deeplink Redis (DB=2)

### Pattern 2: FSM States + Router

**What:** Определение состояний через StatesGroup, регистрация handlers через Router с фильтром по состоянию.

**Source:** https://docs.aiogram.dev/en/latest/dispatcher/finite_state_machine/index.html

```python
# bot/states/onboarding.py
from aiogram.fsm.state import State, StatesGroup

class OnboardingStates(StatesGroup):
    waiting_name = State()
    waiting_company = State()
    waiting_industry = State()
    waiting_phone = State()
    waiting_city = State()

# bot/states/questionnaire.py
class QuestionnaireStates(StatesGroup):
    answering = State()   # generic — question data lives in FSM data dict
```

```python
# bot/handlers/onboarding.py  — паттерн одного шага
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

router = Router()

@router.message(OnboardingStates.waiting_name)
async def handle_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if not name or len(name) < 2:
        await message.answer("Пожалуйста, введите ваше имя (минимум 2 символа).")
        return
    await state.update_data(name=name)
    await state.set_state(OnboardingStates.waiting_company)
    await message.answer("Отлично! Теперь введите название вашей компании:")
```

**Key points:**
- `state.update_data(key=value)` сохраняет данные в Redis FSM data dict
- `state.set_state(StateClass.field)` переводит в следующее состояние
- Handler активируется ТОЛЬКО когда пользователь в указанном состоянии

### Pattern 3: /start — Новый vs Вернувшийся vs Deep-link

**What:** Один handler с тремя ветками логики. Использует `CommandStart()` для plain `/start` и `CommandStart(deep_link=True)` для `/start payload`.

**Source:** https://docs.aiogram.dev/en/latest/utils/deep_linking.html

```python
# bot/handlers/start.py
from aiogram import Router
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.deep_linking import decode_payload

router = Router()

@router.message(CommandStart(deep_link=True))
async def handle_start_deeplink(
    message: Message,
    command: CommandObject,
    state: FSMContext,
) -> None:
    """Handles /start questionnaire_{submission_id}"""
    payload = decode_payload(command.args)  # decodes base64url if needed
    # For plain payloads like "questionnaire_<uuid>", command.args works directly
    if payload.startswith("questionnaire_"):
        submission_id = payload.removeprefix("questionnaire_")
        await state.update_data(submission_id=submission_id)
        await state.set_state(QuestionnaireStates.answering)
        await start_questionnaire(message, state, submission_id)
    # ... other deep-link prefixes

@router.message(CommandStart())
async def handle_start(message: Message, state: FSMContext) -> None:
    """Plain /start — check profile existence"""
    telegram_id = message.from_user.id
    # Call Django API to check profile status...
    # ...
```

**Critical detail:** `command.args` содержит весь payload как строку. `decode_payload()` из `aiogram.utils.deep_linking` нужен только если payload был зашифрован через `encode_payload()`. Для нашего паттерна `questionnaire_{uuid}` — простая строка, `command.args` достаточно. Используем `decode_payload(command.args)` для единообразия на случай специальных символов.

**Порядок регистрации handlers важен:** `CommandStart(deep_link=True)` регистрируем ПЕРЕД `CommandStart()` иначе plain handler перехватит все сообщения.

### Pattern 4: InlineKeyboardBuilder — Industry Selection

**What:** Динамическое построение клавиатуры из списка отраслей, CallbackData для структурированной обработки callback.

**Source:** https://docs.aiogram.dev/en/latest/dispatcher/filters/callback_data.html

```python
# bot/keyboards/industry.py
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

class IndustryCallback(CallbackData, prefix="industry"):
    code: str   # industry.code (slug)

def build_industry_keyboard(industries: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ind in industries:
        builder.button(
            text=ind["name"],
            callback_data=IndustryCallback(code=ind["code"]),
        )
    builder.adjust(2)   # 2 колонки
    return builder.as_markup()

# В onboarding.py:
@router.callback_query(
    IndustryCallback.filter(),
    OnboardingStates.waiting_industry,
)
async def handle_industry_choice(
    callback: CallbackQuery,
    callback_data: IndustryCallback,
    state: FSMContext,
) -> None:
    await state.update_data(industry_code=callback_data.code)
    await callback.message.edit_reply_markup(reply_markup=None)  # убрать кнопки
    await callback.answer()
    await state.set_state(OnboardingStates.waiting_phone)
    await callback.message.answer("Введите ваш номер WhatsApp (например: +77001234567):")
```

**Key points:**
- `CallbackData` с `prefix` — данные кодируются как `industry:code_value`; строка callback_data ≤64 байт
- `builder.adjust(N)` — расставляет кнопки по N в ряд
- `callback.message.edit_reply_markup(reply_markup=None)` — убирает клавиатуру после выбора

### Pattern 5: Multichoice Toggle

**What:** Вопросы типа `multichoice` — кнопки-чекбоксы в FSM data, кнопка «Готово» отправляет результат.

```python
# bot/keyboards/questionnaire.py
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

class MultiChoiceCallback(CallbackData, prefix="mc"):
    option: str
    selected: bool   # текущий статус для toggle

def build_multichoice_keyboard(
    options: list[str],
    selected: set[str],
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for opt in options:
        mark = "✅" if opt in selected else "◻️"
        builder.button(
            text=f"{mark} {opt}",
            callback_data=MultiChoiceCallback(option=opt, selected=opt in selected),
        )
    builder.adjust(1)   # по одной кнопке в ряд
    builder.button(text="Готово ➡️", callback_data="mc_done")
    return builder.as_markup()

# Handler:
@router.callback_query(MultiChoiceCallback.filter(), QuestionnaireStates.answering)
async def handle_multichoice_toggle(
    callback: CallbackQuery,
    callback_data: MultiChoiceCallback,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    selected: set = set(data.get("mc_selected", []))
    if callback_data.option in selected:
        selected.discard(callback_data.option)
    else:
        selected.add(callback_data.option)
    await state.update_data(mc_selected=list(selected))
    # Rebuild keyboard with updated state
    question_data = data["current_question"]
    kb = build_multichoice_keyboard(
        options=question_data["options"]["choices"],
        selected=selected,
    )
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data == "mc_done", QuestionnaireStates.answering)
async def handle_multichoice_done(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    selected = data.get("mc_selected", [])
    submission_id = data["submission_id"]
    question_id = data["current_question"]["id"]
    await api_client.save_answer(submission_id, question_id, {"choices": selected})
    await state.update_data(mc_selected=[])
    await proceed_to_next_question(callback.message, state)
```

**Key points:**
- `F.data == "mc_done"` — фильтр по строковому значению callback_data
- `selected` хранится в FSM data как `list` (JSON-сериализуемый), не `set`
- `callback.message.edit_reply_markup()` обновляет клавиатуру без отправки нового сообщения
- Кнопка «Готово» имеет простую строку (не CallbackData объект) — короче, надёжнее

### Pattern 6: httpx.AsyncClient — API Client

**What:** Singleton async client с base URL, заголовками и таймаутами. Singleton на уровне модуля (не пересоздаётся для каждого запроса).

```python
# bot/services/api_client.py
import httpx
from decouple import config

_client: httpx.AsyncClient | None = None

def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=config("API_BASE_URL", default="http://web:8000/api/v1"),
            headers={"X-Bot-Token": config("BOT_API_SECRET")},
            timeout=httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0),
        )
    return _client


async def onboard(telegram_id: int, name: str, company: str,
                  industry_code: str, phone_wa: str, city: str) -> dict:
    """POST /bot/onboarding/ — create/update ClientProfile."""
    r = await get_client().post("/bot/onboarding/", json={
        "telegram_id": telegram_id,
        "name": name,
        "company": company,
        "industry_code": industry_code,
        "phone_wa": phone_wa,
        "city": city,
    })
    r.raise_for_status()
    return r.json()


async def create_deeplink(telegram_id: int) -> str:
    """POST /bot/deeplink/ — returns one-time token."""
    r = await get_client().post("/bot/deeplink/", json={"telegram_id": telegram_id})
    r.raise_for_status()
    return r.json()["token"]


async def get_next_question(submission_id: str, jwt_token: str) -> dict | None:
    """GET /submissions/{id}/next-question/ — returns question dict or None (204)."""
    headers = {"Authorization": f"Bearer {jwt_token}"}
    r = await get_client().get(
        f"/submissions/{submission_id}/next-question/",
        headers=headers,
    )
    if r.status_code == 204:
        return None   # all questions answered
    r.raise_for_status()
    return r.json()


async def save_answer(submission_id: str, question_id: int,
                      value: dict, jwt_token: str) -> None:
    """POST /submissions/{id}/answers/ — save answer immediately."""
    headers = {"Authorization": f"Bearer {jwt_token}"}
    r = await get_client().post(
        f"/submissions/{submission_id}/answers/",
        json={"question_id": question_id, "value": value},
        headers=headers,
    )
    r.raise_for_status()


async def get_or_create_jwt(telegram_id: int) -> str:
    """Exchange telegram_id for JWT via POST /bot/jwt-for-bot/ (bot-authed)."""
    r = await get_client().post("/bot/jwt/", json={"telegram_id": telegram_id})
    r.raise_for_status()
    return r.json()["access"]
```

**Key points:**
- Singleton client избегает повторного создания соединений при каждом вызове handler
- `X-Bot-Token` заголовок отправляется для bot-эндпоинтов; JWT (`Authorization: Bearer`) — для submission endpoints
- `httpx.Timeout` с раздельными таймаутами: connect=5s, read=30s (PDF generation может быть медленным)
- При `HTTPStatusError` — handler ловит и отправляет пользователю «Ошибка, попробуйте позже»; детали логируются

**Важная деталь по JWT-токенам:** Бот должен получить JWT для submission endpoints. Phase 2 реализовала endpoint `/api/v1/bot/jwt/` (или аналог) для выдачи JWT по telegram_id через X-Bot-Token. JWT хранится в FSM data под ключом `jwt_token`. При обрыве и восстановлении сессии — запрашивается заново.

### Pattern 7: FSM Data Layout для Questionnaire

```python
# FSM data структура при прохождении анкеты:
{
    "submission_id": "550e8400-e29b-41d4-a716-446655440000",
    "jwt_token": "eyJ...",
    "current_question": {
        "id": 42,
        "text": "Какой ваш годовой оборот?",
        "field_type": "choice",
        "options": {"choices": ["<100k", "100k-1M", ">1M"]},
        "progress": "5/27",
    },
    "mc_selected": [],   # для multichoice в progress
}
```

**Key points:**
- `current_question` хранится в FSM data чтобы не делать лишний API-вызов при каждом callback
- `mc_selected` сбрасывается в `[]` после отправки multichoice ответа
- `jwt_token` хранится в FSM data — не нужен новый roundtrip к API на каждый вопрос

### Pattern 8: Questionnaire Loop

```python
# bot/handlers/questionnaire.py
async def proceed_to_next_question(message_or_callback, state: FSMContext) -> None:
    """Central function: fetch next question and show it to user."""
    data = await state.get_data()
    submission_id = data["submission_id"]
    jwt_token = data["jwt_token"]

    question = await api_client.get_next_question(submission_id, jwt_token)

    if question is None:
        # 204 — all questions answered
        await api_client.complete_submission(submission_id, jwt_token)
        await state.clear()
        await message_or_callback.answer(
            "Спасибо! Ваша анкета передана аудитору. "
            "Вы получите уведомление о готовности аудита."
        )
        return

    await state.update_data(current_question=question)
    progress = question.get("progress", "")
    text = f"*Вопрос {progress}*\n\n{question['text']}"

    field_type = question["field_type"]
    if field_type in ("text", "number"):
        await message_or_callback.answer(text, parse_mode="Markdown")
    elif field_type == "choice":
        kb = build_choice_keyboard(question["options"]["choices"])
        await message_or_callback.answer(text, reply_markup=kb, parse_mode="Markdown")
    elif field_type == "multichoice":
        kb = build_multichoice_keyboard(question["options"]["choices"], selected=set())
        await message_or_callback.answer(text, reply_markup=kb, parse_mode="Markdown")
```

### Pattern 9: 24h Reminder — Celery Beat (sync)

**What:** Celery beat periodic task в `backend/`, вызывает Telegram Bot API напрямую через sync `requests`. Celery worker НЕ использует aiogram — только прямой HTTP.

**Source:** ARCHITECTURE.md — Invariant 6: Celery workers send Telegram messages via direct HTTP.

```python
# backend/apps/submissions/tasks.py  (добавить)
import requests
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

@shared_task(bind=True, max_retries=3)
def remind_incomplete_submissions(self):
    """Run every 6h via Celery beat. Remind users with 24h stale questionnaires."""
    from apps.submissions.models import Submission

    cutoff = timezone.now() - timedelta(hours=24)
    submissions = Submission.objects.filter(
        status="in_progress_full",
        updated_at__lt=cutoff,
    ).select_related("client")

    bot_token = settings.TELEGRAM_BOT_TOKEN
    tg_api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    for sub in submissions:
        telegram_id = sub.client.telegram_id
        if not telegram_id:
            continue
        # Simple rate limit: check last_reminded_at
        if sub.last_reminded_at and (timezone.now() - sub.last_reminded_at) < timedelta(hours=24):
            continue
        payload_text = f"questionnaire_{sub.id}"
        deep_link = f"https://t.me/BaqsyBot?start={payload_text}"
        text = (
            "У вас есть незавершённая анкета Baqsy!\n\n"
            f"Продолжите прохождение, чтобы получить аудит: {deep_link}"
        )
        try:
            r = requests.post(tg_api_url, json={
                "chat_id": telegram_id,
                "text": text,
                "disable_web_page_preview": True,
            }, timeout=10)
            r.raise_for_status()
            sub.last_reminded_at = timezone.now()
            sub.save(update_fields=["last_reminded_at"])
        except Exception as exc:
            self.retry(exc=exc, countdown=300)  # retry in 5 min
```

**Для Celery beat schedule добавить в `backend/baqsy/celery.py`:**
```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    "remind-incomplete-submissions": {
        "task": "apps.submissions.tasks.remind_incomplete_submissions",
        "schedule": crontab(minute=0, hour="*/6"),  # каждые 6 часов
    },
}
```

**Для Submission модели добавить поле:**
```python
# backend/apps/submissions/models.py
last_reminded_at = models.DateTimeField(null=True, blank=True)
# + миграция
```

**Key points:**
- `requests` (не httpx) — Celery worker синхронный, import `requests` напрямую
- `requests.post()` достаточно — никакого aiogram в Celery worker
- `last_reminded_at` на модели — простой guard против двойных напоминаний
- `select_for_update()` не нужен здесь — только update одного поля

### Pattern 10: Восстановление прогресса (BOT-10)

```python
# bot/handlers/start.py — блок восстановления
@router.message(CommandStart())
async def handle_start(message: Message, state: FSMContext) -> None:
    telegram_id = message.from_user.id

    # Проверить FSM data сначала (быстро, Redis)
    data = await state.get_data()
    if data.get("submission_id"):
        # FSM data жив — можно продолжить без API вызова
        await proceed_to_next_question(message, state)
        return

    # FSM data пуст (Redis перезапустился или TTL истёк) — спросить API
    try:
        profile_resp = await api_client.get_profile(telegram_id)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            # Новый пользователь
            await state.set_state(OnboardingStates.waiting_name)
            await message.answer("Добро пожаловать в Baqsy! Как вас зовут?")
            return
        raise

    # Проверить активную submission
    active_sub = await api_client.get_active_submission(telegram_id)
    if active_sub and active_sub["status"] == "in_progress_full":
        jwt_token = await api_client.get_or_create_jwt(telegram_id)
        await state.update_data(
            submission_id=str(active_sub["id"]),
            jwt_token=jwt_token,
        )
        await state.set_state(QuestionnaireStates.answering)
        await message.answer("Продолжим вашу анкету! 👋")
        await proceed_to_next_question(message, state)
    else:
        # Вернувшийся без активной анкеты
        deeplink_token = await api_client.create_deeplink(telegram_id)
        site_url = f"https://baqsy.kz/auth/{deeplink_token}"
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="Перейти к выбору тарифа ➡️", url=site_url)
        ]])
        await message.answer(
            f"С возвращением, {profile_resp['name']}! "
            "Для начала нового аудита выберите тариф:",
            reply_markup=kb,
        )
```

**Нужен дополнительный Django API endpoint:** `GET /api/v1/bot/active-submission/?telegram_id=...` — возвращает активную Submission (in_progress_full) для данного telegram_id. Проверить что этот endpoint существует в Phase 2, если нет — добавить в Wave 0 этой фазы.

### Anti-Patterns to Avoid

- **Импорт Django ORM в bot/:** `from apps.submissions.models import Submission` — НИКОГДА. Бот — тонкий клиент. Все данные через REST API.
- **Хранение JWT в постоянном хранилище бота:** JWT хранится ТОЛЬКО в FSM data (Redis TTL=7d). Не в файл, не в `.env`.
- **Блокирующие вызовы в async handler:** `requests.get(...)` в aiogram handler — блокирует event loop. Использовать `httpx.AsyncClient`.
- **Создание нового httpx.AsyncClient в каждом handler:** Дорого. Использовать singleton через `get_client()`.
- **Многоразовые deeplink токены:** Deeplink UUID — одноразовый (Phase 2 удаляет после обмена). Бот должен запрашивать новый для каждого входа на сайт.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| FSM state storage | Своя Redis schema для состояний | `RedisStorage` из aiogram.fsm.storage.redis | TTL management, key namespacing, race conditions |
| Callback data parsing | `message.text.split(":")[1]` | `CallbackData` с prefix | Type safety, ≤64 байт constraint, auto-encoding |
| Deep-link payload | `message.text.split()[1]` | `CommandStart(deep_link=True)` + `decode_payload()` | Корректная обработка base64url edge cases |
| Keyboard builder | `InlineKeyboardMarkup([[InlineKeyboardButton(...)]])` вручную | `InlineKeyboardBuilder` | Меньше boilerplate, `adjust()` для сетки |
| Retry на API errors | Свой цикл с `asyncio.sleep()` | httpx timeout + aiogram error handler | httpx Timeout уже обрабатывает connection retries |
| 24h reminder | Отдельный `asyncio.sleep()` loop в боте | Celery beat periodic task | Crash-safe, управляется из Django Admin |

**Key insight:** aiogram 3 Router + FSM + RedisStorage — достаточно для всего диалогового flow без кастомных middleware или хранилищ. Не усложнять.

---

## Common Pitfalls

### Pitfall 1: Порядок регистрации /start handlers

**What goes wrong:** `@router.message(CommandStart())` перехватывает `/start questionnaire_...` раньше чем `CommandStart(deep_link=True)` обработчик.

**Why it happens:** aiogram обрабатывает handlers в порядке регистрации. Plain `CommandStart()` матчится на любое `/start` сообщение включая те, что содержат payload.

**How to avoid:** Всегда регистрировать специализированный `CommandStart(deep_link=True)` ПЕРВЫМ через `dp.include_router(start_router)` и внутри start_router добавить deep_link handler первым.

**Warning signs:** Бот игнорирует payload и каждый `/start questionnaire_...` запускает онбординг заново.

### Pitfall 2: FSM state vs FSM data confusion

**What goes wrong:** Разработчик хранит всё в state (`set_state(some_value_not_a_State_class)`) вместо FSM data.

**Why it happens:** aiogram 2.x использовал другой API. В aiogram 3 `state` — это только `State()` объект из StatesGroup. Данные — через `state.update_data()`.

**How to avoid:** State = "где находится пользователь в диалоге". Data = "что он ответил". Правило: `state.set_state(OnboardingStates.waiting_name)`, `state.update_data(name=value)`.

### Pitfall 3: callback_data ≤64 байт ограничение

**What goes wrong:** `CallbackData` с длинными строковыми полями (UUID, длинные названия) превышает 64-байтный лимит Telegram.

**Why it happens:** Telegram API ограничивает callback_data в 64 байта. `CallbackData` с prefix="industry" + code="very_long_industry_code_here" может превысить лимит.

**How to avoid:** Держать prefix коротким (2-4 символа), value-поля — короткими slug (max 20 символов). `IndustryCallback(prefix="ind", code=industry.code)` где `code` — SlugField из Django (max 50, но использовать короткие). Проверять длину при разработке.

### Pitfall 4: Потеря FSM data при edit_reply_markup

**What goes wrong:** Бот редактирует сообщение с клавиатурой (multichoice toggle), но FSM data для предыдущего вопроса стирается.

**Why it happens:** `callback.message.edit_reply_markup()` не затрагивает FSM data, но если код случайно вызывает `state.clear()` или `state.set_state()` до завершения multichoice — данные теряются.

**How to avoid:** При multichoice toggle НЕ менять state, только `state.update_data(mc_selected=...)`. State меняется только при нажатии «Готово».

### Pitfall 5: JWT expiry во время длинной анкеты

**What goes wrong:** Пользователь начал анкету (27 вопросов), отвечает медленно. JWT (15 мин по умолчанию в SimpleJWT) истекает на середине анкеты. API начинает возвращать 401.

**Why it happens:** SimpleJWT access token имеет короткий TTL для безопасности.

**How to avoid:** Либо (a) увеличить `ACCESS_TOKEN_LIFETIME` в SimpleJWT settings до 2 часов для bot-issued tokens, либо (b) при 401 ответе автоматически запрашивать новый JWT через `/bot/jwt/` endpoint (бот имеет X-Bot-Token). Рекомендуем вариант (a): в Django settings для bot synthetic users увеличить TTL до 4 часов.

### Pitfall 6: Celery beat vs bot процесс для напоминаний

**What goes wrong:** Разработчик пытается отправить напоминание из aiogram bot процесса через `asyncio.sleep(86400)` или aiogram scheduler.

**Why it happens:** Кажется проще "внутри бота", чем отдельная Celery задача.

**How to avoid:** Celery beat — единственный правильный подход. Bot process может рестартоваться, async sleep не crash-safe. Celery beat в Django — persistent, управляется из Admin, логируется.

---

## Code Examples

### Полный flow онбординга (сводный)

```python
# bot/handlers/onboarding.py — ключевые части

@router.message(OnboardingStates.waiting_phone)
async def handle_phone(message: Message, state: FSMContext) -> None:
    import re
    phone = message.text.strip()
    if not re.match(r"^\+?[78]\d{10}$", phone):
        await message.answer(
            "Введите номер в формате +77001234567 или 87001234567:"
        )
        return
    await state.update_data(phone_wa=phone)
    await state.set_state(OnboardingStates.waiting_city)
    await message.answer("В каком городе находится ваша компания?")


@router.message(OnboardingStates.waiting_city)
async def handle_city(message: Message, state: FSMContext) -> None:
    city = message.text.strip()
    await state.update_data(city=city)

    data = await state.get_data()
    telegram_id = message.from_user.id

    try:
        await api_client.onboard(
            telegram_id=telegram_id,
            name=data["name"],
            company=data["company"],
            industry_code=data["industry_code"],
            phone_wa=data["phone_wa"],
            city=city,
        )
        token = await api_client.create_deeplink(telegram_id)
    except httpx.HTTPStatusError:
        await message.answer("Произошла ошибка. Попробуйте /start снова.")
        await state.clear()
        return

    site_url = f"https://baqsy.kz/auth/{token}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Выбрать тариф и оплатить ➡️", url=site_url)
    ]])
    await state.clear()
    await message.answer(
        "Отлично! Профиль создан.\n\n"
        "Теперь выберите тариф аудита на нашем сайте:",
        reply_markup=kb,
    )
```

### /status и /help

```python
# bot/handlers/commands.py
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

@router.message(Command("status"))
async def cmd_status(message: Message, state: FSMContext) -> None:
    telegram_id = message.from_user.id
    try:
        sub = await api_client.get_active_submission(telegram_id)
    except httpx.HTTPStatusError:
        await message.answer("Ошибка при получении статуса. Попробуйте позже.")
        return
    if not sub:
        await message.answer("У вас нет активных заказов.\n\nЧтобы начать — нажмите /start")
        return
    status_text = {
        "created": "Ожидает оплаты",
        "paid": "Оплачен, ожидает анкеты",
        "in_progress_full": "Анкета в процессе",
        "completed": "Анкета завершена, ожидает аудитора",
        "under_audit": "Аудит в процессе",
        "delivered": "Аудит доставлен",
    }.get(sub["status"], sub["status"])
    await message.answer(f"Статус вашего заказа: *{status_text}*", parse_mode="Markdown")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "*Baqsy — Бизнес-Аудит*\n\n"
        "/start — начать или продолжить\n"
        "/status — статус вашего заказа\n"
        "/help — эта справка\n\n"
        "По вопросам: @baqsy\\_support",
        parse_mode="Markdown",
    )
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `aioredis` для FSM | `redis` package напрямую | aiogram 3.0 (2022) | aioredis deprecated, redis>=5.0 обязателен |
| aiogram 2 `dp.register_message_handler(func, state=...)` | `@router.message(StateClass.state)` decorator | aiogram 3.0 | Декларативный стиль, Router изоляция |
| `CommandStart` без `deep_link` param | `CommandStart(deep_link=True)` + `decode_payload()` | aiogram 3.x | Встроенная поддержка deep links |
| `InlineKeyboardMarkup([[...]])` вручную | `InlineKeyboardBuilder` с `.adjust()` | aiogram 3.x | Меньше boilerplate |
| Глобальный `Dispatcher` | `Router` + `dp.include_router()` | aiogram 3.0 | Модульность, изолированные тесты |

**Deprecated/outdated:**
- `aioredis`: использовать `redis` (pip install redis)
- aiogram 2.x `@dp.message_handler`: другой API полностью, в aiogram 3 Router-based
- `MemoryStorage`: только для dev/тестов без Redis (данные теряются при рестарте)

---

## Open Questions

1. **Endpoint GET /api/v1/bot/active-submission/?telegram_id=**
   - What we know: Phase 2 реализовала SubmissionDetailView (GET /submissions/{id}/), но нет endpoint для поиска по telegram_id
   - What's unclear: Существует ли этот endpoint? Нужна проверка `backend/apps/submissions/urls.py` и `accounts/bot_urls.py`
   - Recommendation: Если нет — добавить как первую задачу Wave 0 (один маленький endpoint в submissions views)

2. **Endpoint POST /api/v1/bot/jwt/ для получения JWT по telegram_id**
   - What we know: Phase 2 реализовала JWT через DeeplinkExchangeView (обмен token → JWT). Но прямого endpoint "дай JWT по telegram_id через X-Bot-Token" может не быть
   - What's unclear: Как бот получает JWT при восстановлении сессии (BOT-10) когда deeplink token уже использован?
   - Recommendation: Проверить `accounts/bot_urls.py`. Если нет — добавить `POST /api/v1/bot/jwt/` в Wave 0: принимает `telegram_id` + X-Bot-Token, возвращает JWT access token

3. **last_reminded_at поле на Submission**
   - What we know: Поле нужно для BOT-11, в Phase 1 не создавалось
   - What's unclear: Нужна ли новая миграция Django
   - Recommendation: Добавить поле + миграцию в Wave 0 этой фазы

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.3 + pytest-asyncio ^0.23 |
| Config file | `backend/pyproject.toml` — `[tool.pytest.ini_options]` |
| Quick run command | `docker-compose exec web pytest apps/submissions/tests/test_api.py -x -q` |
| Full suite command | `docker-compose exec web pytest -x -q` |

**Bot-specific tests** живут в `bot/tests/` и запускаются через отдельный pytest в bot контейнере (или с `--rootdir=bot`).

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| BOT-01 | Bot starts, connects Redis FSM (db=1) | smoke | `docker-compose exec bot python main.py --test-startup` | ❌ Wave 0 |
| BOT-02 | /start triggers OnboardingStates.waiting_name | unit | `pytest bot/tests/test_start.py::test_start_new_user -x` | ❌ Wave 0 |
| BOT-03 | 5 onboarding questions complete with valid input | unit | `pytest bot/tests/test_onboarding.py::test_full_onboarding -x` | ❌ Wave 0 |
| BOT-04 | After onboarding deeplink is sent | unit | `pytest bot/tests/test_onboarding.py::test_deeplink_sent -x` | ❌ Wave 0 |
| BOT-05 | /start questionnaire_uuid starts questionnaire | unit | `pytest bot/tests/test_questionnaire.py::test_start_questionnaire -x` | ❌ Wave 0 |
| BOT-06 | Each answer immediately POSTs to API | unit | `pytest bot/tests/test_questionnaire.py::test_answer_posted_immediately -x` | ❌ Wave 0 |
| BOT-07 | Progress indicator shows N/M | unit | `pytest bot/tests/test_questionnaire.py::test_progress_indicator -x` | ❌ Wave 0 |
| BOT-08 | /status returns last submission status | unit | `pytest bot/tests/test_commands.py::test_status_command -x` | ❌ Wave 0 |
| BOT-09 | /help returns help text | unit | `pytest bot/tests/test_commands.py::test_help_command -x` | ❌ Wave 0 |
| BOT-10 | Resume after FSM data loss | unit | `pytest bot/tests/test_start.py::test_resume_after_fsm_loss -x` | ❌ Wave 0 |
| BOT-11 | Celery task finds 24h stale submissions | unit | `pytest apps/submissions/tests/test_tasks.py::test_remind_incomplete -x` | ❌ Wave 0 |

### Bot Testing Pattern (pytest-asyncio + mocked httpx)

```python
# bot/tests/test_onboarding.py
import pytest
from unittest.mock import AsyncMock, patch
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher

@pytest.fixture
def dp():
    storage = MemoryStorage()   # no Redis needed in tests
    dp = Dispatcher(storage=storage)
    from bot.handlers.onboarding import router
    dp.include_router(router)
    return dp

@pytest.mark.asyncio
async def test_handle_name_valid(dp):
    """Valid name advances state to waiting_company."""
    # Use aiogram test helpers or mock bot
    # Pattern: create fake message, call handler directly
    from aiogram.fsm.context import FSMContext
    from bot.states.onboarding import OnboardingStates

    storage = MemoryStorage()
    # ... test implementation with mocked message
```

**Рекомендуемый подход для bot тестов:** Тестировать `api_client` функции отдельно (mocking httpx responses через `pytest-mock`), тестировать FSM state transitions отдельно с MemoryStorage. Полную интеграцию бота (реальный Redis + реальный Django) — только в smoke тестах.

### Sampling Rate

- **Per task commit:** `docker-compose exec web pytest apps/submissions/tests/ -x -q` (backend tests)
- **Per wave merge:** `docker-compose exec web pytest -x -q` (full backend suite)
- **Phase gate:** Full backend suite + bot smoke test green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `bot/tests/__init__.py` + `bot/tests/test_start.py` — covers BOT-02, BOT-10
- [ ] `bot/tests/test_onboarding.py` — covers BOT-03, BOT-04
- [ ] `bot/tests/test_questionnaire.py` — covers BOT-05, BOT-06, BOT-07
- [ ] `bot/tests/test_commands.py` — covers BOT-08, BOT-09
- [ ] `backend/apps/submissions/tests/test_tasks.py` — covers BOT-11
- [ ] Bot dev deps: `cd bot && poetry add --group dev pytest pytest-asyncio pytest-mock`
- [ ] Django migration: `last_reminded_at` поле на Submission model
- [ ] Django endpoint: `POST /api/v1/bot/jwt/` (если нет в Phase 2)
- [ ] Django endpoint: `GET /api/v1/bot/active-submission/` (если нет в Phase 2)

---

## Sources

### Primary (HIGH confidence)
- [aiogram 3.27 FSM docs](https://docs.aiogram.dev/en/latest/dispatcher/finite_state_machine/index.html) — StatesGroup, State, FSMContext, RedisStorage
- [aiogram 3.27 Deep Linking docs](https://docs.aiogram.dev/en/latest/utils/deep_linking.html) — CommandStart(deep_link=True), decode_payload()
- [aiogram 3.27 Callback Data docs](https://docs.aiogram.dev/en/latest/dispatcher/filters/callback_data.html) — CallbackData factory, prefix, filter()
- [aiogram 3.27 Keyboard builder docs](https://docs.aiogram.dev/en/latest/utils/keyboard.html) — InlineKeyboardBuilder, adjust()
- STACK.md (this project) — aiogram 3.27, httpx 0.27, redis 5.3 версии подтверждены PyPI
- ARCHITECTURE.md (this project) — Bot thin client invariant, Celery→Telegram direct HTTP pattern
- `bot/pyproject.toml` — installed deps: aiogram 3.27.0, httpx 0.27.0, redis 5.3.0
- `bot/Dockerfile` — multi-stage build ready
- `backend/apps/accounts/views.py` — OnboardingView, DeeplinkCreateView реализованы
- `backend/apps/submissions/views.py` — все 5 submission endpoints реализованы

### Secondary (MEDIUM confidence)
- [aiogram-tests PyPI](https://pypi.org/project/aiogram-tests/) — testing pattern for aiogram 3 handlers
- [aiogram FSM guide (Groosha)](https://mastergroosha.github.io/aiogram-3-guide/fsm/) — verified FSM patterns
- Celery 5.6.3 docs — periodic tasks, beat schedule, bind=True retry pattern

### Tertiary (LOW confidence)
- Community patterns for multichoice toggle in aiogram 3 — extrapolated from InlineKeyboardBuilder docs

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — все версии верифицированы в pyproject.toml, официальные docs
- Architecture: HIGH — паттерны из ARCHITECTURE.md и официальной документации aiogram 3
- Pitfalls: HIGH — документированные ограничения Telegram API (64 байт) и aiogram 3 migration notes
- Bot testing: MEDIUM — aiogram-tests библиотека существует, паттерны extrapolated из docs

**Research date:** 2026-04-16
**Valid until:** 2026-07-16 (aiogram minor releases frequent, но 3.x API stable)
