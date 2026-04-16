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
