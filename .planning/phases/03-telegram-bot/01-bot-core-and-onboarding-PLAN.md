---
phase: 03-telegram-bot
plan: 01
type: execute
wave: 1
title: "Bot core setup + onboarding FSM flow"
depends_on: [00]
requirements: [BOT-01, BOT-02, BOT-03, BOT-04, BOT-08, BOT-09]
autonomous: true
files_modified:
  - bot/main.py
  - bot/config.py
  - bot/services/__init__.py
  - bot/services/api_client.py
  - bot/states/__init__.py
  - bot/states/onboarding.py
  - bot/states/questionnaire.py
  - bot/handlers/__init__.py
  - bot/handlers/start.py
  - bot/handlers/onboarding.py
  - bot/handlers/commands.py
  - bot/keyboards/__init__.py
  - bot/keyboards/industry.py
nyquist_compliant: true
---

# Plan 01: Bot Core + Onboarding FSM

## Goal

Replace bot skeleton with full aiogram 3 setup: Bot + Dispatcher + RedisStorage + Router. Implement onboarding FSM (5 questions), /start command with new/returning user detection, /status and /help commands, deep-link generation after onboarding.

## must_haves

- Bot starts via aiogram long-polling with RedisStorage(db=1)
- `/start` detects new vs returning user
- Onboarding asks 5 questions: name, company, industry (inline KB), phone, city
- After onboarding: calls POST /bot/onboarding/ + POST /bot/deeplink/ → sends URL button
- `/status` shows submission status
- `/help` shows help text
- All handlers use api_client to call Django REST API

## Tasks

<task id="01-01">
<title>Create bot config, API client, and FSM states</title>
<read_first>
- bot/pyproject.toml (installed deps)
- .planning/phases/03-telegram-bot/03-CONTEXT.md (API client decisions)
- .planning/phases/03-telegram-bot/03-RESEARCH.md (httpx patterns, FSM states)
</read_first>
<action>
Create `bot/config.py`:
```python
from decouple import config

BOT_TOKEN = config("TELEGRAM_BOT_TOKEN")
API_BASE_URL = config("API_BASE_URL", default="http://web:8000/api/v1")
BOT_API_SECRET = config("BOT_API_SECRET", default="dev-bot-secret")
REDIS_URL = config("AIOGRAM_REDIS_URL", default="redis://redis:6379/1")
SITE_URL = config("SITE_URL", default="https://baqsy.kz")
```

Create `bot/services/__init__.py` (empty).

Create `bot/services/api_client.py`:
```python
import httpx
import logging
from bot.config import API_BASE_URL, BOT_API_SECRET

log = logging.getLogger(__name__)

_client: httpx.AsyncClient | None = None

def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=API_BASE_URL,
            timeout=30.0,
            headers={"X-Bot-Token": BOT_API_SECRET},
        )
    return _client

async def close_client():
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()
        _client = None

# Bot-authenticated endpoints (X-Bot-Token)

async def onboard(telegram_id, name, company, industry_code="", phone_wa="", city=""):
    r = await get_client().post("/bot/onboarding/", json={
        "telegram_id": telegram_id, "name": name, "company": company,
        "industry_code": industry_code, "phone_wa": phone_wa, "city": city,
    })
    r.raise_for_status()
    return r.json()

async def create_deeplink(telegram_id):
    r = await get_client().post("/bot/deeplink/", json={"telegram_id": telegram_id})
    r.raise_for_status()
    return r.json()

async def get_industries():
    r = await get_client().get("/industries/")
    r.raise_for_status()
    return r.json()["results"]

async def get_jwt(telegram_id):
    r = await get_client().post("/bot/jwt/", json={"telegram_id": telegram_id})
    r.raise_for_status()
    return r.json()

async def get_active_submission(telegram_id):
    r = await get_client().get("/bot/active-submission/", params={"telegram_id": telegram_id})
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()

# JWT-authenticated endpoints (for submission operations)

async def _jwt_client(jwt_token):
    return httpx.AsyncClient(
        base_url=API_BASE_URL,
        timeout=30.0,
        headers={"Authorization": f"Bearer {jwt_token}"},
    )

async def get_next_question(submission_id, jwt_token):
    async with await _jwt_client(jwt_token) as c:
        r = await c.get(f"/submissions/{submission_id}/next-question/")
        if r.status_code == 204:
            return None
        r.raise_for_status()
        return r.json()

async def save_answer(submission_id, question_id, value, jwt_token):
    async with await _jwt_client(jwt_token) as c:
        r = await c.post(f"/submissions/{submission_id}/answers/", json={
            "question_id": question_id, "value": value,
        })
        r.raise_for_status()
        return r.json()

async def complete_submission(submission_id, jwt_token):
    async with await _jwt_client(jwt_token) as c:
        r = await c.post(f"/submissions/{submission_id}/complete/")
        r.raise_for_status()
        return r.json()

async def get_submission_status(submission_id, jwt_token):
    async with await _jwt_client(jwt_token) as c:
        r = await c.get(f"/submissions/{submission_id}/")
        r.raise_for_status()
        return r.json()
```

