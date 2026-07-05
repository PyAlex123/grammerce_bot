from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.locales import t

_NICHES = [
    # ("coffee", "niche_coffee"),      # TODO: добавить когда будет демо-бот
    ("clothes", "niche_clothes"),
    ("flowers", "niche_flowers"),
    # ("food", "niche_food"),           # TODO: добавить когда будет демо-бот
    # ("cosmetics", "niche_cosmetics"),  # TODO: включить когда будет демо-магазин косметики
    ("electronics", "niche_electronics"),
]


def niches_keyboard(lang: str) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=t(lang, label_key), callback_data=f"demo:{niche}")]
        for niche, label_key in _NICHES
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def demo_bot_keyboard(lang: str, url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "open_demo"), url=url)],
            [InlineKeyboardButton(text=t(lang, "back"), callback_data="demo:back")],
        ]
    )
