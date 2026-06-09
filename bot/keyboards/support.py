from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.locales import t


def support_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "faq_price_btn"), callback_data="faq:price")],
            [InlineKeyboardButton(text=t(lang, "faq_timeline_btn"), callback_data="faq:terms")],
            [InlineKeyboardButton(text=t(lang, "faq_live_operator_btn"), callback_data="faq:operator")],
        ]
    )
