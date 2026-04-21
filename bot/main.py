"""Baqsy Telegram Bot — aiogram 3 with FSM + Django REST API client."""
import asyncio
import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import TelegramObject

from bot.config import BOT_TOKEN, REDIS_URL
from bot.services.api_client import APIError, close_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("baqsy.bot")


class ErrorGuardMiddleware(BaseMiddleware):
    """Catch unhandled exceptions so a single bad request never kills the poller.

    APIError has a user-safe message; anything else gets logged and replaced
    with a generic notice so clients never see a stack trace.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except APIError as e:
            await self._notify(event, str(e))
        except Exception:
            log.exception("Unhandled exception in handler")
            await self._notify(event, "Произошла ошибка, попробуйте позже.")

    @staticmethod
    async def _notify(event: TelegramObject, text: str) -> None:
        try:
            if hasattr(event, "answer"):
                await event.answer(text)
            elif hasattr(event, "message") and event.message:  # CallbackQuery
                await event.message.answer(text)
        except Exception:
            log.debug("Failed to notify user about error", exc_info=True)


class RequestLogMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user_id = getattr(getattr(event, "from_user", None), "id", None)
        text = getattr(event, "text", None) or getattr(event, "data", None)
        log.info("event user=%s payload=%r", user_id, text)
        return await handler(event, data)


async def main():
    # state_ttl=1h so an abandoned FSM doesn't keep a user stuck after /start
    storage = RedisStorage.from_url(REDIS_URL, state_ttl=3600, data_ttl=604800)
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=storage)

    dp.message.middleware(RequestLogMiddleware())
    dp.callback_query.middleware(RequestLogMiddleware())
    dp.message.middleware(ErrorGuardMiddleware())
    dp.callback_query.middleware(ErrorGuardMiddleware())

    # Import and include routers (order matters: deep_link before plain CommandStart)
    from bot.handlers.commands import router as commands_router
    from bot.handlers.onboarding import router as onboarding_router
    from bot.handlers.questionnaire import router as questionnaire_router
    from bot.handlers.start import router as start_router

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
