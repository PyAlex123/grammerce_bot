import logging

from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.db import crud
from bot.db.models import BotUser
from bot.locales import t
from bot.locales.ru import texts as RU
from bot.locales.uz import texts as UZ
from bot.services.platform_auth import PlatformAuthError, issue_auth_link

logger = logging.getLogger(__name__)
router = Router(name="register")

_BTN_CREATE = {RU["btn_create_shop"], UZ["btn_create_shop"]}


async def send_auth_link(
    message: Message, session: AsyncSession, user: BotUser, tg_user=None
) -> None:
    """Send the single 'Создать магазин' CTA.

    When PLATFORM_WEBAPP_URL is set → one WebApp button that auto-logins via
    Telegram initData (no consume_url, no fork). Otherwise → one URL button with
    a one-shot consume_url issued by the platform. `tg_user` overrides the
    Telegram user used for the consume_url request (needed for callback queries,
    where message.from_user is the bot).
    """
    lang = user.language or "ru"

    if settings.PLATFORM_WEBAPP_URL:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(
                    text=t(lang, "btn_create_shop"),
                    web_app=WebAppInfo(url=settings.PLATFORM_WEBAPP_URL),
                )
            ]]
        )
        await crud.log_event(session, user, "register_click", {"mode": "webapp"})
        await message.answer(t(lang, "cta_create_shop_prompt"), reply_markup=keyboard)
        return

    # Fallback: one-shot consume_url link — a single button, no fork.
    try:
        consume_url = await issue_auth_link(tg_user or message.from_user)
    except PlatformAuthError as exc:
        await crud.log_event(session, user, "register_error", {"reason": str(exc)})
        await message.answer(t(lang, "register_error"))
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text=t(lang, "cta_open_platform_btn"), url=consume_url)
        ]]
    )
    await crud.log_event(session, user, "register_click", {"consume_url": consume_url})
    await message.answer(t(lang, "cta_create_shop_prompt"), reply_markup=keyboard)


@router.message(F.text.in_(_BTN_CREATE))
async def handle_create_shop(message: Message, session: AsyncSession) -> None:
    user, _ = await crud.get_or_create_user(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
    )
    await send_auth_link(message, session, user)


@router.callback_query(F.data == "menu:create")
async def handle_create_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    """Welcome-screen 'Создать магазин' fallback when no WebApp URL is configured."""
    user, _ = await crud.get_or_create_user(
        session,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
    )
    await send_auth_link(callback.message, session, user, tg_user=callback.from_user)
    await callback.answer()
