"""Questionnaire FSM handler — stub for Plan 01.

Full implementation arrives in Plan 02 (bot-questionnaire-fsm).
"""
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.states.questionnaire import QuestionnaireStates
from bot.services import api_client
from bot.handlers.start import _send_next_question

router = Router()


@router.message(QuestionnaireStates.answering)
async def handle_text_answer(message: Message, state: FSMContext):
    """Handle free-text / number answer for the current question."""
    data = await state.get_data()
    submission_id = data.get("submission_id")
    jwt_token = data.get("jwt_token")
    question_id = data.get("current_question_id")
    field_type = data.get("current_field_type", "text")

    value = message.text.strip()

    if field_type == "number":
        try:
            value = str(float(value))
        except ValueError:
            await message.answer("Пожалуйста, введите число:")
            return

    await api_client.save_answer(submission_id, question_id, value, jwt_token)
    await _send_next_question(message, state)


@router.callback_query(QuestionnaireStates.answering, F.data.startswith("choice:"))
async def handle_choice_answer(callback: CallbackQuery, state: FSMContext):
    """Handle single-choice answer (inline button)."""
    data = await state.get_data()
    value = callback.data.split(":", 1)[1]

    await api_client.save_answer(
        data["submission_id"], data["current_question_id"], value, data["jwt_token"]
    )
    await callback.answer()
    await _send_next_question(callback.message, state)


@router.callback_query(QuestionnaireStates.multichoice_selecting, F.data.startswith("mc:"))
async def handle_multichoice_toggle(callback: CallbackQuery, state: FSMContext):
    """Toggle multichoice option or submit when 'done'."""
    choice = callback.data.split(":", 1)[1]
    data = await state.get_data()
    selected: list = list(data.get("mc_selected", []))

    if choice == "done":
        if not selected:
            await callback.answer("Выберите хотя бы один вариант")
            return
        await api_client.save_answer(
            data["submission_id"], data["current_question_id"], selected, data["jwt_token"]
        )
        await callback.answer()
        await state.set_state(QuestionnaireStates.answering)
        await _send_next_question(callback.message, state)
        return

    # Toggle selection
    if choice in selected:
        selected.remove(choice)
    else:
        selected.append(choice)
    await state.update_data(mc_selected=selected)

    # Rebuild keyboard with updated selection indicators
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    choices = data.get("current_options", {}).get("choices", [])
    kb = InlineKeyboardMarkup(inline_keyboard=[
        *[
            [InlineKeyboardButton(
                text=f"+ {c}" if c in selected else f"-- {c}",
                callback_data=f"mc:{c}",
            )]
            for c in choices
        ],
        [InlineKeyboardButton(text="Готово", callback_data="mc:done")],
    ])
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()
