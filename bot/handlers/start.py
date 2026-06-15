import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.filters.command import CommandObject
from aiogram.types import CallbackQuery, Message, MenuButtonDefault
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import crud
from bot.keyboards.menu import welcome_keyboard
from bot.locales import t
from bot.services.platform_auth import PlatformAuthError, issue_auth_link

logger = logging.getLogger(__name__)
router = Router(name="start")


def detect_language(language_code: str | None) -> str:
    """Map a Telegram language_code to a supported locale (uz / ru, default ru)."""
    if language_code and language_code.lower().startswith("uz"):
        return "uz"
    return "ru"


async def _get_cta_url(tg_user, lang: str) -> str | None:
    """Generate a one-shot consume_url for the CTA button. Returns None on error."""
    try:
        return await issue_auth_link(tg_user, lang=lang)
    except PlatformAuthError as exc:
        logger.warning("Failed to pre-generate auth link: %s", exc)
        return None


async def _send_welcome(message: Message, bot: Bot, lang: str) -> None:
    assert message.from_user is not None
    name = (message.from_user.first_name or "").strip()
    cta_url = await _get_cta_url(message.from_user, lang)
    await message.answer(
        t(lang, "start_welcome").format(name=name),
        reply_markup=welcome_keyboard(lang, cta_url),
    )
    # Reset any previously-set menu button so users don't see a stale
    # "Grammerce" button that opened the plain site without auth.
    await bot.set_chat_menu_button(
        chat_id=message.from_user.id,
        menu_button=MenuButtonDefault(),
    )


def parse_utm(payload: str | None) -> dict[str, str | None]:
    """
    Parses deep-link payload in format utm_<source>_<campaign>.
    Example: utm_tgads_uzb4ru → source=tgads, medium=tg, campaign=uzb4ru
    """
    if not payload or not payload.startswith("utm_"):
        return {}
    rest = payload[4:]  # strip "utm_"
    parts = rest.split("_", 1)
    return {
        "utm_source": parts[0] if parts else None,
        "utm_medium": "tg",
        "utm_campaign": parts[1] if len(parts) > 1 else None,
    }


@router.message(CommandStart())
async def cmd_start(
    message: Message, command: CommandObject, session: AsyncSession, bot: Bot
) -> None:
    assert message.from_user is not None
    user, _ = await crud.get_or_create_user(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
    )

    if command.args == "register":
        from bot.handlers.register import send_create_shop_cta

        await send_create_shop_cta(message, session, user)
        return

    utm = parse_utm(command.args)
    if utm:
        await crud.save_utm(
            session,
            user,
            utm.get("utm_source"),
            utm.get("utm_medium"),
            utm.get("utm_campaign"),
        )

    # Auto-detect language from Telegram on first contact (no blocking screen).
    if not user.language:
        lang = detect_language(message.from_user.language_code)
        await crud.set_language(session, user, lang)
        await crud.log_event(session, user, "language_auto", {"language": lang})
    else:
        lang = user.language

    await _send_welcome(message, bot, lang)
    await crud.log_event(session, user, "menu_view", {"source": "start"})


@router.message(Command("chatid"))
async def cmd_chatid(message: Message) -> None:
    await message.answer(
        f"Chat ID: <code>{message.chat.id}</code>\n"
        f"User ID: <code>{message.from_user.id}</code>",
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("lang:"))
async def select_language(callback: CallbackQuery, session: AsyncSession) -> None:
    """Language toggle on the welcome screen — re-render the greeting in place."""
    assert callback.data is not None
    assert isinstance(callback.message, Message)
    lang = callback.data.split(":")[1]
    user, _ = await crud.get_or_create_user(
        session,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
    )
    await crud.set_language(session, user, lang)
    await crud.log_event(session, user, "language_select", {"language": lang})

    name = (callback.from_user.first_name or "").strip()
    cta_url = await _get_cta_url(callback.from_user, lang)
    await callback.message.edit_text(
        t(lang, "start_welcome").format(name=name),
        reply_markup=welcome_keyboard(lang, cta_url),
    )
    await callback.answer()
