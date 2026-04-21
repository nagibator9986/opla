from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.services import api_client

router = Router()


@router.message(Command("status"))
async def cmd_status(message: Message):
    active = await api_client.get_active_submission(message.from_user.id)
    if not active:
        await message.answer(
            "У вас нет активных заказов.\n"
            "Отправьте /start, чтобы выбрать тариф."
        )
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
        f"<b>Статус вашего заказа</b>\n\n"
        f"Статус: {st}\n"
        f"Прогресс анкеты: {progress}\n"
        f"Создан: {active.get('created_at', '?')[:10]}"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "<b>Baqsy System</b> — платформа бизнес-аудита\n\n"
        "<b>Команды:</b>\n"
        "/start — начать работу или продолжить\n"
        "/status — узнать статус заказа\n"
        "/reset — удалить профиль и начать заново\n"
        "/help — эта справка\n\n"
        "<b>Как это работает:</b>\n"
        "1. Ответьте на 5 вопросов о компании\n"
        "2. Выберите тариф и оплатите на сайте\n"
        "3. Пройдите анкету из 27 вопросов\n"
        "4. Получите персональный PDF-аудит"
    )


@router.message(Command("reset"))
async def cmd_reset(message: Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да, удалить профиль", callback_data="reset:confirm"),
                InlineKeyboardButton(text="Отмена", callback_data="reset:cancel"),
            ],
        ]
    )
    await message.answer(
        "Удалить ваш профиль и все данные?\n"
        "Вместе с ним будут удалены незавершённые заказы.\n"
        "Это действие необратимо.",
        reply_markup=kb,
    )


@router.callback_query(F.data == "reset:cancel")
async def reset_cancel(callback: CallbackQuery):
    await callback.answer("Отменено")
    await callback.message.edit_text("Сброс отменён. Профиль сохранён.")


@router.callback_query(F.data == "reset:confirm")
async def reset_confirm(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await api_client.reset_profile(callback.from_user.id)
    await callback.answer("Профиль удалён")
    await callback.message.edit_text(
        "Профиль удалён. Отправьте /start, чтобы начать заново."
    )


# Fallback: any text that no other handler picked up (no FSM state, no command).
# Must be the LAST handler registered in the LAST router — aiogram dispatches in
# router-include order, so this won't shadow FSM/onboarding/questionnaire states.
@router.message(F.text)
async def fallback_text(message: Message):
    await message.answer(
        "Не понял команду. Напишите:\n"
        "/start — начать или продолжить\n"
        "/status — статус заказа\n"
        "/help — подробности"
    )
