import json
import logging

from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import crud
from bot.keyboards.menu import research_keyboard
from bot.locales import t

logger = logging.getLogger(__name__)
router = Router(name="research")


async def send_research_welcome(message: Message, lang: str) -> None:
    """Send the research-flow welcome screen with only the survey WebApp button.
    Called from cmd_start when the deep-link param starts with 'research_'.
    No main-menu buttons are shown — this is an isolated flow."""
    await message.answer(
        t(lang, "research_welcome"),
        reply_markup=research_keyboard(lang),
    )


@router.message(F.web_app_data)
async def handle_survey_webapp_data(message: Message, session: AsyncSession) -> None:
    """Receive completed survey JSON from the WebApp via tg.sendData()."""
    assert message.from_user is not None

    raw = message.web_app_data.data if message.web_app_data else ""
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        logger.warning("survey: invalid JSON from user %s", message.from_user.id)
        user, _ = await crud.get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )
        lang = user.language or "ru"
        await crud.log_event(session, user, "survey_error", {"raw": raw[:200]})
        await message.answer(t(lang, "research_error"))
        return

    # Ignore web_app_data that isn't from the survey (e.g. other Mini Apps)
    if payload.get("type") != "survey_submission":
        return

    user, _ = await crud.get_or_create_user(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
    )
    lang = user.language or "ru"

    await crud.save_survey_response(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        payload=payload,
    )
    await crud.log_event(session, user, "survey_completed", {
        "source": payload.get("meta", {}).get("start_param"),
        "consent": payload.get("contact", {}).get("consent", False),
    })

    # Confirmation — plain text only, no CTA buttons (spec §2)
    await message.answer(t(lang, "research_confirmation"))
