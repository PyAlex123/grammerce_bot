from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from bot.config import settings
from bot.locales import t

# Maps current language → target language for the toggle button.
_OTHER_LANG = {"ru": "uz", "uz": "ru"}


def _create_shop_button(lang: str) -> InlineKeyboardButton:
    """Primary CTA. Tapping it issues a one-shot login link and opens it inside
    Telegram (WebApp / Mini App) — handled by handlers/register (menu:create)."""
    return InlineKeyboardButton(
        text=t(lang, "btn_create_shop"), callback_data="menu:create"
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


def webapp_button(lang: str, label_key: str, url: str) -> InlineKeyboardMarkup:
    """Single-button keyboard that opens `url` inside Telegram (WebApp), not the browser."""
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text=t(lang, label_key), web_app=WebAppInfo(url=url))
        ]]
    )


def cabinet_button(lang: str, label_key: str) -> InlineKeyboardMarkup | None:
    """Lifecycle 'open cabinet' button — opens the platform inside Telegram (WebApp)."""
    url = settings.PLATFORM_WEBAPP_URL or settings.PLATFORM_URL
    if not url:
        return None
    return webapp_button(lang, label_key, url)
