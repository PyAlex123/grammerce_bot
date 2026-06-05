"""add registered_at to bot_users

Revision ID: 0001_add_registered_at
Revises:
Create Date: 2026-06-05

Idempotent: the column is only added when missing, so this is safe both on a
deployed DB (created earlier via create_all, without the column) and on a fresh
DB where create_all already added it.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_add_registered_at"
down_revision = None
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return column in {c["name"] for c in inspector.get_columns(table)}


def upgrade() -> None:
    if not _has_column("bot_users", "registered_at"):
        op.add_column(
            "bot_users",
            sa.Column("registered_at", sa.DateTime(), nullable=True),
        )


def downgrade() -> None:
    if _has_column("bot_users", "registered_at"):
        op.drop_column("bot_users", "registered_at")
