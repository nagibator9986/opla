from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from bot.services import api_client
from bot.states.questionnaire import QuestionnaireStates
from bot.handlers.start import _send_next_question

router = Router()


@router.message(QuestionnaireStates.answering)
async def process_text_answer(message: Message, state: FSMContext):
    """Handle free-text or number input for current question."""
    data = await state.get_data()
    submission_id = data["submission_id"]
    jwt_token = data["jwt_token"]
    question_id = data["current_question_id"]
    field_type = data["current_field_type"]

    text = message.text.strip()

    if field_type == "number":
        try:
            num = float(text) if "." in text else int(text)
            value = {"number": num}
        except ValueError:
            await message.answer("Пожалуйста, введите число:")
            return
    else:
        value = {"text": text}

    try:
        await api_client.save_answer(submission_id, question_id, value, jwt_token)
    except Exception:
        await message.answer("Ошибка при сохранении ответа. Попробуйте ещё раз.")
        return

    await _send_next_question(message, state)


@router.callback_query(QuestionnaireStates.answering, F.data.startswith("choice:"))
async def process_choice_answer(callback: CallbackQuery, state: FSMContext):
    """Handle single-choice inline button."""
    choice = callback.data.split(":", 1)[1]
    data = await state.get_data()

    try:
        await api_client.save_answer(
            data["submission_id"],
            data["current_question_id"],
            {"choice": choice},
            data["jwt_token"],
        )
    except Exception:
        await callback.answer("Ошибка, попробуйте ещё раз")
        return

    await callback.answer()
    await _send_next_question(callback.message, state)


@router.callback_query(QuestionnaireStates.multichoice_selecting, F.data.startswith("mc:"))
async def process_multichoice_toggle(callback: CallbackQuery, state: FSMContext):
    """Toggle multichoice selection or submit on 'done'."""
    value = callback.data.split(":", 1)[1]
    data = await state.get_data()

    if value == "done":
        selected = data.get("mc_selected", [])
        if not selected:
            await callback.answer("Выберите хотя бы один вариант")
            return

        try:
            await api_client.save_answer(
                data["submission_id"],
                data["current_question_id"],
                {"choices": selected},
                data["jwt_token"],
            )
        except Exception:
            await callback.answer("Ошибка, попробуйте ещё раз")
            return

        await callback.answer()
        await state.set_state(QuestionnaireStates.answering)
        await _send_next_question(callback.message, state)
        return

    # Toggle selection
    selected = list(data.get("mc_selected", []))
    if value in selected:
        selected.remove(value)
    else:
        selected.append(value)
    await state.update_data(mc_selected=selected)

    # Update keyboard to show selection state with checkmark indicators
    options = data.get("current_options", {}).get("choices", [])
    kb = InlineKeyboardMarkup(inline_keyboard=[
        *[[InlineKeyboardButton(
            text=f"{'✅' if c in selected else '☐'} {c}",
            callback_data=f"mc:{c}"
        )] for c in options],
        [InlineKeyboardButton(text=f"✅ Готово ({len(selected)})", callback_data="mc:done")],
    ])
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()
