import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import MenuButtonWebApp, WebAppInfo
from aiohttp import web

from bot.config import settings
from bot.db.engine import create_tables, get_session_factory, init_engine
from bot.handlers import admin, demo, operator, register, research, start, support
from bot.middlewares.events import EventsMiddleware
from bot.services.push_scheduler import scheduler_loop
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

    # Optional persistent menu button (left of the input field) → WebApp "Кабинет".
    # Only when PLATFORM_WEBAPP_URL is configured; wrapped so a bad value can't
    # crash startup. The create-shop flow does NOT depend on this.
    if settings.PLATFORM_WEBAPP_URL:
        try:
            await bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(
                    text="Кабинет",
                    web_app=WebAppInfo(url=settings.PLATFORM_WEBAPP_URL),
                )
            )
        except Exception:
            logger.error("Failed to set WebApp menu button", exc_info=True)

    dp = Dispatcher(storage=MemoryStorage())

    dp.update.middleware(EventsMiddleware(session_factory))

    dp.include_router(admin.router)      # before operator — broadcast owns admin chat while composing
    dp.include_router(operator.router)   # intercepts admin chat outside broadcast
    dp.include_router(research.router)   # before start — handles web_app_data early
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

    # Hourly activation-push scheduler (in-process).
    scheduler_task = asyncio.create_task(scheduler_loop(bot, session_factory))

    logger.info("Starting Grammerce bot (long polling)...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler_task.cancel()
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
