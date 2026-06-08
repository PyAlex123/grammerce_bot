from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from bot.config import settings
from bot.locales import t

# Maps current language → target language for the toggle button.
_OTHER_LANG = {"ru": "uz", "uz": "ru"}


def main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    # Deprecated reply keyboard — replaced by welcome_keyboard (inline) in start.py.
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(lang, "btn_create_shop"))],
            [KeyboardButton(text=t(lang, "btn_demo"))],
            [KeyboardButton(text=t(lang, "btn_support"))],
        ],
        resize_keyboard=True,
    )


def _create_shop_button(lang: str) -> InlineKeyboardButton:
    """Primary CTA. A WebApp button (initData auto-login) when PLATFORM_WEBAPP_URL
    is configured, otherwise a callback that falls back to the consume_url flow."""
    if settings.PLATFORM_WEBAPP_URL:
        return InlineKeyboardButton(
            text=t(lang, "btn_create_shop"),
            web_app=WebAppInfo(url=settings.PLATFORM_WEBAPP_URL),
        )
    return InlineKeyboardButton(
        text=t(lang, "btn_create_shop"),
        callback_data="menu:create",
    )


def welcome_keyboard(lang: str) -> InlineKeyboardMarkup:
    """First-screen keyboard: one primary CTA, two secondary actions, language toggle."""
    other = _OTHER_LANG.get(lang, "uz")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_create_shop_button(lang)],
            [
                InlineKeyboardButton(text=t(lang, "btn_demo"), callback_data="menu:demo"),
                InlineKeyboardButton(text=t(lang, "btn_support"), callback_data="menu:support"),
            ],
            [InlineKeyboardButton(text=t(lang, "btn_lang_toggle"), callback_data=f"lang:{other}")],
        ]
    )


def cabinet_button(lang: str, label_key: str) -> InlineKeyboardMarkup | None:
    """Single-button keyboard that opens the platform cabinet.

    WebApp button when PLATFORM_WEBAPP_URL is set; otherwise a URL button to the
    platform login page. Returns None when no URL is configured at all, so callers
    can send a plain message without a broken button.
    """
    if settings.PLATFORM_WEBAPP_URL:
        button = InlineKeyboardButton(
            text=t(lang, label_key),
            web_app=WebAppInfo(url=settings.PLATFORM_WEBAPP_URL),
        )
    elif settings.PLATFORM_URL:
        button = InlineKeyboardButton(
            text=t(lang, label_key),
            url=f"{settings.PLATFORM_URL.rstrip('/')}/login",
        )
    else:
        return None
    return InlineKeyboardMarkup(inline_keyboard=[[button]])
