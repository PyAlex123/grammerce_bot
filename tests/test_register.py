import pytest
from unittest.mock import AsyncMock

from sqlalchemy import select as sa_select

from bot.db import crud
from bot.db.models import BotEvent
from bot.handlers.register import handle_create_shop, send_auth_link
from bot.handlers.start import cmd_start
from bot.services.platform_auth import PlatformAuthError


CONSUME_URL = "https://grammerce.io/api/auth/telegram/consume?token=test-uuid"
WEBAPP_URL = "https://grammerce.io/app"


# ---------------------------------------------------------------------------
# consume_url fallback mode (PLATFORM_WEBAPP_URL unset — the test env default)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_shop_issues_single_link_button(
    make_message, db_session, monkeypatch
):
    mock_issue = AsyncMock(return_value=CONSUME_URL)
    monkeypatch.setattr("bot.handlers.register.issue_auth_link", mock_issue)

    message = make_message(text="🏪 Создать магазин", user_id=30001)
    await handle_create_shop(message, session=db_session)

    mock_issue.assert_awaited_once_with(message.from_user)
    message.answer.assert_called_once()
    keyboard = message.answer.call_args.kwargs["reply_markup"]
    buttons = [b for row in keyboard.inline_keyboard for b in row]
    # One button only — no register/login fork
    assert len(buttons) == 1
    assert buttons[0].url == CONSUME_URL


@pytest.mark.asyncio
async def test_create_shop_logs_register_click_event(
    make_message, db_session, monkeypatch
):
    monkeypatch.setattr(
        "bot.handlers.register.issue_auth_link",
        AsyncMock(return_value=CONSUME_URL),
    )

    message = make_message(text="🏪 Создать магазин", user_id=30002)
    await handle_create_shop(message, session=db_session)
    await db_session.commit()

    result = await db_session.execute(
        sa_select(BotEvent).where(BotEvent.event_type == "register_click")
    )
    events = result.scalars().all()
    assert len(events) == 1
    assert events[0].payload == {"consume_url": CONSUME_URL}


@pytest.mark.asyncio
async def test_create_shop_platform_error_shows_user_message(
    make_message, db_session, monkeypatch
):
    monkeypatch.setattr(
        "bot.handlers.register.issue_auth_link",
        AsyncMock(side_effect=PlatformAuthError("platform returned HTTP 401")),
    )

    message = make_message(text="🏪 Создать магазин", user_id=30003)
    await handle_create_shop(message, session=db_session)

    message.answer.assert_called_once()
    text = message.answer.call_args[0][0]
    assert "⚠️" in text
    assert "не удалось" in text.lower()
    assert message.answer.call_args.kwargs.get("reply_markup") is None


@pytest.mark.asyncio
async def test_create_shop_platform_error_logs_register_error_event(
    make_message, db_session, monkeypatch
):
    monkeypatch.setattr(
        "bot.handlers.register.issue_auth_link",
        AsyncMock(side_effect=PlatformAuthError("timeout")),
    )

    message = make_message(text="🏪 Создать магазин", user_id=30004)
    await handle_create_shop(message, session=db_session)
    await db_session.commit()

    result = await db_session.execute(
        sa_select(BotEvent).where(BotEvent.event_type == "register_error")
    )
    events = result.scalars().all()
    assert len(events) == 1
    assert events[0].payload == {"reason": "timeout"}


@pytest.mark.asyncio
async def test_start_register_deeplink_triggers_auth_link(
    make_message, make_command, db_session, monkeypatch
):
    mock_issue = AsyncMock(return_value=CONSUME_URL)
    monkeypatch.setattr("bot.handlers.register.issue_auth_link", mock_issue)

    message = make_message(text="/start register", user_id=30005)
    command = make_command(args="register")
    await cmd_start(message, command=command, session=db_session)

    mock_issue.assert_awaited_once_with(message.from_user)
    message.answer.assert_called_once()
    keyboard = message.answer.call_args.kwargs["reply_markup"]
    assert keyboard.inline_keyboard[0][0].url == CONSUME_URL


@pytest.mark.asyncio
async def test_start_register_skips_language_selection_for_new_user(
    make_message, make_command, db_session, monkeypatch
):
    monkeypatch.setattr(
        "bot.handlers.register.issue_auth_link",
        AsyncMock(return_value=CONSUME_URL),
    )

    message = make_message(text="/start register", user_id=30006)
    command = make_command(args="register")
    await cmd_start(message, command=command, session=db_session)

    user, _ = await crud.get_or_create_user(db_session, 30006)
    assert user.language is None
    message.answer.assert_called_once()
    # Must be the auth-link message, not language selection
    text = message.answer.call_args[0][0]
    assert "Tilni tanlang" not in text


@pytest.mark.asyncio
async def test_send_auth_link_uses_uz_locale_when_user_language_is_uz(
    make_message, db_session, monkeypatch
):
    monkeypatch.setattr(
        "bot.handlers.register.issue_auth_link",
        AsyncMock(return_value=CONSUME_URL),
    )

    user, _ = await crud.get_or_create_user(db_session, 30007, "uzuser")
    await crud.set_language(db_session, user, "uz")

    message = make_message(user_id=30007)
    await send_auth_link(message, db_session, user)

    text = message.answer.call_args[0][0]
    assert "Platformani ochish" not in text  # that's the button, not the message
    assert "2 daqiqa" in text


# ---------------------------------------------------------------------------
# WebApp mode (PLATFORM_WEBAPP_URL set — Mini App auto-login)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_shop_webapp_mode_sends_webapp_button(
    make_message, db_session, monkeypatch
):
    monkeypatch.setattr("bot.handlers.register.settings.PLATFORM_WEBAPP_URL", WEBAPP_URL)
    mock_issue = AsyncMock()
    monkeypatch.setattr("bot.handlers.register.issue_auth_link", mock_issue)

    message = make_message(text="🏪 Создать магазин", user_id=30100)
    await handle_create_shop(message, session=db_session)

    # WebApp mode must NOT hit the platform for a consume_url
    mock_issue.assert_not_called()
    keyboard = message.answer.call_args.kwargs["reply_markup"]
    buttons = [b for row in keyboard.inline_keyboard for b in row]
    assert len(buttons) == 1
    assert buttons[0].web_app is not None
    assert buttons[0].web_app.url == WEBAPP_URL


@pytest.mark.asyncio
async def test_create_shop_webapp_mode_logs_webapp_mode(
    make_message, db_session, monkeypatch
):
    monkeypatch.setattr("bot.handlers.register.settings.PLATFORM_WEBAPP_URL", WEBAPP_URL)

    message = make_message(text="🏪 Создать магазин", user_id=30101)
    await handle_create_shop(message, session=db_session)
    await db_session.commit()

    result = await db_session.execute(
        sa_select(BotEvent).where(BotEvent.event_type == "register_click")
    )
    events = result.scalars().all()
    assert len(events) == 1
    assert events[0].payload == {"mode": "webapp"}
