from datetime import datetime

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
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

    # Activation funnel state (fed by the platform via /api/bot/funnel-state).
    # store_created_at == registered_at (reused, not duplicated).
    product_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    first_product_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    training_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    plan_paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    demo_views: Mapped[list["BotDemoView"]] = relationship(back_populates="user")
    tickets: Mapped[list["BotSupportTicket"]] = relationship(back_populates="user")
    events: Mapped[list["BotEvent"]] = relationship(back_populates="user")
    push_sends: Mapped[list["BotPushSend"]] = relationship(back_populates="user")


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


class BotPushSend(Base):
    """One row per activation-push delivery. Makes the scheduler idempotent and
    enforces the "max 2 sends per step" rule (unique on user+step+send_no)."""

    __tablename__ = "bot_push_sends"
    __table_args__ = (
        UniqueConstraint("bot_user_id", "step", "send_no", name="uq_push_send"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    bot_user_id: Mapped[int] = mapped_column(ForeignKey("bot_users.id"), nullable=False)
    step: Mapped[int] = mapped_column(Integer, nullable=False)
    send_no: Mapped[int] = mapped_column(Integer, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["BotUser"] = relationship(back_populates="push_sends")


class SurveySource(Base):
    """One row per (user, source) — tracks deep-link clicks for funnel analytics."""

    __tablename__ = "survey_sources"
    __table_args__ = (
        UniqueConstraint("user_id", "source", name="uq_survey_source_user_source"),
        Index("idx_survey_sources_source", "source"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    entered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SurveyResponse(Base):
    """Completed survey submission received via web_app_data."""

    __tablename__ = "survey_responses"
    __table_args__ = (
        Index("idx_responses_source", "source"),
        Index("idx_responses_consent", "consent"),
        Index("idx_responses_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # 8 survey answer fields
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Postgres-native array in prod; JSON on SQLite (test engine can't render ARRAY).
    platforms: Mapped[list[str] | None] = mapped_column(
        ARRAY(Text).with_variant(JSON, "sqlite"), nullable=True
    )
    commission: Mapped[str | None] = mapped_column(String(32), nullable=True)
    contacts: Mapped[str | None] = mapped_column(String(64), nullable=True)
    lost_case: Mapped[str | None] = mapped_column(Text, nullable=True)
    own_channel: Mapped[str | None] = mapped_column(String(64), nullable=True)
    budget: Mapped[str | None] = mapped_column(String(64), nullable=True)
    pain: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Contact block
    contact_tg: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_store: Mapped[str | None] = mapped_column(String(255), nullable=True)
    consent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Meta
    lang: Mapped[str | None] = mapped_column(String(16), nullable=True)
    platform: Mapped[str | None] = mapped_column(String(32), nullable=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
