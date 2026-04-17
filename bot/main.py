import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import settings
from bot.db.engine import create_tables, get_session_factory, init_engine
from bot.handlers import demo, register, start, support
from bot.middlewares.events import EventsMiddleware

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

    dp.include_router(start.router)
    dp.include_router(demo.router)
    dp.include_router(register.router)
    dp.include_router(support.router)

    logger.info("Starting Grammerce bot (long polling)...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
