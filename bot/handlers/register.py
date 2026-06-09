import logging

from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import crud
from bot.db.models import BotUser
from bot.keyboards.menu import create_shop_keyboard
from bot.locales import t
from bot.locales.ru import texts as RU
from bot.locales.uz import texts as UZ

logger = logging.getLogger(__name__)
router = Router(name="register")

_BTN_CREATE = {RU["btn_create_shop"], UZ["btn_create_shop"]}


async def send_create_shop_cta(
    message: Message, session: AsyncSession, user: BotUser
) -> None:
    """Send the single WebApp 'Создать магазин' CTA.

    The button opens the platform Mini App, which logs the user in via Telegram
    initData (no password, no consume_url, no fork).
    """
    lang = user.language or "ru"
    await crud.log_event(session, user, "register_click", {"mode": "webapp"})
    await message.answer(
        t(lang, "cta_create_shop_prompt"), reply_markup=create_shop_keyboard(lang)
    )


@router.message(F.text.in_(_BTN_CREATE))
async def handle_create_shop(message: Message, session: AsyncSession) -> None:
    user, _ = await crud.get_or_create_user(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
    )
    await send_create_shop_cta(message, session, user)
