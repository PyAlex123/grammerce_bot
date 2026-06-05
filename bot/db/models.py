from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.db.engine import Base


class BotUser(Base):
    __tablename__ = "bot_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    language: Mapped[str | None] = mapped_column(String(2), nullable=True)
    utm_source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    utm_medium: Mapped[str | None] = mapped_column(String(64), nullable=True)
    utm_campaign: Mapped[str | None] = mapped_column(String(128), nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_active_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    registered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    demo_views: Mapped[list["BotDemoView"]] = relationship(back_populates="user")
    tickets: Mapped[list["BotSupportTicket"]] = relationship(back_populates="user")
    events: Mapped[list["BotEvent"]] = relationship(back_populates="user")


class BotDemoView(Base):
    __tablename__ = "bot_demo_views"

    id: Mapped[int] = mapped_column(primary_key=True)
    bot_user_id: Mapped[int] = mapped_column(ForeignKey("bot_users.id"), nullable=False)
    niche: Mapped[str] = mapped_column(String(32), nullable=False)
    viewed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["BotUser"] = relationship(back_populates="demo_views")


class BotSupportTicket(Base):
    __tablename__ = "bot_support_tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    bot_user_id: Mapped[int] = mapped_column(ForeignKey("bot_users.id"), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="open", nullable=False)
    operator_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["BotUser"] = relationship(back_populates="tickets")


class BotEvent(Base):
    __tablename__ = "bot_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    bot_user_id: Mapped[int] = mapped_column(ForeignKey("bot_users.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["BotUser"] = relationship(back_populates="events")