Create `bot/states/__init__.py` (empty).

Create `bot/states/onboarding.py`:
```python
from aiogram.fsm.state import State, StatesGroup

class OnboardingStates(StatesGroup):
    waiting_name = State()
    waiting_company = State()
    waiting_industry = State()
    waiting_phone = State()
    waiting_city = State()
```

Create `bot/states/questionnaire.py`:
```python
from aiogram.fsm.state import State, StatesGroup

class QuestionnaireStates(StatesGroup):
    answering = State()
    multichoice_selecting = State()
```

Create `bot/keyboards/__init__.py` (empty).

Create `bot/keyboards/industry.py`:
```python
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def build_industry_keyboard(industries: list[dict]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=ind["name"], callback_data=f"industry:{ind['code']}")]
        for ind in industries
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
```
</action>
<acceptance_criteria>
- `bot/config.py` contains `BOT_TOKEN = config("TELEGRAM_BOT_TOKEN")`
- `bot/services/api_client.py` contains `async def onboard(`
- `bot/services/api_client.py` contains `async def create_deeplink(`
- `bot/services/api_client.py` contains `async def get_next_question(`
- `bot/states/onboarding.py` contains `class OnboardingStates(StatesGroup):`
- `bot/states/questionnaire.py` contains `class QuestionnaireStates(StatesGroup):`
- `bot/keyboards/industry.py` contains `def build_industry_keyboard(`
</acceptance_criteria>
</task>

<task id="01-02">
<title>Create /start handler + onboarding FSM flow</title>
<read_first>
- bot/services/api_client.py
- bot/states/onboarding.py
- bot/keyboards/industry.py
- .planning/phases/03-telegram-bot/03-CONTEXT.md (onboarding 5 questions)
- .planning/phases/03-telegram-bot/03-RESEARCH.md (CommandStart deep_link pattern)
</read_first>
<action>
Create `bot/handlers/__init__.py` (empty).

Create `bot/handlers/start.py`:
```python
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.services import api_client
from bot.states.onboarding import OnboardingStates
from bot.states.questionnaire import QuestionnaireStates
from bot.config import SITE_URL

router = Router()

@router.message(CommandStart(deep_link=True))
async def start_with_payload(message: Message, state: FSMContext):
    """Handle /start with deep-link payload (e.g., questionnaire_<uuid>)."""
    payload = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
    
    if payload.startswith("questionnaire_"):
        submission_id = payload.replace("questionnaire_", "")
        jwt_data = await api_client.get_jwt(message.from_user.id)
        await state.update_data(
            submission_id=submission_id,
            jwt_token=jwt_data["access"],
        )
        await state.set_state(QuestionnaireStates.answering)
        await _send_next_question(message, state)
        return

    # Unknown payload — treat as regular start
    await start_regular(message, state)


@router.message(CommandStart())
async def start_regular(message: Message, state: FSMContext):
    """Handle plain /start — new or returning user."""
    await state.clear()
    telegram_id = message.from_user.id
    
    # Check for active submission
    active = await api_client.get_active_submission(telegram_id)
    if active:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Продолжить анкету", callback_data="resume_questionnaire")],
            [InlineKeyboardButton(text="Начать сначала", callback_data="start_fresh")],
        ])
        await message.answer(
            f"С возвращением! У вас есть незавершённая анкета.\n"
            f"Прогресс: {active.get('answered_count', 0)}/{active.get('total_questions', '?')}",
            reply_markup=kb,
        )
        await state.update_data(active_submission=active)
        return
    
    # Check if profile exists (returning user without active submission)
    try:
        jwt_data = await api_client.get_jwt(telegram_id)
        # Has profile — offer site link
        deeplink = await api_client.create_deeplink(telegram_id)
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Выбрать тариф", url=f"{SITE_URL}/auth/{deeplink['token']}")],
        ])
        await message.answer(
            "Добро пожаловать в Baqsy System!\n\n"
            "Для нового аудита выберите тариф на сайте:",
            reply_markup=kb,
        )
        return
    except Exception:
        pass
    
    # New user — start onboarding
    await message.answer(
        "Добро пожаловать в Baqsy System! 🎯\n\n"
        "Я помогу вам пройти бизнес-аудит.\n"
        "Давайте начнём с нескольких вопросов о вашей компании.\n\n"
        "Как вас зовут?"
    )
    await state.set_state(OnboardingStates.waiting_name)


@router.callback_query(F.data == "resume_questionnaire")
async def resume_questionnaire(callback, state: FSMContext):
    data = await state.get_data()
    active = data.get("active_submission")
    if not active:
        await callback.answer("Сессия истекла, напишите /start")
        return
    
    jwt_data = await api_client.get_jwt(callback.from_user.id)
    await state.update_data(
        submission_id=str(active["id"]),
        jwt_token=jwt_data["access"],
    )
    await state.set_state(QuestionnaireStates.answering)
    await callback.answer()
    await _send_next_question(callback.message, state)


async def _send_next_question(message, state: FSMContext):
    """Fetch and send next question from Django API."""
    data = await state.get_data()
    submission_id = data["submission_id"]
    jwt_token = data["jwt_token"]
    
    question = await api_client.get_next_question(submission_id, jwt_token)
    if question is None:
        # All answered — complete
        result = await api_client.complete_submission(submission_id, jwt_token)
        await message.answer(
            "Спасибо! Ваша анкета передана аудитору. 🎉\n\n"
            "Мы уведомим вас, когда результат будет готов.\n"
            "Используйте /status чтобы проверить статус."
        )
        await state.clear()
        return
    
    await state.update_data(
        current_question_id=question["id"],
        current_field_type=question["field_type"],
        current_options=question.get("options", {}),
    )
    
    progress = question.get("progress", "")
    text = f"📋 Вопрос {progress}\n\n{question['text']}"
    
    ft = question["field_type"]
    if ft == "choice":
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        choices = question["options"].get("choices", [])
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=c, callback_data=f"choice:{c}")]
            for c in choices
        ])
        await message.answer(text, reply_markup=kb)
    elif ft == "multichoice":
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        choices = question["options"].get("choices", [])
        kb = InlineKeyboardMarkup(inline_keyboard=[
            *[[InlineKeyboardButton(text=f"☐ {c}", callback_data=f"mc:{c}")] for c in choices],
            [InlineKeyboardButton(text="✅ Готово", callback_data="mc:done")],
        ])
        await state.update_data(mc_selected=[])
        await state.set_state(QuestionnaireStates.multichoice_selecting)
        await message.answer(text + "\n\n(Выберите все подходящие варианты)", reply_markup=kb)
    else:
        # text or number — free input
        hint = "Введите число:" if ft == "number" else ""
        await message.answer(text + (f"\n\n{hint}" if hint else ""))
```

