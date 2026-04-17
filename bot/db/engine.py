from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


_engine = None
_session_factory: async_sessionmaker | None = None


def init_engine(database_url: str) -> None:
    global _engine, _session_factory
    _engine = create_async_engine(database_url, echo=False)
    _session_factory = async_sessionmaker(
        _engine, expire_on_commit=False, class_=AsyncSession
    )


def get_session_factory() -> async_sessionmaker:
    if _session_factory is None:
        raise RuntimeError("Call init_engine() before get_session_factory()")
    return _session_factory


async def create_tables() -> None:
    from bot.db import models  # noqa: F401 — ensure models are imported

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
