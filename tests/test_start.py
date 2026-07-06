import pytest
from unittest.mock import AsyncMock

from bot.handlers.start import cmd_start, detect_language, parse_utm, select_language
from bot.services.platform_auth import AuthLink


@pytest.fixture(autouse=True)
def _mock_issue_auth(monkeypatch):
    """Stub the platform call so /start tests never hit the network.

    The welcome flow calls issue_auth to pre-generate the desktop consume_url
    and read has_shop; return a fixed AuthLink for both start.py and its use in
    select_language."""
    monkeypatch.setattr(
        "bot.handlers.start.issue_auth",
        AsyncMock(
            return_value=AuthLink(
                consume_url="https://platform.test/consume/x",
                has_shop=False,
                needs_setup=True,
            )
        ),
    )


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
# Unit tests: detect_language
# ---------------------------------------------------------------------------

def test_detect_language_uz():
    assert detect_language("uz") == "uz"
    assert detect_language("uz-UZ") == "uz"


def test_detect_language_defaults_to_ru():
    assert detect_language("en") == "ru"
    assert detect_language(None) == "ru"


# ---------------------------------------------------------------------------
# Integration tests: /start handler
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_start_new_user_shows_personalised_welcome(make_message, make_command, db_session, make_state):
    message = make_message(text="/start", first_name="Алиса")
    command = make_command(args=None)
    await cmd_start(message, command=command, session=db_session, bot=AsyncMock(), state=make_state())
    message.answer.assert_called_once()
    text = message.answer.call_args[0][0]
    assert "Алиса" in text  # personalised by first_name
    assert message.answer.call_args.kwargs.get("reply_markup") is not None

    # Language auto-detected and saved (no blocking language screen)
    from bot.db.crud import get_or_create_user
    user, _ = await get_or_create_user(db_session, 123456)
    assert user.language == "ru"


@pytest.mark.asyncio
async def test_start_autodetects_uz_from_language_code(make_message, make_command, db_session, make_state):
    message = make_message(text="/start", user_id=10010, language_code="uz")
    command = make_command(args=None)
    await cmd_start(message, command=command, session=db_session, bot=AsyncMock(), state=make_state())

    from bot.db.crud import get_or_create_user
    user, _ = await get_or_create_user(db_session, 10010)
    assert user.language == "uz"
    text = message.answer.call_args[0][0]
    assert "Salom" in text


@pytest.mark.asyncio
async def test_start_with_utm_saves_to_db(make_message, make_command, db_session, make_state):
    message = make_message(text="/start utm_tgads_uzb4ru", user_id=10001)
    command = make_command(args="utm_tgads_uzb4ru")
    await cmd_start(message, command=command, session=db_session, bot=AsyncMock(), state=make_state())

    from bot.db.crud import get_or_create_user
    user, _ = await get_or_create_user(db_session, 10001)
    assert user.utm_source == "tgads"
    assert user.utm_campaign == "uzb4ru"


@pytest.mark.asyncio
async def test_start_returning_user_shows_welcome(make_message, make_command, db_session, make_state):
    from bot.db.crud import get_or_create_user, set_language
    user, _ = await get_or_create_user(db_session, 10002, "returning")
    await set_language(db_session, user, "ru")
    await db_session.commit()

    message = make_message(text="/start", user_id=10002, first_name="Боб")
    command = make_command(args=None)
    await cmd_start(message, command=command, session=db_session, bot=AsyncMock(), state=make_state())
    message.answer.assert_called_once()
    # Personalised welcome (no language-selection blocker)
    text = message.answer.call_args[0][0]
    assert "Боб" in text
    assert "grammerce.io" in text


@pytest.mark.asyncio
async def test_utm_not_overwritten_on_second_start(make_message, make_command, db_session, make_state):
    from bot.db.crud import get_or_create_user, save_utm
    user, _ = await get_or_create_user(db_session, 10003)
    await save_utm(db_session, user, "original", "tg", "original_campaign")
    await db_session.commit()

    message = make_message(text="/start utm_new_campaign", user_id=10003)
    command = make_command(args="utm_new_campaign")
    await cmd_start(message, command=command, session=db_session, bot=AsyncMock(), state=make_state())

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
    # Toggle re-renders the welcome in place (edit), no extra message
    cb.message.edit_text.assert_called_once()
    cb.answer.assert_called_once()


@pytest.mark.asyncio
async def test_select_language_uz(make_callback, db_session):
    cb = make_callback(data="lang:uz", user_id=20002)
    await select_language(cb, session=db_session)

    from bot.db.crud import get_or_create_user
    user, _ = await get_or_create_user(db_session, 20002)
    assert user.language == "uz"


@pytest.mark.asyncio
async def test_language_toggle_rerenders_welcome(make_callback, db_session):
    from bot.db.crud import get_or_create_user, set_language
    user, _ = await get_or_create_user(db_session, 20010)
    await set_language(db_session, user, "ru")
    await db_session.commit()

    cb = make_callback(data="lang:uz", user_id=20010, first_name="Дима")
    await select_language(cb, session=db_session)

    text = cb.message.edit_text.call_args[0][0]
    assert "Salom" in text  # switched to uz greeting
    assert "Дима" in text
    assert cb.message.edit_text.call_args.kwargs.get("reply_markup") is not None


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
