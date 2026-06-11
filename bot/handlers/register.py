import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import crud
from bot.db.models import BotUser
from bot.keyboards.menu import webapp_button
from bot.locales import t
from bot.locales.ru import texts as RU
from bot.locales.uz import texts as UZ
from bot.services.platform_auth import PlatformAuthError, issue_auth_link

logger = logging.getLogger(__name__)
router = Router(name="register")

_BTN_CREATE = {RU["btn_create_shop"], UZ["btn_create_shop"]}


async def send_create_shop_cta(
    message: Message, session: AsyncSession, user: BotUser, tg_user=None
) -> None:
    """Issue a one-shot login link and present it as a WebApp button.

    The platform's consume_url opens inside Telegram (Mini App webview): it
    validates the token, logs the user in by telegram_id and redirects to the
    cabinet — no external browser, no separate Mini App page needed. `tg_user`
    overrides the Telegram user used for the request (for callback queries,
    where message.from_user is the bot).
    """
    lang = user.language or "ru"
    try:
        consume_url = await issue_auth_link(tg_user or message.from_user, lang=lang)
    except PlatformAuthError as exc:
        await crud.log_event(session, user, "register_error", {"reason": str(exc)})
        await message.answer(t(lang, "register_error"))
        return

    await crud.log_event(session, user, "register_click", {"consume_url": consume_url})
    await message.answer(
        t(lang, "cta_create_shop_prompt"),
        reply_markup=webapp_button(lang, "cta_open_platform_btn", consume_url),
    )


@router.message(F.text.in_(_BTN_CREATE))
async def handle_create_shop(message: Message, session: AsyncSession) -> None:
    user, _ = await crud.get_or_create_user(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
    )
    await send_create_shop_cta(message, session, user)


@router.callback_query(F.data == "menu:create")
async def handle_create_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    """Welcome-screen 'Создать магазин' button → issue link and open in Telegram."""
    user, _ = await crud.get_or_create_user(
        session,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
    )
    await send_create_shop_cta(callback.message, session, user, tg_user=callback.from_user)
    await callback.answer()
