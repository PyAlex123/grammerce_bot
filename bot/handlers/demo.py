import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.db import crud
from bot.keyboards.demo import demo_bot_keyboard, niches_keyboard
from bot.locales import t
from bot.locales.ru import texts as RU
from bot.locales.uz import texts as UZ

logger = logging.getLogger(__name__)
router = Router(name="demo")

_BTN_DEMO = {RU["btn_demo"], UZ["btn_demo"]}


@router.message(F.text.in_(_BTN_DEMO))
async def show_niches(message: Message, session: AsyncSession) -> None:
    user, _ = await crud.get_or_create_user(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
    )
    lang = user.language or "ru"
    await crud.log_event(session, user, "menu_view", {"section": "demo"})
    await message.answer(t(lang, "choose_niche"), reply_markup=niches_keyboard(lang))


@router.callback_query(F.data.startswith("demo:"))
async def handle_demo_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    niche = callback.data.split(":")[1]

    user, _ = await crud.get_or_create_user(
        session,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
    )
    lang = user.language or "ru"

    if niche == "back":
        await callback.message.edit_text(
            t(lang, "choose_niche"), reply_markup=niches_keyboard(lang)
        )
        await callback.answer()
        return

    url = settings.demo_urls.get(niche)
    if not url:
        logger.error("Unknown demo niche: %s", niche)
        await callback.answer()
        return

    await crud.log_demo_view(session, user, niche)
    await crud.log_event(session, user, "demo_view", {"niche": niche})

    niche_label_key = f"niche_{niche}"
    await callback.message.edit_text(
        f"{t(lang, niche_label_key)}\n\n{t(lang, 'open_demo')}",
        reply_markup=demo_bot_keyboard(lang, url),
    )
    await callback.answer()
