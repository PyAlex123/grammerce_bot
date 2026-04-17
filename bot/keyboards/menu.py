from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from bot.locales import t


def main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(lang, "btn_create_shop"))],
            [KeyboardButton(text=t(lang, "btn_demo"))],
            [KeyboardButton(text=t(lang, "btn_support"))],
        ],
        resize_keyboard=True,
    )
