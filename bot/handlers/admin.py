"""Admin broadcast flow (/broadcast) — segmented manual mailings.

Only the admin (``SUPPORT_CHAT_ID``) can use it. Registered before the operator
router; content is captured only while in ``BroadcastStates.waiting_content`` so
the live-operator chat is untouched the rest of the time.
"""
import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.db import crud
from bot.keyboards.broadcast import (
    cta_keyboard,
    language_keyboard,
    preview_keyboard,
    segment_keyboard,
)
from bot.keyboards.menu import push_keyboard
from bot.locales.ru import texts as RU
from bot.services.broadcast import run_broadcast
from bot.states.broadcast import BroadcastStates

logger = logging.getLogger(__name__)
router = Router(name="admin")


def _is_admin(chat_id: int) -> bool:
    return chat_id == settings.SUPPORT_CHAT_ID


def _lang_label(lang: str | None) -> str:
    return RU["bcast_lang_all"] if lang is None else RU[f"bcast_lang_{lang}"]


def _cta_markup(data: dict) -> InlineKeyboardMarkup | None:
    """Build the optional 'Создать магазин' button from stored flow state.

    Reuses ``push_keyboard`` (static WebApp button on PLATFORM_WEBAPP_URL, one
    for everyone). Returns None when CTA wasn't requested or no URL is set.
    """
    if not data.get("cta"):
        return None
    lang = data.get("lang") or "ru"
    return push_keyboard(lang, "btn_create_shop")


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext, session: AsyncSession) -> None:
    if message.from_user is None or not _is_admin(message.chat.id):
        return
    await state.clear()
    counts = await crud.segment_counts(session)
    await message.answer(RU["bcast_pick_segment"], reply_markup=segment_keyboard(counts))


@router.callback_query(F.data.startswith("bcast:seg:"))
async def pick_segment(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    if callback.message is None or not _is_admin(callback.message.chat.id):
        await callback.answer()
        return
    segment = callback.data.split(":")[2]
    await state.update_data(segment=segment)
    # Language counts scoped to this segment.
    counts = {
        None: await crud.count_segment(session, segment, None),
        "ru": await crud.count_segment(session, segment, "ru"),
        "uz": await crud.count_segment(session, segment, "uz"),
    }
    await callback.message.answer(RU["bcast_pick_lang"], reply_markup=language_keyboard(counts))
    await callback.answer()


@router.callback_query(F.data.startswith("bcast:lang:"))
async def pick_language(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_admin(callback.message.chat.id):
        await callback.answer()
        return
    raw = callback.data.split(":")[2]
    lang = None if raw == "all" else raw
    await state.update_data(lang=lang)
    await state.set_state(BroadcastStates.waiting_content)
    await callback.message.answer(RU["bcast_ask_content"])
    await callback.answer()


@router.message(BroadcastStates.waiting_content)
async def receive_content(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not _is_admin(message.chat.id):
        return
    await state.update_data(from_chat_id=message.chat.id, message_id=message.message_id)
    await message.answer(RU["bcast_ask_cta"], reply_markup=cta_keyboard())


@router.callback_query(F.data.startswith("bcast:cta:"))
async def pick_cta(
    callback: CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession
) -> None:
    if callback.message is None or not _is_admin(callback.message.chat.id):
        await callback.answer()
        return
    await state.update_data(cta=callback.data.split(":")[2] == "1")
    data = await state.get_data()

    markup = _cta_markup(data)
    if data.get("cta") and markup is None:
        await callback.message.answer(RU["bcast_no_cta_url"])

    segment, lang = data["segment"], data.get("lang")
    count = await crud.count_segment(session, segment, lang)

    # Preview: copy the stored message back with the CTA attached, then summary.
    await bot.copy_message(
        chat_id=callback.message.chat.id,
        from_chat_id=data["from_chat_id"],
        message_id=data["message_id"],
        reply_markup=markup,
    )
    summary = RU["bcast_preview_summary"].format(
        segment=RU[f"bcast_seg_{segment}"], lang=_lang_label(lang), count=count
    )
    await callback.message.answer(summary, reply_markup=preview_keyboard(count))
    await callback.answer()


@router.callback_query(F.data == "bcast:test")
async def send_test(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    if callback.message is None or not _is_admin(callback.message.chat.id):
        await callback.answer()
        return
    data = await state.get_data()
    # Single recipient — the admin themselves; nothing to flag as blocked.
    await run_broadcast(
        bot,
        [settings.SUPPORT_CHAT_ID],
        from_chat_id=data["from_chat_id"],
        message_id=data["message_id"],
        reply_markup=_cta_markup(data),
    )
    await callback.message.answer(RU["bcast_test_done"])
    await callback.answer()


@router.callback_query(F.data == "bcast:send")
async def send_all(
    callback: CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession
) -> None:
    if callback.message is None or not _is_admin(callback.message.chat.id):
        await callback.answer()
        return
    data = await state.get_data()
    segment, lang = data["segment"], data.get("lang")
    recipients = await crud.broadcast_recipients(session, segment, lang)
    if not recipients:
        await callback.message.answer(RU["bcast_empty"])
        await state.clear()
        await callback.answer()
        return

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(RU["bcast_sending"].format(count=len(recipients)))
    await callback.answer()

    delivered, failed, blocked = await run_broadcast(
        bot,
        recipients,
        from_chat_id=data["from_chat_id"],
        message_id=data["message_id"],
        reply_markup=_cta_markup(data),
    )
    # Persist who blocked the bot so the next broadcast (and the push
    # scheduler) skip them instead of re-discovering it every run.
    for tg_id in blocked:
        await crud.mark_blocked(session, tg_id)
    await crud.record_broadcast(
        session,
        segment=segment,
        lang=lang,
        total=len(recipients),
        delivered=delivered,
        failed=failed,
    )
    await state.clear()
    await callback.message.answer(
        RU["bcast_report"].format(delivered=delivered, failed=failed)
    )


@router.callback_query(F.data == "bcast:cancel")
async def cancel(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or not _is_admin(callback.message.chat.id):
        await callback.answer()
        return
    await state.clear()
    await callback.message.answer(RU["bcast_cancelled"])
    await callback.answer()
