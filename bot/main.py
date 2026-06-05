import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

from bot.config import settings
from bot.db.engine import create_tables, get_session_factory, init_engine
from bot.handlers import demo, operator, register, start, support
from bot.middlewares.events import EventsMiddleware
from bot.web import create_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    init_engine(settings.DATABASE_URL)
    await create_tables()

    session_factory = get_session_factory()

    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.update.middleware(EventsMiddleware(session_factory))

    dp.include_router(operator.router)  # must be first — intercepts admin chat
    dp.include_router(start.router)
    dp.include_router(demo.router)
    dp.include_router(register.router)
    dp.include_router(support.router)

    app = create_app(bot, session_factory)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, settings.BOT_WEBHOOK_HOST, settings.BOT_WEBHOOK_PORT)
    await site.start()
    logger.info(
        "Webhook server listening on %s:%s",
        settings.BOT_WEBHOOK_HOST,
        settings.BOT_WEBHOOK_PORT,
    )

    logger.info("Starting Grammerce bot (long polling)...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
