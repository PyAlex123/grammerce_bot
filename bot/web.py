import logging

from aiogram import Bot
from aiohttp import web
from sqlalchemy.ext.asyncio import async_sessionmaker

from bot.config import settings
from bot.db import crud
from bot.keyboards.menu import cabinet_button
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
    """aiohttp app exposing platform → bot lifecycle callbacks.

    All endpoints authenticate with the same X-Bot-Secret header and expect a
    JSON body containing at least `telegram_id` (mirrors the existing contract).
    """

    async def _parse_user_event(request: web.Request):
        """Validate secret + JSON + telegram_id.

        Returns (telegram_id:int, data:dict) on success, or
        (None, error_response) on failure.
        """
        if request.headers.get("X-Bot-Secret") != settings.PLATFORM_BOT_SHARED_SECRET:
            logger.warning("%s: bad or missing X-Bot-Secret", request.path)
            return None, web.json_response({"error": "bad secret"}, status=401)
        try:
            data = await request.json()
        except Exception:
            return None, web.json_response({"error": "bad payload"}, status=400)
        telegram_id = data.get("telegram_id")
        if telegram_id is None:
            return None, web.json_response({"error": "bad payload"}, status=400)
        try:
            telegram_id = int(telegram_id)
        except (TypeError, ValueError):
            return None, web.json_response({"error": "bad payload"}, status=400)
        return telegram_id, data

    async def _send_to_user(telegram_id: int, text: str, markup=None) -> None:
        try:
            await bot.send_message(telegram_id, text, reply_markup=markup)
        except Exception:
            logger.error(
                "Failed to send lifecycle notice to user %s", telegram_id, exc_info=True
            )

    async def user_registered(request: web.Request) -> web.Response:
        telegram_id, data = await _parse_user_event(request)
        if telegram_id is None:
            return data  # error response

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
            admin_text = t("ru", "admin_new_registration").format(
                name=name,
                utm=_format_utm(user),
                time=user.registered_at.strftime("%Y-%m-%d %H:%M UTC"),
            )
            user_lang = user.language or "ru"

        # 1) notify the admin (operator chat)
        try:
            await bot.send_message(settings.SUPPORT_CHAT_ID, admin_text)
        except Exception:
            logger.error(
                "Failed to send new-registration notice to admin (chat_id=%s)",
                settings.SUPPORT_CHAT_ID,
                exc_info=True,
            )

        # 2) notify the user — store created, time to add products (§6.5.1)
        await _send_to_user(
            telegram_id,
            t(user_lang, "notify_store_created"),
            cabinet_button(user_lang, "btn_open_cabinet"),
        )

        return web.json_response({"ok": True})

    async def new_order(request: web.Request) -> web.Response:
        telegram_id, data = await _parse_user_event(request)
        if telegram_id is None:
            return data  # error response

        async with session_factory() as session:
            user = await crud.get_user_by_telegram_id(session, telegram_id)
            lang = (user.language if user else None) or "ru"
            if user is not None:
                await crud.log_event(
                    session, user, "notify_new_order",
                    {"order_number": data.get("order_number")},
                )
                await session.commit()

        text = t(lang, "notify_new_order").format(
            order_number=data.get("order_number", ""),
            customer_name=data.get("customer_name", ""),
            phone=data.get("phone", ""),
            amount=data.get("amount", ""),
        )
        await _send_to_user(telegram_id, text, cabinet_button(lang, "btn_open_order"))
        return web.json_response({"ok": True})

    async def low_products(request: web.Request) -> web.Response:
        telegram_id, data = await _parse_user_event(request)
        if telegram_id is None:
            return data  # error response

        async with session_factory() as session:
            user = await crud.get_user_by_telegram_id(session, telegram_id)
            lang = (user.language if user else None) or "ru"
            if user is not None:
                await crud.log_event(
                    session, user, "notify_low_products",
                    {"product_count": data.get("product_count")},
                )
                await session.commit()

        text = t(lang, "notify_low_products").format(
            product_count=data.get("product_count", ""),
        )
        await _send_to_user(telegram_id, text, cabinet_button(lang, "btn_add_products"))
        return web.json_response({"ok": True})

    app = web.Application()
    app.router.add_post("/api/bot/user-registered", user_registered)
    app.router.add_post("/api/bot/new-order", new_order)
    app.router.add_post("/api/bot/low-products", low_products)
    return app