Create `bot/handlers/onboarding.py`:
```python
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.services import api_client
from bot.states.onboarding import OnboardingStates
from bot.keyboards.industry import build_industry_keyboard
from bot.config import SITE_URL

router = Router()

@router.message(OnboardingStates.waiting_name)
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("Пожалуйста, введите ваше имя (минимум 2 символа):")
        return
    await state.update_data(name=name)
    await message.answer(f"Отлично, {name}! Как называется ваша компания?")
    await state.set_state(OnboardingStates.waiting_company)

@router.message(OnboardingStates.waiting_company)
async def process_company(message: Message, state: FSMContext):
    company = message.text.strip()
    if len(company) < 2:
        await message.answer("Введите название компании (минимум 2 символа):")
        return
    await state.update_data(company=company)
    
    industries = await api_client.get_industries()
    kb = build_industry_keyboard(industries)
    await message.answer("В какой отрасли работает ваша компания?", reply_markup=kb)
    await state.set_state(OnboardingStates.waiting_industry)

@router.callback_query(OnboardingStates.waiting_industry, F.data.startswith("industry:"))
async def process_industry(callback: CallbackQuery, state: FSMContext):
    industry_code = callback.data.split(":", 1)[1]
    await state.update_data(industry_code=industry_code)
    await callback.answer()
    await callback.message.answer(
        "Укажите ваш номер WhatsApp для получения результатов\n"
        "(формат: +7XXXXXXXXXX):"
    )
    await state.set_state(OnboardingStates.waiting_phone)

@router.message(OnboardingStates.waiting_phone)
async def process_phone(message: Message, state: FSMContext):
    import re
    phone = message.text.strip()
    if not re.match(r"^[\+]?[78]\d{10}$", phone.replace(" ", "").replace("-", "")):
        await message.answer("Введите номер в формате +7XXXXXXXXXX или 8XXXXXXXXXX:")
        return
    await state.update_data(phone_wa=phone)
    await message.answer("В каком городе вы находитесь?")
    await state.set_state(OnboardingStates.waiting_city)

@router.message(OnboardingStates.waiting_city)
async def process_city(message: Message, state: FSMContext):
    city = message.text.strip()
    await state.update_data(city=city)
    data = await state.get_data()
    
    # Call Django API
    await api_client.onboard(
        telegram_id=message.from_user.id,
        name=data["name"],
        company=data["company"],
        industry_code=data.get("industry_code", ""),
        phone_wa=data.get("phone_wa", ""),
        city=city,
    )
    
    # Create deep-link for site
    deeplink = await api_client.create_deeplink(message.from_user.id)
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Выбрать тариф и оплатить", url=f"{SITE_URL}/auth/{deeplink['token']}")],
    ])
    
    await message.answer(
        f"Спасибо, {data['name']}! Профиль создан. 🎉\n\n"
        f"Компания: {data['company']}\n"
        f"WhatsApp: {data.get('phone_wa', '—')}\n"
        f"Город: {city}\n\n"
        "Для продолжения выберите тариф на нашем сайте:",
        reply_markup=kb,
    )
    await state.clear()
```

