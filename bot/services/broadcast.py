"""Manual admin broadcasts.

Copies one source message (text, photo or a forwarded channel post) to a list
of recipients via ``bot.copy_message`` — the single primitive that reproduces
any message type without a "forwarded from" header. Throttled and resilient:
blocked/deleted users are counted as failures, Telegram flood waits are honoured.
"""
import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import InlineKeyboardMarkup

logger = logging.getLogger(__name__)

# ~20 messages/sec — safely under Telegram's ~30/sec broadcast ceiling.
_SEND_INTERVAL = 0.05


async def run_broadcast(
    bot: Bot,
    recipients: list[int],
    *,
    from_chat_id: int,
    message_id: int,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> tuple[int, int]:
    """Copy ``message_id`` (living in ``from_chat_id``) to every recipient.

    Returns ``(delivered, failed)``. A user who blocked the bot or deleted their
    account (``TelegramForbiddenError``) is a failure, not a crash. On a flood
    wait we sleep the requested time and retry that same recipient once.
    """
    delivered = 0
    failed = 0
    for tg_id in recipients:
        try:
            await bot.copy_message(
                chat_id=tg_id,
                from_chat_id=from_chat_id,
                message_id=message_id,
                reply_markup=reply_markup,
            )
            delivered += 1
        except TelegramRetryAfter as exc:
            # Flood control — wait it out and retry this recipient once.
            await asyncio.sleep(exc.retry_after)
            try:
                await bot.copy_message(
                    chat_id=tg_id,
                    from_chat_id=from_chat_id,
                    message_id=message_id,
                    reply_markup=reply_markup,
                )
                delivered += 1
            except Exception:
                logger.warning("broadcast: retry failed for %s", tg_id, exc_info=True)
                failed += 1
        except TelegramForbiddenError:
            # Bot blocked or account deleted — expected, count and move on.
            failed += 1
        except Exception:
            logger.warning("broadcast: send failed for %s", tg_id, exc_info=True)
            failed += 1
        await asyncio.sleep(_SEND_INTERVAL)

    logger.info("broadcast done: %s delivered, %s failed", delivered, failed)
    return delivered, failed
