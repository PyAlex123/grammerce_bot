from aiogram.fsm.state import State, StatesGroup


class BroadcastStates(StatesGroup):
    # Admin has picked a segment + language and is now sending the content
    # message (text, photo or a forwarded channel post) to broadcast.
    waiting_content = State()
