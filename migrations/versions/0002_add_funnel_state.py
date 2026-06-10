"""add funnel-state columns + bot_push_sends table

Revision ID: 0002_add_funnel_state
Revises: 0001_add_registered_at
Create Date: 2026-06-10

Idempotent: columns/table are only added when missing, so this is safe both on a
deployed DB (created earlier via create_all, without them) and on a fresh DB
where create_all already added them.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0002_add_funnel_state"
down_revision = "0001_add_registered_at"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column in {c["name"] for c in inspector.get_columns(table)}


def _has_table(table: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table in inspector.get_table_names()


def upgrade() -> None:
    if not _has_column("bot_users", "product_count"):
        op.add_column(
            "bot_users",
            sa.Column("product_count", sa.Integer(), nullable=False, server_default="0"),
        )
    if not _has_column("bot_users", "first_product_at"):
        op.add_column(
            "bot_users", sa.Column("first_product_at", sa.DateTime(), nullable=True)
        )
    if not _has_column("bot_users", "training_completed"):
        op.add_column(
            "bot_users",
            sa.Column(
                "training_completed", sa.Boolean(), nullable=False, server_default=sa.false()
            ),
        )
    if not _has_column("bot_users", "trial_ends_at"):
        op.add_column(
            "bot_users", sa.Column("trial_ends_at", sa.DateTime(), nullable=True)
        )
    if not _has_column("bot_users", "plan_paid"):
        op.add_column(
            "bot_users",
            sa.Column("plan_paid", sa.Boolean(), nullable=False, server_default=sa.false()),
        )

    if not _has_table("bot_push_sends"):
        op.create_table(
            "bot_push_sends",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "bot_user_id",
                sa.Integer(),
                sa.ForeignKey("bot_users.id"),
                nullable=False,
            ),
            sa.Column("step", sa.Integer(), nullable=False),
            sa.Column("send_no", sa.Integer(), nullable=False),
            sa.Column("sent_at", sa.DateTime(), nullable=True),
            sa.UniqueConstraint(
                "bot_user_id", "step", "send_no", name="uq_push_send"
            ),
        )


def downgrade() -> None:
    if _has_table("bot_push_sends"):
        op.drop_table("bot_push_sends")
    for col in (
        "plan_paid",
        "trial_ends_at",
        "training_completed",
        "first_product_at",
        "product_count",
    ):
        if _has_column("bot_users", col):
            op.drop_column("bot_users", col)
