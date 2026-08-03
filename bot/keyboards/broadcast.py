"""Inline keyboards for the admin broadcast flow (Russian-only, single admin)."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.db.crud import BROADCAST_SEGMENTS
from bot.locales.ru import texts as RU

_CANCEL_BTN = InlineKeyboardButton(text=RU["bcast_btn_cancel"], callback_data="bcast:cancel")


def segment_keyboard(counts: dict[str, int]) -> InlineKeyboardMarkup:
    """Segment picker — one button per segment, labelled with its live count."""
    rows = [
        [
            InlineKeyboardButton(
                text=f"{RU[f'bcast_seg_{seg}']} ({counts.get(seg, 0)})",
                callback_data=f"bcast:seg:{seg}",
            )
        ]
        for seg in BROADCAST_SEGMENTS
    ]
    rows.append([_CANCEL_BTN])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def language_keyboard(counts: dict[str | None, int]) -> InlineKeyboardMarkup:
    """Language filter — Все / Русский / Узбекский, each with its count."""
    rows = [
        [InlineKeyboardButton(
            text=f"{RU['bcast_lang_all']} ({counts.get(None, 0)})",
            callback_data="bcast:lang:all",
        )],
        [InlineKeyboardButton(
            text=f"{RU['bcast_lang_ru']} ({counts.get('ru', 0)})",
            callback_data="bcast:lang:ru",
        )],
        [InlineKeyboardButton(
            text=f"{RU['bcast_lang_uz']} ({counts.get('uz', 0)})",
            callback_data="bcast:lang:uz",
        )],
        [_CANCEL_BTN],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def cta_keyboard() -> InlineKeyboardMarkup:
    """Ask whether to attach the 'Создать магазин' button to the broadcast."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=RU["bcast_cta_yes"], callback_data="bcast:cta:1")],
        [InlineKeyboardButton(text=RU["bcast_cta_no"], callback_data="bcast:cta:0")],
        [_CANCEL_BTN],
    ])


def preview_keyboard(count: int) -> InlineKeyboardMarkup:
    """Final confirm — test to self, send to all (N), or cancel."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=RU["bcast_btn_test"], callback_data="bcast:test")],
        [InlineKeyboardButton(
            text=RU["bcast_btn_send"].format(count=count), callback_data="bcast:send"
        )],
        [_CANCEL_BTN],
    ])
