import logging
from urllib.parse import urlencode

from aiogram import F, Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import crud
from bot.locales import t
from bot.locales.ru import texts as RU
from bot.locales.uz import texts as UZ

logger = logging.getLogger(__name__)
router = Router(name="register")

_BTN_CREATE = {RU["btn_create_shop"], UZ["btn_create_shop"]}
_REGISTER_BASE = "https://admin.grammerce.io/sign-up"


def _build_register_url(user) -> str:
    params: dict[str, str] = {"tg_user_id": str(user.telegram_id)}
    if user.utm_source:
        params["utm_source"] = user.utm_source
    if user.utm_medium:
        params["utm_medium"] = user.utm_medium
    if user.utm_campaign:
        params["utm_campaign"] = user.utm_campaign
    return f"{_REGISTER_BASE}?{urlencode(params)}"


@router.message(F.text.in_(_BTN_CREATE))
async def handle_create_shop(message: Message, session: AsyncSession) -> None:
    user, _ = await crud.get_or_create_user(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
    )
    lang = user.language or "ru"
    url = _build_register_url(user)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "register_btn"), url=url)]
        ]
    )
    await crud.log_event(session, user, "register_click", {"url": url})
    await message.answer(
        t(lang, "register_text"),
        reply_markup=keyboard,
        parse_mode="Markdown",
    )
