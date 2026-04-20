import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.filters.command import CommandObject
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import crud
from bot.keyboards.language import language_keyboard
from bot.keyboards.menu import main_menu_keyboard
from bot.locales import t

logger = logging.getLogger(__name__)
router = Router(name="start")


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
    message: Message, command: CommandObject, session: AsyncSession
) -> None:
    user, _ = await crud.get_or_create_user(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
    )

    if command.args == "register":
        from bot.handlers.register import send_auth_link

        await send_auth_link(message, session, user)
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

    if user.language:
        # Returning user — skip language selection, show menu
        await message.answer(
            t(user.language, "menu"),
            reply_markup=main_menu_keyboard(user.language),
        )
    else:
        await message.answer(
            t(None, "choose_language"),
            reply_markup=language_keyboard(),
        )


@router.message(Command("chatid"))
async def cmd_chatid(message: Message) -> None:
    await message.answer(
        f"Chat ID: <code>{message.chat.id}</code>\n"
        f"User ID: <code>{message.from_user.id}</code>",
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("lang:"))
async def select_language(callback: CallbackQuery, session: AsyncSession) -> None:
    lang = callback.data.split(":")[1]
    user, _ = await crud.get_or_create_user(
        session,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
    )
    await crud.set_language(session, user, lang)
    await crud.log_event(session, user, "language_select", {"language": lang})

    await callback.message.edit_text(t(lang, "welcome"))
    await callback.message.answer(
        t(lang, "menu"),
        reply_markup=main_menu_keyboard(lang),
    )
    await crud.log_event(session, user, "menu_view", {"source": "language_select"})
    await callback.answer()
