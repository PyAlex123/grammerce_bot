from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)

from bot.locales import t

_NICHES = [
    ("coffee", "niche_coffee"),
    ("clothes", "niche_clothes"),
    ("flowers", "niche_flowers"),
    ("food", "niche_food"),
    ("cosmetics", "niche_cosmetics"),
    ("electronics", "niche_electronics"),
]


def niches_keyboard(lang: str) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=t(lang, label_key), callback_data=f"demo:{niche}")]
        for niche, label_key in _NICHES
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def webapp_keyboard(lang: str, url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "open_demo"), web_app=WebAppInfo(url=url))],
            [InlineKeyboardButton(text=t(lang, "back"), callback_data="demo:back")],
        ]
    )
