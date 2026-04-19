import pytest
from unittest.mock import patch

from bot.handlers.demo import show_niches, handle_demo_callback
from bot.locales.ru import texts as RU
from bot.locales.uz import texts as UZ


@pytest.mark.asyncio
async def test_show_niches_sends_keyboard(make_message, db_session):
    from bot.db.crud import get_or_create_user, set_language
    user, _ = await get_or_create_user(db_session, 30001)
    await set_language(db_session, user, "ru")
    await db_session.commit()

    message = make_message(text=RU["btn_demo"], user_id=30001)
    await show_niches(message, session=db_session)
    message.answer.assert_called_once()
    assert message.answer.call_args.kwargs.get("reply_markup") is not None


@pytest.mark.asyncio
async def test_show_niches_uz(make_message, db_session):
    from bot.db.crud import get_or_create_user, set_language
    user, _ = await get_or_create_user(db_session, 30002)
    await set_language(db_session, user, "uz")
    await db_session.commit()

    message = make_message(text=UZ["btn_demo"], user_id=30002)
    await show_niches(message, session=db_session)
    message.answer.assert_called_once()


@pytest.mark.asyncio
async def test_demo_niche_logs_view(make_callback, db_session):
    from sqlalchemy import select as sa_select
    from bot.db.models import BotDemoView
    from bot.db.crud import get_or_create_user, set_language

    user, _ = await get_or_create_user(db_session, 30003)
    await set_language(db_session, user, "ru")
    await db_session.commit()

    cb = make_callback(data="demo:coffee", user_id=30003)
    with patch("bot.handlers.demo.settings") as mock_settings:
        mock_settings.demo_urls = {"coffee": "https://demo.grammerce.io/coffee"}
        await handle_demo_callback(cb, session=db_session)
        await db_session.commit()

    result = await db_session.execute(
        sa_select(BotDemoView).where(BotDemoView.niche == "coffee")
    )
    views = result.scalars().all()
    assert len(views) == 1


@pytest.mark.asyncio
async def test_demo_niche_logs_event(make_callback, db_session):
    from sqlalchemy import select as sa_select
    from bot.db.models import BotEvent
    from bot.db.crud import get_or_create_user, set_language

    user, _ = await get_or_create_user(db_session, 30004)
    await set_language(db_session, user, "ru")
    await db_session.commit()

    cb = make_callback(data="demo:flowers", user_id=30004)
    with patch("bot.handlers.demo.settings") as mock_settings:
        mock_settings.demo_urls = {"flowers": "https://demo.grammerce.io/flowers"}
        await handle_demo_callback(cb, session=db_session)
        await db_session.commit()

    result = await db_session.execute(
        sa_select(BotEvent).where(BotEvent.event_type == "demo_view")
    )
    events = result.scalars().all()
    assert any(e.payload and e.payload.get("niche") == "flowers" for e in events)


@pytest.mark.asyncio
async def test_demo_back_callback(make_callback, db_session):
    from bot.db.crud import get_or_create_user, set_language
    user, _ = await get_or_create_user(db_session, 30005)
    await set_language(db_session, user, "ru")
    await db_session.commit()

    cb = make_callback(data="demo:back", user_id=30005)
    await handle_demo_callback(cb, session=db_session)
    cb.message.edit_text.assert_called_once()
    cb.answer.assert_called_once()


@pytest.mark.asyncio
async def test_demo_webapp_url_in_keyboard(make_callback, db_session):
    from bot.db.crud import get_or_create_user, set_language
    user, _ = await get_or_create_user(db_session, 30006)
    await set_language(db_session, user, "ru")
    await db_session.commit()

    cb = make_callback(data="demo:cosmetics", user_id=30006)
    with patch("bot.handlers.demo.settings") as mock_settings:
        mock_settings.demo_urls = {"cosmetics": "https://t.me/grammerce_cosmetics_bot"}
        await handle_demo_callback(cb, session=db_session)

    cb.message.edit_text.assert_called_once()
    kb = cb.message.edit_text.call_args.kwargs.get("reply_markup")
    assert kb is not None
    flat_buttons = [btn for row in kb.inline_keyboard for btn in row]
    url_buttons = [b for b in flat_buttons if b.url is not None]
    assert len(url_buttons) == 1
    assert url_buttons[0].url == "https://t.me/grammerce_cosmetics_bot"
