"""add survey_sources and survey_responses tables

Revision ID: 0003_add_survey_tables
Revises: 0002_add_funnel_state
Create Date: 2026-06-17

Idempotent: tables are only created when missing, so running this on a DB
that already has them (e.g. created via create_all) is safe.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_add_survey_tables"
down_revision = "0002_add_funnel_state"
branch_labels = None
depends_on = None


def _table_exists(name: str) -> bool:
    bind = op.get_bind()
    return sa.inspect(bind).has_table(name)


def upgrade() -> None:
    if not _table_exists("survey_sources"):
        op.create_table(
            "survey_sources",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("username", sa.String(255), nullable=True),
            sa.Column("source", sa.String(64), nullable=False),
            sa.Column(
                "entered_at",
                sa.DateTime(),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.UniqueConstraint("user_id", "source", name="uq_survey_source_user_source"),
        )
        op.create_index("idx_survey_sources_source", "survey_sources", ["source"])
        op.create_index("idx_survey_sources_user_id", "survey_sources", ["user_id"])

    if not _table_exists("survey_responses"):
        op.create_table(
            "survey_responses",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("username", sa.String(255), nullable=True),
            sa.Column("source", sa.String(64), nullable=True),
            sa.Column("category", sa.String(64), nullable=True),
            sa.Column("platforms", postgresql.ARRAY(sa.Text()), nullable=True),
            sa.Column("commission", sa.String(32), nullable=True),
            sa.Column("contacts", sa.String(64), nullable=True),
            sa.Column("lost_case", sa.Text(), nullable=True),
            sa.Column("own_channel", sa.String(64), nullable=True),
            sa.Column("budget", sa.String(64), nullable=True),
            sa.Column("pain", sa.Text(), nullable=True),
            sa.Column("contact_tg", sa.String(255), nullable=True),
            sa.Column("contact_store", sa.String(255), nullable=True),
            sa.Column("consent", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("lang", sa.String(16), nullable=True),
            sa.Column("platform", sa.String(32), nullable=True),
            sa.Column("raw_payload", postgresql.JSONB(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )
        op.create_index("idx_responses_source", "survey_responses", ["source"])
        op.create_index("idx_responses_user_id", "survey_responses", ["user_id"])
        op.create_index("idx_responses_consent", "survey_responses", ["consent"])
        op.create_index("idx_responses_created", "survey_responses", ["created_at"])


def downgrade() -> None:
    if _table_exists("survey_responses"):
        op.drop_table("survey_responses")
    if _table_exists("survey_sources"):
        op.drop_table("survey_sources")
