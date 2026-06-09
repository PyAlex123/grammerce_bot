import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from aiogram.fsm.context import FSMContext

from bot.handlers.support import show_support, handle_faq, receive_support_message
from bot.locales.ru import texts as RU
from bot.states.support import SupportStates


def _make_state() -> FSMContext:
    state = MagicMock(spec=FSMContext)
    state.set_state = AsyncMock()
    state.clear = AsyncMock()
    state.get_state = AsyncMock(return_value=None)
    return state


@pytest.mark.asyncio
async def test_show_support_sends_keyboard(make_message, db_session):
    from bot.db.crud import get_or_create_user, set_language
    user, _ = await get_or_create_user(db_session, 40001)
    await set_language(db_session, user, "ru")
    await db_session.commit()

    message = make_message(text=RU["btn_support"], user_id=40001)
    await show_support(message, session=db_session)
    message.answer.assert_called_once()
    kb = message.answer.call_args.kwargs.get("reply_markup")
    assert kb is not None
    flat_buttons = [btn for row in kb.inline_keyboard for btn in row]
    cb_data = [b.callback_data for b in flat_buttons]
    # Exactly 3 questions now — Цена / Сроки / Оператор
    assert cb_data == ["faq:price", "faq:terms", "faq:operator"]
    assert "faq:setup" not in cb_data
    assert "faq:api" not in cb_data


@pytest.mark.asyncio
async def test_faq_price_answer(make_callback, db_session):
    from bot.db.crud import get_or_create_user, set_language
    user, _ = await get_or_create_user(db_session, 40002)
    await set_language(db_session, user, "ru")
    await db_session.commit()

    cb = make_callback(data="faq:price", user_id=40002)
    state = _make_state()
    await handle_faq(cb, state=state, session=db_session)
    cb.message.answer.assert_called_once()
    text = cb.message.answer.call_args[0][0]
    assert "390 000" in text
    assert "7 дней" in text
    assert cb.message.answer.call_args.kwargs.get("reply_markup") is None


@pytest.mark.asyncio
async def test_faq_answers_have_no_back_button(make_callback, db_session):
    from bot.db.crud import get_or_create_user, set_language
    for i, topic in enumerate(["price", "terms"], start=40020):
        user, _ = await get_or_create_user(db_session, i)
        await set_language(db_session, user, "ru")
        await db_session.commit()

        cb = make_callback(data=f"faq:{topic}", user_id=i)
        state = _make_state()
        await handle_faq(cb, state=state, session=db_session)
        assert cb.message.answer.call_args.kwargs.get("reply_markup") is None, (
            f"FAQ answer for topic={topic} must not include a reply markup"
        )


@pytest.mark.asyncio
async def test_faq_answers_do_not_contain_forbidden_phrases(make_callback, db_session):
    from bot.db.crud import get_or_create_user, set_language

    forbidden = ["$", "docs.grammerce.io", "/pricing", "5 минут", "14 дней", "Setup Fee"]
    for i, (topic, lang) in enumerate(
        [
            ("price", "ru"), ("terms", "ru"),
            ("price", "uz"), ("terms", "uz"),
        ],
        start=40030,
    ):
        user, _ = await get_or_create_user(db_session, i)
        await set_language(db_session, user, lang)
        await db_session.commit()

        cb = make_callback(data=f"faq:{topic}", user_id=i)
        state = _make_state()
        await handle_faq(cb, state=state, session=db_session)
        text = cb.message.answer.call_args[0][0]
        for phrase in forbidden:
            assert phrase not in text, (
                f"FAQ answer for topic={topic} lang={lang} must not contain '{phrase}', got: {text!r}"
            )


@pytest.mark.asyncio
async def test_faq_all_topics_have_answers(make_callback, db_session):
    from bot.db.crud import get_or_create_user, set_language
    for i, topic in enumerate(["price", "terms"], start=40010):
        user, _ = await get_or_create_user(db_session, i)
        await set_language(db_session, user, "ru")
        await db_session.commit()

        cb = make_callback(data=f"faq:{topic}", user_id=i)
        state = _make_state()
        await handle_faq(cb, state=state, session=db_session)
        cb.message.answer.assert_called_once(), f"No answer for topic={topic}"


