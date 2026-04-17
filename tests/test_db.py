import pytest
from bot.db import crud
from bot.db.models import BotDemoView, BotEvent, BotSupportTicket, BotUser


@pytest.mark.asyncio
async def test_create_new_user(db_session):
    user, created = await crud.get_or_create_user(db_session, telegram_id=111, username="alice")
    assert created is True
    assert user.telegram_id == 111
    assert user.username == "alice"
    assert user.id is not None


@pytest.mark.asyncio
async def test_get_existing_user_not_duplicated(db_session):
    await crud.get_or_create_user(db_session, telegram_id=222, username="bob")
    user2, created = await crud.get_or_create_user(db_session, telegram_id=222, username="bob")
    assert created is False
    result = await db_session.execute(
        __import__("sqlalchemy").select(BotUser).where(BotUser.telegram_id == 222)
    )
    rows = result.scalars().all()
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_set_language(db_session):
    user, _ = await crud.get_or_create_user(db_session, telegram_id=333)
    assert user.language is None
    await crud.set_language(db_session, user, "ru")
    assert user.language == "ru"


@pytest.mark.asyncio
async def test_save_utm_first_time(db_session):
    user, _ = await crud.get_or_create_user(db_session, telegram_id=444)
    await crud.save_utm(db_session, user, "tgads", "tg", "uzb4ru")
    assert user.utm_source == "tgads"
    assert user.utm_medium == "tg"
    assert user.utm_campaign == "uzb4ru"


@pytest.mark.asyncio
async def test_save_utm_not_overwritten(db_session):
    user, _ = await crud.get_or_create_user(db_session, telegram_id=555)
    await crud.save_utm(db_session, user, "first_source", "tg", "first_campaign")
    await crud.save_utm(db_session, user, "second_source", "tg", "second_campaign")
    assert user.utm_source == "first_source"
    assert user.utm_campaign == "first_campaign"


@pytest.mark.asyncio
async def test_log_demo_view(db_session):
    user, _ = await crud.get_or_create_user(db_session, telegram_id=666)
    view = await crud.log_demo_view(db_session, user, "coffee")
    assert isinstance(view, BotDemoView)
    assert view.niche == "coffee"
    assert view.bot_user_id == user.id


@pytest.mark.asyncio
async def test_create_ticket(db_session):
    user, _ = await crud.get_or_create_user(db_session, telegram_id=777)
    ticket = await crud.create_ticket(db_session, user, "Как создать магазин?")
    assert isinstance(ticket, BotSupportTicket)
    assert ticket.status == "open"
    assert ticket.message == "Как создать магазин?"


@pytest.mark.asyncio
async def test_log_event(db_session):
    user, _ = await crud.get_or_create_user(db_session, telegram_id=888)
    event = await crud.log_event(db_session, user, "demo_view", {"niche": "flowers"})
    assert isinstance(event, BotEvent)
    assert event.event_type == "demo_view"
    assert event.payload == {"niche": "flowers"}


@pytest.mark.asyncio
async def test_log_event_no_payload(db_session):
    user, _ = await crud.get_or_create_user(db_session, telegram_id=999)
    event = await crud.log_event(db_session, user, "menu_view")
    assert event.payload is None
