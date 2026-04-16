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
        "Добро пожаловать в Baqsy System!\n\n"
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
        await api_client.complete_submission(submission_id, jwt_token)
        await message.answer(
            "Спасибо! Ваша анкета передана аудитору.\n\n"
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
    text = f"Вопрос {progress}\n\n{question['text']}"

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
            *[[InlineKeyboardButton(text=f"-- {c}", callback_data=f"mc:{c}")] for c in choices],
            [InlineKeyboardButton(text="Готово", callback_data="mc:done")],
        ])
        await state.update_data(mc_selected=[])
        await state.set_state(QuestionnaireStates.multichoice_selecting)
        await message.answer(text + "\n\n(Выберите все подходящие варианты)", reply_markup=kb)
    else:
        # text or number — free input
        hint = "Введите число:" if ft == "number" else ""
        await message.answer(text + (f"\n\n{hint}" if hint else ""))
