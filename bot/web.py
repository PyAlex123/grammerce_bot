import logging
from datetime import datetime, timezone

from aiogram import Bot
from aiohttp import web
from sqlalchemy.ext.asyncio import async_sessionmaker

from bot.config import settings
from bot.db import crud
from bot.keyboards.menu import cabinet_button
from bot.locales import t

logger = logging.getLogger(__name__)


def _parse_dt(value) -> datetime | None:
    """Parse an ISO-8601 string into a naive UTC datetime, or None.

    Accepts a trailing 'Z' and tz-aware offsets; the result is stored naive in
    UTC to match the rest of the schema (datetime.utcnow()-based columns)."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        logger.warning("funnel-state: bad datetime %r", value)
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


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

    async def funnel_state(request: web.Request) -> web.Response:
        """Platform → bot funnel-state upsert that drives activation pushes.

        Body (all funnel fields optional, partial updates supported):
          { "telegram_id": "123", "product_count": 3, "training_completed": true,
            "trial_ends_at": "2026-06-15T00:00:00Z", "plan_paid": false,
            "store_created_at": "2026-06-01T10:00:00Z" }
        """
        telegram_id, data = await _parse_user_event(request)
        if telegram_id is None:
            return data  # error response

        async with session_factory() as session:
            user, _ = await crud.get_or_create_user(
                session, telegram_id=telegram_id, username=data.get("username")
            )
            await crud.update_funnel_state(
                session,
                user,
                product_count=data.get("product_count"),
                training_completed=data.get("training_completed"),
                trial_ends_at=_parse_dt(data.get("trial_ends_at")),
                plan_paid=data.get("plan_paid"),
                store_created_at=_parse_dt(data.get("store_created_at")),
            )
            await crud.log_event(
                session,
                user,
                "funnel_state_update",
                {
                    "product_count": data.get("product_count"),
                    "training_completed": data.get("training_completed"),
                    "plan_paid": data.get("plan_paid"),
                },
            )
            await session.commit()

        return web.json_response({"ok": True})

    app = web.Application()
    app.router.add_post("/api/bot/user-registered", user_registered)
    app.router.add_post("/api/bot/new-order", new_order)
    app.router.add_post("/api/bot/low-products", low_products)
    app.router.add_post("/api/bot/funnel-state", funnel_state)
    return app
