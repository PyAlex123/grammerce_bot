import pytest

from sqlalchemy import select as sa_select

from bot.db import crud
from bot.db.models import BotEvent
from bot.handlers.register import handle_create_shop, send_create_shop_cta
from bot.handlers.start import cmd_start

WEBAPP_URL = "https://grammerce.io/app"


# ---------------------------------------------------------------------------
# WebApp button (PLATFORM_WEBAPP_URL set)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_shop_sends_single_webapp_button(
    make_message, db_session, monkeypatch
):
    monkeypatch.setattr("bot.keyboards.menu.settings.PLATFORM_WEBAPP_URL", WEBAPP_URL)

    message = make_message(text="🏪 Создать магазин", user_id=30001)
    await handle_create_shop(message, session=db_session)

    message.answer.assert_called_once()
    keyboard = message.answer.call_args.kwargs["reply_markup"]
    buttons = [b for row in keyboard.inline_keyboard for b in row]
    assert len(buttons) == 1
    assert buttons[0].web_app is not None
    assert buttons[0].web_app.url == WEBAPP_URL


@pytest.mark.asyncio
async def test_create_shop_logs_register_click_event(
    make_message, db_session, monkeypatch
):
    monkeypatch.setattr("bot.keyboards.menu.settings.PLATFORM_WEBAPP_URL", WEBAPP_URL)

    message = make_message(text="🏪 Создать магазин", user_id=30002)
    await handle_create_shop(message, session=db_session)
    await db_session.commit()

    result = await db_session.execute(
        sa_select(BotEvent).where(BotEvent.event_type == "register_click")
    )
    events = result.scalars().all()
    assert len(events) == 1
    assert events[0].payload == {"mode": "webapp"}


@pytest.mark.asyncio
async def test_start_register_deeplink_sends_webapp_cta(
    make_message, make_command, db_session, monkeypatch
):
    monkeypatch.setattr("bot.keyboards.menu.settings.PLATFORM_WEBAPP_URL", WEBAPP_URL)

    message = make_message(text="/start register", user_id=30005)
    command = make_command(args="register")
    await cmd_start(message, command=command, session=db_session)

    message.answer.assert_called_once()
    keyboard = message.answer.call_args.kwargs["reply_markup"]
    assert keyboard.inline_keyboard[0][0].web_app.url == WEBAPP_URL


# ---------------------------------------------------------------------------
# Fallback when PLATFORM_WEBAPP_URL is unset (test env default) — single link
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_shop_falls_back_to_single_link_button(make_message, db_session):
    message = make_message(text="🏪 Создать магазин", user_id=30003)
    await handle_create_shop(message, session=db_session)

    keyboard = message.answer.call_args.kwargs["reply_markup"]
    buttons = [b for row in keyboard.inline_keyboard for b in row]
    # Still one button — a plain site link, never a crash, never a fork
    assert len(buttons) == 1
    assert buttons[0].web_app is None
    assert buttons[0].url is not None


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_start_register_skips_language_selection_for_new_user(
    make_message, make_command, db_session
):
    message = make_message(text="/start register", user_id=30006)
    command = make_command(args="register")
    await cmd_start(message, command=command, session=db_session)

    user, _ = await crud.get_or_create_user(db_session, 30006)
    assert user.language is None
    message.answer.assert_called_once()
    text = message.answer.call_args[0][0]
    assert "Tilni tanlang" not in text


@pytest.mark.asyncio
async def test_cta_uses_uz_locale_when_user_language_is_uz(make_message, db_session):
    user, _ = await crud.get_or_create_user(db_session, 30007, "uzuser")
    await crud.set_language(db_session, user, "uz")

    message = make_message(user_id=30007)
    await send_create_shop_cta(message, db_session, user)

    text = message.answer.call_args[0][0]
    assert "2 daqiqa" in text
