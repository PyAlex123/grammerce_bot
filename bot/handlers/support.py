import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.db import crud
from bot.keyboards.support import back_to_support_keyboard, support_keyboard
from bot.locales import t
from bot.locales.ru import texts as RU
from bot.locales.uz import texts as UZ
from bot.states.support import SupportStates

logger = logging.getLogger(__name__)
router = Router(name="support")

_BTN_SUPPORT = {RU["btn_support"], UZ["btn_support"]}

_FAQ_ANSWERS = {
    "price": "faq_price_answer",
    "setup": "faq_setup_answer",
    "terms": "faq_terms_answer",
    "api": "faq_api_answer",
}


@router.message(F.text.in_(_BTN_SUPPORT))
async def show_support(message: Message, session: AsyncSession) -> None:
    user, _ = await crud.get_or_create_user(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
    )
    lang = user.language or "ru"
    await crud.log_event(session, user, "menu_view", {"section": "support"})
    await message.answer(t(lang, "support_text"), reply_markup=support_keyboard(lang))


@router.callback_query(F.data.startswith("faq:"))
async def handle_faq(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    topic = callback.data.split(":")[1]
    user, _ = await crud.get_or_create_user(
        session,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
    )
    lang = user.language or "ru"

    if topic == "operator":
        await state.set_state(SupportStates.waiting_message)
        await crud.log_event(session, user, "support_faq", {"topic": "operator"})
        await callback.message.answer(t(lang, "ask_question"))
        await callback.answer()
        return

    answer_key = _FAQ_ANSWERS.get(topic)
    if answer_key:
        await crud.log_event(session, user, "support_faq", {"topic": topic})
        await callback.message.answer(
            t(lang, answer_key),
            reply_markup=back_to_support_keyboard(lang),
            parse_mode="Markdown",
        )
    await callback.answer()


@router.callback_query(F.data == "support:menu")
async def back_to_support_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    user, _ = await crud.get_or_create_user(
        session,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
    )
    lang = user.language or "ru"
    await callback.message.answer(
        t(lang, "support_text"), reply_markup=support_keyboard(lang)
    )
    await callback.answer()


@router.message(SupportStates.waiting_message)
async def receive_support_message(
    message: Message, state: FSMContext, bot: Bot, session: AsyncSession
) -> None:
    user, _ = await crud.get_or_create_user(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
    )
    lang = user.language or "ru"

    await crud.create_ticket(session, user, message.text or "")
    await crud.log_event(session, user, "support_ticket", {"length": len(message.text or "")})

    try:
        header = (
            f"📩 Новый тикет от @{message.from_user.username or message.from_user.id}\n"
            f"tg_id: {message.from_user.id}\n"
            f"lang: {user.language}\n"
            f"---\n"
        )
        await bot.send_message(settings.SUPPORT_CHAT_ID, header + (message.text or ""))
    except Exception:
        logger.error("Failed to forward ticket to support chat", exc_info=True)

    await state.clear()
    await message.answer(t(lang, "ticket_received"))
