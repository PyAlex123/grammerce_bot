import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.db import crud
from bot.keyboards.support import support_keyboard
from bot.locales import t
from bot.locales.ru import texts as RU
from bot.locales.uz import texts as UZ
from bot.states.support import SupportStates

logger = logging.getLogger(__name__)
router = Router(name="support")

_BTN_SUPPORT = {RU["btn_support"], UZ["btn_support"]}

_FAQ_ANSWERS = {
    "price": "faq_price",
    "terms": "faq_timeline",
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
    await message.answer(t(lang, "support_intro"), reply_markup=support_keyboard(lang))


async def open_live_operator(target_message, tg_user, state: FSMContext, session: AsyncSession) -> None:
    """Открыть чат с оператором: перевести пользователя в SupportStates.waiting_message
    и показать приглашение написать вопрос. Общий код для FAQ-кнопки «Живой оператор»
    и deep-link ?start=support. `tg_user` — реальный пользователь Telegram (в callbacks
    ``callback.message.from_user`` это бот, поэтому его передают отдельно)."""
    user, _ = await crud.get_or_create_user(
        session, telegram_id=tg_user.id, username=tg_user.username
    )
    lang = user.language or "ru"
    await state.set_state(SupportStates.waiting_message)
    await crud.log_event(session, user, "support_faq", {"topic": "operator"})
    await target_message.answer(t(lang, "ask_question"))


@router.callback_query(F.data == "menu:support")
async def open_support(callback: CallbackQuery, session: AsyncSession) -> None:
    """Entry point from the welcome-screen inline 'Поддержка' button."""
    user, _ = await crud.get_or_create_user(
        session,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
    )
    lang = user.language or "ru"
    await crud.log_event(session, user, "menu_view", {"section": "support"})
    await callback.message.answer(t(lang, "support_intro"), reply_markup=support_keyboard(lang))
    await callback.answer()


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
        await open_live_operator(callback.message, callback.from_user, state, session)
        await callback.answer()
        return

    answer_key = _FAQ_ANSWERS.get(topic)
    if answer_key:
        await crud.log_event(session, user, "support_faq", {"topic": topic})
        await callback.message.answer(t(lang, answer_key), parse_mode="HTML")
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

    raw_username = message.from_user.username or str(message.from_user.id)
    start_btn = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text=RU["operator_start_btn"],
                callback_data=f"operator:start:{message.from_user.id}:{raw_username}",
            )
        ]]
    )
    try:
        header = t("ru", "ticket_header").format(
            username=raw_username,
            tg_id=message.from_user.id,
            lang=user.language,
        )
        await bot.send_message(
            settings.SUPPORT_CHAT_ID,
            header + (message.text or ""),
            reply_markup=start_btn,
        )
    except Exception:
        logger.error(
            "Failed to forward ticket to support chat "
            "(admin may not have started the bot — chat_id=%s)",
            settings.SUPPORT_CHAT_ID,
            exc_info=True,
        )

    await state.clear()
    await message.answer(t(lang, "ticket_received"))


@router.message(F.text)
async def relay_user_to_operator(message: Message, bot: Bot) -> None:
    from bot.handlers.operator import _active_user_ids  # lazy — avoids circular import

    if message.from_user is None:
        return
    if message.from_user.id not in _active_user_ids:
        return

    prefix = RU["user_relay_prefix"].format(
        username=message.from_user.username or str(message.from_user.id)
    )
    try:
        await bot.send_message(settings.SUPPORT_CHAT_ID, prefix + (message.text or ""))
    except Exception:
        logger.error("Failed to relay user message to operator", exc_info=True)
