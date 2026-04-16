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
        f"Спасибо, {data['name']}! Профиль создан.\n\n"
        f"Компания: {data['company']}\n"
        f"WhatsApp: {data.get('phone_wa', '—')}\n"
        f"Город: {city}\n\n"
        "Для продолжения выберите тариф на нашем сайте:",
        reply_markup=kb,
    )
    await state.clear()
