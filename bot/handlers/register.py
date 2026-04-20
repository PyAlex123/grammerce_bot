import logging

from aiogram import F, Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

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
    message: Message, session: AsyncSession, user: BotUser
) -> None:
    """Request a one-shot auth link from the platform and send it to the user."""
    lang = user.language or "ru"
    try:
        consume_url = await issue_auth_link(message.from_user)
    except PlatformAuthError as exc:
        await crud.log_event(
            session, user, "register_error", {"reason": str(exc)}
        )
        await message.answer(t(lang, "register_error"))
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "cta_open_platform_btn"), url=consume_url)]
        ]
    )
    await crud.log_event(
        session, user, "register_click", {"consume_url": consume_url}
    )
    await message.answer(t(lang, "cta_create_shop_prompt"), reply_markup=keyboard)


@router.message(F.text.in_(_BTN_CREATE))
async def handle_create_shop(message: Message, session: AsyncSession) -> None:
    user, _ = await crud.get_or_create_user(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
    )
    await send_auth_link(message, session, user)