@pytest.mark.asyncio
async def test_faq_operator_sets_fsm_state(make_callback, db_session):
    from bot.db.crud import get_or_create_user, set_language
    user, _ = await get_or_create_user(db_session, 40003)
    await set_language(db_session, user, "ru")
    await db_session.commit()

    cb = make_callback(data="faq:operator", user_id=40003)
    state = _make_state()
    await handle_faq(cb, state=state, session=db_session)
    state.set_state.assert_called_once_with(SupportStates.waiting_message)
    cb.message.answer.assert_called_once()


@pytest.mark.asyncio
async def test_support_ticket_created(make_message, db_session):
    from sqlalchemy import select as sa_select
    from bot.db.models import BotSupportTicket
    from bot.db.crud import get_or_create_user, set_language

    user, _ = await get_or_create_user(db_session, 40004)
    await set_language(db_session, user, "ru")
    await db_session.commit()

    message = make_message(text="Хочу узнать про тарифы", user_id=40004)
    state = _make_state()
    mock_bot = MagicMock()
    mock_bot.send_message = AsyncMock()

    with patch("bot.handlers.support.settings") as mock_settings:
        mock_settings.SUPPORT_CHAT_ID = -999
        await receive_support_message(message, state=state, bot=mock_bot, session=db_session)
        await db_session.commit()

    result = await db_session.execute(
        sa_select(BotSupportTicket).where(BotSupportTicket.bot_user_id == user.id)
    )
    tickets = result.scalars().all()
    assert len(tickets) == 1
    assert tickets[0].status == "open"
    assert "тарифы" in tickets[0].message


@pytest.mark.asyncio
async def test_support_ticket_forwarded_to_chat(make_message, db_session):
    from bot.db.crud import get_or_create_user, set_language
    user, _ = await get_or_create_user(db_session, 40005)
    await set_language(db_session, user, "ru")
    await db_session.commit()

    message = make_message(text="Тестовый вопрос", user_id=40005)
    state = _make_state()
    mock_bot = MagicMock()
    mock_bot.send_message = AsyncMock()

    with patch("bot.handlers.support.settings") as mock_settings:
        mock_settings.SUPPORT_CHAT_ID = -12345
        await receive_support_message(message, state=state, bot=mock_bot, session=db_session)

    mock_bot.send_message.assert_called_once()
    call_args = mock_bot.send_message.call_args
    assert call_args[0][0] == -12345


@pytest.mark.asyncio
async def test_support_ticket_clears_fsm_state(make_message, db_session):
    from bot.db.crud import get_or_create_user, set_language
    user, _ = await get_or_create_user(db_session, 40006)
    await set_language(db_session, user, "ru")
    await db_session.commit()

    message = make_message(text="Вопрос", user_id=40006)
    state = _make_state()
    mock_bot = MagicMock()
    mock_bot.send_message = AsyncMock()

    with patch("bot.handlers.support.settings") as mock_settings:
        mock_settings.SUPPORT_CHAT_ID = -999
        await receive_support_message(message, state=state, bot=mock_bot, session=db_session)

    state.clear.assert_called_once()


@pytest.mark.asyncio
async def test_support_ticket_logs_event(make_message, db_session):
    from sqlalchemy import select as sa_select
    from bot.db.models import BotEvent
    from bot.db.crud import get_or_create_user, set_language

    user, _ = await get_or_create_user(db_session, 40007)
    await set_language(db_session, user, "ru")
    await db_session.commit()

    message = make_message(text="Вопрос про API", user_id=40007)
    state = _make_state()
    mock_bot = MagicMock()
    mock_bot.send_message = AsyncMock()

    with patch("bot.handlers.support.settings") as mock_settings:
        mock_settings.SUPPORT_CHAT_ID = -999
        await receive_support_message(message, state=state, bot=mock_bot, session=db_session)
        await db_session.commit()

    result = await db_session.execute(
        sa_select(BotEvent).where(BotEvent.event_type == "support_ticket")
    )
    events = result.scalars().all()
    assert len(events) >= 1
