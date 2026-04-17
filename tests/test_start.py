import pytest
from unittest.mock import AsyncMock, MagicMock

from bot.handlers.start import cmd_start, parse_utm, select_language


# ---------------------------------------------------------------------------
# Unit tests: parse_utm
# ---------------------------------------------------------------------------

def test_parse_utm_valid():
    result = parse_utm("utm_tgads_uzb4ru")
    assert result["utm_source"] == "tgads"
    assert result["utm_medium"] == "tg"
    assert result["utm_campaign"] == "uzb4ru"


def test_parse_utm_no_campaign():
    result = parse_utm("utm_organic")
    assert result["utm_source"] == "organic"
    assert result.get("utm_campaign") is None


def test_parse_utm_none():
    assert parse_utm(None) == {}


def test_parse_utm_no_prefix():
    assert parse_utm("randomtext") == {}


# ---------------------------------------------------------------------------
# Integration tests: /start handler
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_start_new_user_shows_language_buttons(make_message, make_command, db_session):
    message = make_message(text="/start")
    command = make_command(args=None)
    await cmd_start(message, command=command, session=db_session)
    message.answer.assert_called_once()
    call_kwargs = message.answer.call_args
    assert call_kwargs.kwargs.get("reply_markup") is not None


@pytest.mark.asyncio
async def test_start_with_utm_saves_to_db(make_message, make_command, db_session):
    message = make_message(text="/start utm_tgads_uzb4ru", user_id=10001)
    command = make_command(args="utm_tgads_uzb4ru")
    await cmd_start(message, command=command, session=db_session)

    from bot.db.crud import get_or_create_user
    user, _ = await get_or_create_user(db_session, 10001)
    assert user.utm_source == "tgads"
    assert user.utm_campaign == "uzb4ru"


@pytest.mark.asyncio
async def test_start_returning_user_shows_menu(make_message, make_command, db_session):
    from bot.db.crud import get_or_create_user, set_language
    user, _ = await get_or_create_user(db_session, 10002, "returning")
    await set_language(db_session, user, "ru")
    await db_session.commit()

    message = make_message(text="/start", user_id=10002)
    command = make_command(args=None)
    await cmd_start(message, command=command, session=db_session)
    message.answer.assert_called_once()
    # Should show menu, not language selection
    text = message.answer.call_args[0][0]
    assert "меню" in text.lower() or "Меню" in text


@pytest.mark.asyncio
async def test_utm_not_overwritten_on_second_start(make_message, make_command, db_session):
    from bot.db.crud import get_or_create_user, save_utm
    user, _ = await get_or_create_user(db_session, 10003)
    await save_utm(db_session, user, "original", "tg", "original_campaign")
    await db_session.commit()

    message = make_message(text="/start utm_new_campaign", user_id=10003)
    command = make_command(args="utm_new_campaign")
    await cmd_start(message, command=command, session=db_session)

    user2, _ = await get_or_create_user(db_session, 10003)
    assert user2.utm_source == "original"


# ---------------------------------------------------------------------------
# Language selection callback
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_select_language_ru(make_callback, db_session):
    cb = make_callback(data="lang:ru", user_id=20001)
    await select_language(cb, session=db_session)

    from bot.db.crud import get_or_create_user
    user, _ = await get_or_create_user(db_session, 20001)
    assert user.language == "ru"
    cb.message.edit_text.assert_called_once()
    cb.message.answer.assert_called_once()
    cb.answer.assert_called_once()


@pytest.mark.asyncio
async def test_select_language_uz(make_callback, db_session):
    cb = make_callback(data="lang:uz", user_id=20002)
    await select_language(cb, session=db_session)

    from bot.db.crud import get_or_create_user
    user, _ = await get_or_create_user(db_session, 20002)
    assert user.language == "uz"


@pytest.mark.asyncio
async def test_language_select_logs_event(make_callback, db_session):
    from sqlalchemy import select as sa_select
    from bot.db.models import BotEvent

    cb = make_callback(data="lang:ru", user_id=20003)
    await select_language(cb, session=db_session)
    await db_session.commit()

    result = await db_session.execute(
        sa_select(BotEvent).where(BotEvent.event_type == "language_select")
    )
    events = result.scalars().all()
    assert len(events) >= 1
    assert events[0].payload == {"language": "ru"}
