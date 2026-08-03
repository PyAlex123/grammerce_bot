"""add bot_users.blocked_at

Revision ID: 0004_add_blocked_at
Revises: 0003_add_survey_tables
Create Date: 2026-08-03

Idempotent: the column is only added when missing, so this is safe both on the
deployed DB (created earlier via create_all, without it) and on a fresh DB
where create_all already added it.
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_add_blocked_at"
down_revision = "0003_add_survey_tables"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column in {c["name"] for c in inspector.get_columns(table)}


def upgrade() -> None:
    if not _has_column("bot_users", "blocked_at"):
        op.add_column("bot_users", sa.Column("blocked_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    if _has_column("bot_users", "blocked_at"):
        op.drop_column("bot_users", "blocked_at")
