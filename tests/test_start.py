import pytest
from bot.handlers.start import cmd_start


@pytest.mark.asyncio
async def test_start_replies_hello(make_message):
    message = make_message(text="/start")
    await cmd_start(message)
    message.answer.assert_called_once()
    text = message.answer.call_args[0][0]
    assert "Hello" in text or "Grammerce" in text
