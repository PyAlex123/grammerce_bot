import logging

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.config import settings
from bot.locales.ru import texts as RU

logger = logging.getLogger(__name__)
router = Router(name="operator")

# Module-level session state (process-local, cleared on restart — same as MemoryStorage)
_current_user_id: int | None = None  # tg_id of user admin is currently chatting with
_active_user_ids: set[int] = set()   # set of user tg_ids in an active session


def _is_admin(chat_id: int) -> bool:
    return chat_id == settings.SUPPORT_CHAT_ID


def is_relayable(text: str | None) -> bool:
    """Текст из админского чата, который надо переслать пользователю.

    Команды (`/start`, `/chatid`, …) исключены: этот роутер подключён раньше
    start.router, и без фильтра он съедал бы их — админ не видел бы меню входа
    на платформу. `/broadcast` работает и так: admin.router идёт ещё раньше.
    """
    return bool(text) and not text.startswith("/")


@router.callback_query(F.data.startswith("operator:start:"))
async def operator_start_chat(callback: CallbackQuery, bot: Bot) -> None:
    if callback.message is None or not _is_admin(callback.message.chat.id):
        await callback.answer()
        return

    global _current_user_id

    parts = callback.data.split(":")  # ["operator", "start", "<id>", "<username>"]
    user_tg_id = int(parts[2])
    raw_username = parts[3] if len(parts) > 3 else str(user_tg_id)

    # Close previous session silently when switching to a new user
    if _current_user_id is not None and _current_user_id != user_tg_id:
        _active_user_ids.discard(_current_user_id)

    _current_user_id = user_tg_id
    _active_user_ids.add(user_tg_id)

    end_btn = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text=RU["operator_end_btn"], callback_data="operator:end")
        ]]
    )
    await callback.message.answer(
        RU["operator_chat_started_admin"].format(username=raw_username, tg_id=user_tg_id),
        reply_markup=end_btn,
    )
    await callback.answer("Чат активирован")

    try:
        await bot.send_message(user_tg_id, RU["operator_chat_started_user"])
    except Exception:
        logger.error(
            "Failed to notify user %s that operator joined", user_tg_id, exc_info=True
        )


# Сообщение админа, подлежащее пересылке пользователю. Вынесено из декоратора,
# чтобы фильтр можно было проверить тестами напрямую.
RELAY_FILTER = F.chat.func(lambda c: c.id == settings.SUPPORT_CHAT_ID) & F.text.func(
    is_relayable
)


@router.message(RELAY_FILTER)
async def operator_relay_to_user(message: Message, bot: Bot) -> None:
    if _current_user_id is None:
        await message.answer(RU["operator_no_active_chat"])
        return

    try:
        await bot.send_message(
            _current_user_id, RU["operator_relay_prefix"] + (message.text or "")
        )
    except Exception:
        logger.error(
            "Failed to relay operator message to user %s", _current_user_id, exc_info=True
        )


@router.callback_query(F.data == "operator:end")
async def operator_end_chat(callback: CallbackQuery, bot: Bot) -> None:
    if callback.message is None or not _is_admin(callback.message.chat.id):
        await callback.answer()
        return

    global _current_user_id

    if _current_user_id is None:
        await callback.answer(RU["operator_no_active_chat"], show_alert=True)
        return

    ended_user_id = _current_user_id
    _active_user_ids.discard(ended_user_id)
    _current_user_id = None

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(RU["operator_chat_ended_admin"])
    await callback.answer()

    try:
        await bot.send_message(ended_user_id, RU["operator_chat_ended_user"])
    except Exception:
        logger.error(
            "Failed to notify user %s that chat ended", ended_user_id, exc_info=True
        )
