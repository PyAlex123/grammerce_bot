from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonWebApp, WebAppInfo

from bot.config import settings
from bot.locales import t

# Maps current language → target language for the toggle button.
_OTHER_LANG = {"ru": "uz", "uz": "ru"}


def _create_shop_button(lang: str) -> InlineKeyboardButton:
    """Primary CTA.
    When PLATFORM_WEBAPP_URL is set — opens the platform directly as a Mini App
    (no extra step, auth via Telegram initData). Otherwise falls back to the
    one-shot consume_url flow via menu:create callback.
    """
    if settings.PLATFORM_WEBAPP_URL:
        return InlineKeyboardButton(
            text=t(lang, "btn_create_shop"),
            web_app=WebAppInfo(url=settings.PLATFORM_WEBAPP_URL),
        )
    return InlineKeyboardButton(
        text=t(lang, "btn_create_shop"), callback_data="menu:create"
    )


def chat_menu_button(lang: str) -> MenuButtonWebApp | None:
    """Persistent Menu Button shown next to the message input field.
    Returns None when no platform URL is configured.
    """
    url = settings.PLATFORM_WEBAPP_URL or settings.PLATFORM_URL
    if not url:
        return None
    return MenuButtonWebApp(text=t(lang, "btn_menu_button"), web_app=WebAppInfo(url=url))


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


def push_keyboard(
    lang: str, cta_label_key: str, with_channel: bool = False, url: str | None = None
) -> InlineKeyboardMarkup | None:
    """Keyboard for an activation push.

    Row 1: the CTA WebApp button. When `url` is given (a one-shot auto-login
    consume_url) the button opens it — logging the user straight into the
    cabinet. Otherwise it falls back to PLATFORM_WEBAPP_URL/PLATFORM_URL (the
    logged-out page). Row 2 (only when `with_channel` and CHANNEL_URL is set):
    a link to the channel. Returns None if there is no URL to point the CTA at.
    """
    url = url or settings.PLATFORM_WEBAPP_URL or settings.PLATFORM_URL
    if not url:
        return None
    rows = [[InlineKeyboardButton(text=t(lang, cta_label_key), web_app=WebAppInfo(url=url))]]
    if with_channel and settings.CHANNEL_URL:
        rows.append(
            [InlineKeyboardButton(text=t(lang, "push_btn_channel"), url=settings.CHANNEL_URL)]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)
