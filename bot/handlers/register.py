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
    message: Message, session: AsyncSession, user: BotUser, tg_user=None, *, edit: bool = False
) -> None:
    """Issue a one-shot login link and present it as a WebApp button.

    When `edit=True` the existing message is edited in-place (no extra
    message appears in the chat). Use this from callback handlers so the
    welcome message transforms directly into the open-platform button.
    `tg_user` overrides the Telegram user for the auth request (callbacks
    carry the bot user in message.from_user, not the real user).
    """
    lang = user.language or "ru"
    tg = tg_user or message.from_user
    assert tg is not None
    try:
        consume_url = await issue_auth_link(tg, lang=lang)
    except PlatformAuthError as exc:
        await crud.log_event(session, user, "register_error", {"reason": str(exc)})
        await message.answer(t(lang, "register_error"))
        return

    await crud.log_event(session, user, "register_click", {"consume_url": consume_url})
    kb = webapp_button(lang, "cta_open_platform_btn", consume_url)
    if edit:
        await message.edit_text(t(lang, "cta_create_shop_prompt"), reply_markup=kb)
    else:
        await message.answer(t(lang, "cta_create_shop_prompt"), reply_markup=kb)


@router.message(F.text.in_(_BTN_CREATE))
async def handle_create_shop(message: Message, session: AsyncSession) -> None:
    assert message.from_user is not None
    user, _ = await crud.get_or_create_user(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
    )
    await send_create_shop_cta(message, session, user)


@router.callback_query(F.data == "menu:create")
async def handle_create_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    """Welcome-screen 'Создать магазин' button → edits the message in-place, no new message."""
    user, _ = await crud.get_or_create_user(
        session,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
    )
    assert isinstance(callback.message, Message)
    await send_create_shop_cta(
        callback.message, session, user, tg_user=callback.from_user, edit=True
    )
    await callback.answer()
