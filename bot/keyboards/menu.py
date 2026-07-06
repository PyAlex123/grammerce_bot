from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonWebApp, WebAppInfo

from bot.config import settings
from bot.locales import t

# Maps current language → target language for the toggle button.
_OTHER_LANG = {"ru": "uz", "uz": "ru"}


def _create_shop_button(
    lang: str,
    has_shop: bool = False,
    webapp_url: str | None = None,
    consume_url: str | None = None,
) -> InlineKeyboardButton:
    """Primary CTA — a WebApp button opening the platform as a Mini App (TWA).

    URL priority: an explicit ``webapp_url`` → the reusable ``PLATFORM_WEBAPP_URL``
    (auto-logs in by Telegram initData, re-openable without `auth_expired`) →
    the one-shot ``consume_url`` (still opens inside Telegram, logs in once).
    The label depends on `has_shop`: "open platform" when the user already has a
    shop, "create shop" otherwise.

    Only when no URL is available at all do we fall back to the ``menu:create``
    callback. That callback replaces the whole welcome menu with a separate
    "create shop" screen, so we avoid it whenever any URL exists — the button
    must open the Mini App directly, not swap out the menu.
    """
    label = t(lang, "btn_open_platform" if has_shop else "btn_create_shop")
    url = webapp_url or settings.PLATFORM_WEBAPP_URL or consume_url
    if url:
        return InlineKeyboardButton(text=label, web_app=WebAppInfo(url=url))
    return InlineKeyboardButton(text=label, callback_data="menu:create")


def chat_menu_button(lang: str, url: str | None = None) -> MenuButtonWebApp | None:
    """Persistent Menu Button shown next to the message input field.
    `url` should be a fresh one-shot consume_url so the button opens the
    platform with auth. Falls back to PLATFORM_WEBAPP_URL when not given.
    Returns None when no URL is available at all.
    """
    resolved = url or settings.PLATFORM_WEBAPP_URL
    if not resolved:
        return None
    return MenuButtonWebApp(
        text=t(lang, "btn_menu_button"),
        web_app=WebAppInfo(url=resolved),
    )


def welcome_keyboard(
    lang: str, *, has_shop: bool = False, consume_url: str | None = None
) -> InlineKeyboardMarkup:
    """First-screen keyboard.

    Row 1: WebApp CTA opening the persistent Mini App (label by `has_shop`).
    Row 2 (only when `consume_url` given): a plain url-button "open on computer"
    carrying the one-shot consume_url — for logging in from a desktop browser.
    Then Demo/Support and the language toggle.
    """
    other = _OTHER_LANG.get(lang, "uz")
    rows: list[list[InlineKeyboardButton]] = [
        [_create_shop_button(lang, has_shop, consume_url=consume_url)]
    ]
    if consume_url:
        rows.append(
            [InlineKeyboardButton(text=t(lang, "btn_open_desktop"), url=consume_url)]
        )
    rows.extend([
        [
            InlineKeyboardButton(text=t(lang, "btn_demo"), callback_data="menu:demo"),
            InlineKeyboardButton(text=t(lang, "btn_support"), callback_data="menu:support"),
        ],
        [InlineKeyboardButton(text=t(lang, "btn_lang_toggle"), callback_data=f"lang:{other}")],
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def research_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Single-button keyboard for the research welcome screen.
    Opens the survey WebApp directly; no main-menu buttons."""
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=t(lang, "research_btn_start"),
            web_app=WebAppInfo(url=settings.SURVEY_WEBAPP_URL),
        )
    ]])


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
