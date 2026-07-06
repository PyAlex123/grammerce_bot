import pytest
from unittest.mock import AsyncMock

from sqlalchemy import select as sa_select

from bot.db import crud
from bot.db.models import BotEvent
from bot.handlers.register import (
    handle_create_callback,
    handle_create_shop,
    send_create_shop_cta,
)
from bot.handlers.start import cmd_start
from bot.services.platform_auth import AuthLink, PlatformAuthError

CONSUME_URL = "https://grammerce.io/api/auth/telegram/consume?token=test-uuid"


# ---------------------------------------------------------------------------
# Create-shop CTA — opens the consume_url as a WebApp (inside Telegram)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_shop_opens_consume_url_as_webapp(
    make_message, db_session, monkeypatch
):
    monkeypatch.setattr(
        "bot.handlers.register.issue_auth_link", AsyncMock(return_value=CONSUME_URL)
    )

    message = make_message(text="🏪 Создать магазин", user_id=30001)
    await handle_create_shop(message, session=db_session)

    message.answer.assert_called_once()
    keyboard = message.answer.call_args.kwargs["reply_markup"]
    buttons = [b for row in keyboard.inline_keyboard for b in row]
    assert len(buttons) == 1
    # WebApp button (opens in Telegram), NOT a plain url button (browser)
    assert buttons[0].url is None
    assert buttons[0].web_app is not None
    assert buttons[0].web_app.url == CONSUME_URL


@pytest.mark.asyncio
async def test_create_shop_logs_register_click_event(
    make_message, db_session, monkeypatch
):
    monkeypatch.setattr(
        "bot.handlers.register.issue_auth_link", AsyncMock(return_value=CONSUME_URL)
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
async def test_menu_create_callback_opens_webapp(make_callback, db_session, monkeypatch):
    mock_issue = AsyncMock(return_value=CONSUME_URL)
    monkeypatch.setattr("bot.handlers.register.issue_auth_link", mock_issue)

    cb = make_callback(data="menu:create", user_id=30008)
    await handle_create_callback(cb, session=db_session)

    # Uses the real Telegram user (not the bot) for the auth request, with lang
    mock_issue.assert_awaited_once_with(cb.from_user, lang="ru")
    cb.answer.assert_called_once()
    # edit=True → the welcome message is edited in place (no new message).
    keyboard = cb.message.edit_text.call_args.kwargs["reply_markup"]
    assert keyboard.inline_keyboard[0][0].web_app.url == CONSUME_URL


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
    assert message.answer.call_args.kwargs.get("reply_markup") is None


@pytest.mark.asyncio
async def test_create_shop_platform_error_logs_event(
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
async def test_start_register_deeplink_shows_welcome_with_webapp_cta(
    make_message, make_command, db_session, monkeypatch
):
    """`/start register` lands on the full welcome (not a separate create-shop
    screen), and its primary CTA opens the platform as a Mini App directly.

    With no PLATFORM_WEBAPP_URL the button falls back to the one-shot
    consume_url as a WebApp — never to the menu:create callback (which used to
    replace the whole welcome menu with a lone "open platform" button)."""
    monkeypatch.setattr(
        "bot.handlers.start.issue_auth",
        AsyncMock(
            return_value=AuthLink(
                consume_url=CONSUME_URL, has_shop=False, needs_setup=True
            )
        ),
    )
    monkeypatch.setattr("bot.config.settings.PLATFORM_WEBAPP_URL", "")

    message = make_message(text="/start register", user_id=30005)
    command = make_command(args="register")
    await cmd_start(message, command=command, session=db_session, bot=AsyncMock())

    message.answer.assert_called_once()
    keyboard = message.answer.call_args.kwargs["reply_markup"]
    primary = keyboard.inline_keyboard[0][0]
    assert primary.callback_data is None  # not the menu:create callback anymore
    assert primary.web_app is not None    # opens inside Telegram (TWA)
    assert primary.web_app.url == CONSUME_URL


@pytest.mark.asyncio
async def test_start_register_shows_welcome_without_language_screen(
    make_message, make_command, db_session, monkeypatch
):
    """register deep-link never shows a blocking language screen — the welcome
    is rendered directly (language is silently auto-detected, like plain /start)."""
    monkeypatch.setattr(
        "bot.handlers.start.issue_auth",
        AsyncMock(
            return_value=AuthLink(
                consume_url=CONSUME_URL, has_shop=False, needs_setup=True
            )
        ),
    )

    message = make_message(text="/start register", user_id=30006, language_code="ru")
    command = make_command(args="register")
    await cmd_start(message, command=command, session=db_session, bot=AsyncMock())

    message.answer.assert_called_once()
    text = message.answer.call_args[0][0]
    assert "Tilni tanlang" not in text  # no language-selection screen
    assert "grammerce.io" in text        # the normal welcome is shown
    user, _ = await crud.get_or_create_user(db_session, 30006)
    assert user.language == "ru"          # auto-detected, not a blocking prompt


@pytest.mark.asyncio
async def test_cta_uses_uz_locale_when_user_language_is_uz(
    make_message, db_session, monkeypatch
):
    monkeypatch.setattr(
        "bot.handlers.register.issue_auth_link", AsyncMock(return_value=CONSUME_URL)
    )

    user, _ = await crud.get_or_create_user(db_session, 30007, "uzuser")
    await crud.set_language(db_session, user, "uz")

    message = make_message(user_id=30007)
    await send_create_shop_cta(message, db_session, user)

    text = message.answer.call_args[0][0]
    assert "2 daqiqa" in text
