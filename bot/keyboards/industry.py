from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def build_industry_keyboard(industries: list[dict]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=ind["name"], callback_data=f"industry:{ind['code']}")]
        for ind in industries
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
