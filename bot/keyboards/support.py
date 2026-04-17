from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.locales import t


def support_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "faq_price"), callback_data="faq:price")],
            [InlineKeyboardButton(text=t(lang, "faq_setup"), callback_data="faq:setup")],
            [InlineKeyboardButton(text=t(lang, "faq_terms"), callback_data="faq:terms")],
            [InlineKeyboardButton(text=t(lang, "faq_api"), callback_data="faq:api")],
            [InlineKeyboardButton(text=t(lang, "live_operator"), callback_data="faq:operator")],
        ]
    )


def back_to_support_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "back"), callback_data="support:menu")]
        ]
    )
