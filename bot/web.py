import logging

from aiogram import Bot
from aiohttp import web
from sqlalchemy.ext.asyncio import async_sessionmaker

from bot.config import settings
from bot.db import crud
from bot.locales import t

logger = logging.getLogger(__name__)


def _format_name(data: dict, fallback: str) -> str:
    parts = [data.get("first_name"), data.get("last_name")]
    name = " ".join(p for p in parts if p)
    return name or fallback


def _format_utm(user) -> str:
    bits = [user.utm_source, user.utm_campaign]
    utm = " / ".join(b for b in bits if b)
    return utm or t("ru", "admin_utm_unknown")


def create_app(bot: Bot, session_factory: async_sessionmaker) -> web.Application:
    """aiohttp app exposing platform → bot lifecycle callbacks."""

    async def user_registered(request: web.Request) -> web.Response:
        if request.headers.get("X-Bot-Secret") != settings.PLATFORM_BOT_SHARED_SECRET:
            logger.warning("user-registered: bad or missing X-Bot-Secret")
            return web.json_response({"error": "bad secret"}, status=401)

        try:
            data = await request.json()
        except Exception:
            return web.json_response({"error": "bad payload"}, status=400)

        telegram_id = data.get("telegram_id")
        if telegram_id is None:
            return web.json_response({"error": "bad payload"}, status=400)
        try:
            telegram_id = int(telegram_id)
        except (TypeError, ValueError):
            return web.json_response({"error": "bad payload"}, status=400)

        async with session_factory() as session:
            user, _ = await crud.get_or_create_user(
                session, telegram_id=telegram_id, username=data.get("username")
            )
            is_first = await crud.mark_registered(session, user)
            await crud.log_event(
                session, user, "register_complete", {"first": is_first}
            )
            await session.commit()

            if not is_first:
                logger.info("user-registered: duplicate for tg_id=%s", telegram_id)
                return web.json_response({"ok": True})

            name = _format_name(data, user.username or str(telegram_id))
            text = t("ru", "admin_new_registration").format(
                name=name,
                utm=_format_utm(user),
                time=user.registered_at.strftime("%Y-%m-%d %H:%M UTC"),
            )

        try:
            await bot.send_message(settings.SUPPORT_CHAT_ID, text)
        except Exception:
            logger.error(
                "Failed to send new-registration notice to admin (chat_id=%s)",
                settings.SUPPORT_CHAT_ID,
                exc_info=True,
            )

        return web.json_response({"ok": True})

    app = web.Application()
    app.router.add_post("/api/bot/user-registered", user_registered)
    return app
