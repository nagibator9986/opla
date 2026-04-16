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
        f"Статус вашего заказа:\n\n"
        f"Статус: {st}\n"
        f"Прогресс анкеты: {progress}\n"
        f"Создан: {active.get('created_at', '?')[:10]}"
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Baqsy System — платформа бизнес-аудита\n\n"
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