Create `bot/handlers/commands.py`:
```python
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.services import api_client

router = Router()

@router.message(Command("status"))
async def cmd_status(message: Message):
    active = await api_client.get_active_submission(message.from_user.id)
    if not active:
        await message.answer("У вас нет активных заказов.")
        return
    
    status_map = {
        "created": "Создан",
        "in_progress_basic": "Онбординг",
        "paid": "Оплачен",
        "in_progress_full": "Заполнение анкеты",
        "completed": "Анкета завершена",
        "under_audit": "На аудите",
        "delivered": "Доставлен",
    }
    st = status_map.get(active["status"], active["status"])
    progress = f"{active.get('answered_count', 0)}/{active.get('total_questions', '?')}"
    
    await message.answer(
        f"📊 Статус вашего заказа:\n\n"
        f"Статус: {st}\n"
        f"Прогресс анкеты: {progress}\n"
        f"Создан: {active.get('created_at', '?')[:10]}"
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "ℹ️ Baqsy System — платформа бизнес-аудита\n\n"
        "Команды:\n"
        "/start — начать работу или продолжить\n"
        "/status — узнать статус заказа\n"
        "/help — эта справка\n\n"
        "Как это работает:\n"
        "1. Ответьте на 5 вопросов о компании\n"
        "2. Выберите тариф и оплатите на сайте\n"
        "3. Пройдите анкету из 27 вопросов\n"
        "4. Получите персональный PDF-аудит\n\n"
        "Вопросы? Свяжитесь с нами: @baqsy_support"
    )
```
</action>
<acceptance_criteria>
- `bot/handlers/start.py` contains `@router.message(CommandStart(deep_link=True))`
- `bot/handlers/start.py` contains `async def start_regular(`
- `bot/handlers/start.py` contains `async def _send_next_question(`
- `bot/handlers/onboarding.py` contains `class.*OnboardingStates.waiting_name`
- `bot/handlers/onboarding.py` contains `build_industry_keyboard`
- `bot/handlers/commands.py` contains `Command("status")`
- `bot/handlers/commands.py` contains `Command("help")`
</acceptance_criteria>
</task>

<task id="01-03">
<title>Create bot main.py with Dispatcher + Router setup</title>
<read_first>
- bot/main.py (current skeleton — replace entirely)
- bot/handlers/start.py
- bot/handlers/onboarding.py
- bot/handlers/commands.py
- bot/config.py
</read_first>
<action>
Replace `bot/main.py` entirely:

```python
"""Baqsy Telegram Bot — aiogram 3 with FSM + Django REST API client."""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from bot.config import BOT_TOKEN, REDIS_URL
from bot.services.api_client import close_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("baqsy.bot")


async def main():
    storage = RedisStorage.from_url(REDIS_URL, state_ttl=86400, data_ttl=604800)
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=storage)

    # Import and include routers (order matters: deep_link before plain CommandStart)
    from bot.handlers.start import router as start_router
    from bot.handlers.onboarding import router as onboarding_router
    from bot.handlers.commands import router as commands_router
    from bot.handlers.questionnaire import router as questionnaire_router

    dp.include_router(start_router)
    dp.include_router(onboarding_router)
    dp.include_router(questionnaire_router)
    dp.include_router(commands_router)

    log.info("Baqsy bot starting (long-polling)...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await close_client()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
```
</action>
<acceptance_criteria>
- `bot/main.py` contains `RedisStorage.from_url(REDIS_URL`
- `bot/main.py` contains `dp.include_router(start_router)`
- `bot/main.py` contains `dp.include_router(onboarding_router)`
- `bot/main.py` contains `dp.include_router(questionnaire_router)`
- `bot/main.py` contains `dp.start_polling(bot`
</acceptance_criteria>
</task>

## Verification

```bash
python -c "from bot.handlers.start import router"      # import succeeds
python -c "from bot.handlers.onboarding import router"  # import succeeds
python -c "from bot.services.api_client import onboard" # import succeeds
```
