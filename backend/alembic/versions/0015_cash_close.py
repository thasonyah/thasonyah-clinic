"""Daily cash close records."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0015_cash_close"
down_revision = "0014_stock_adjustments"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cash_closes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("day", sa.Date(), nullable=False, unique=True),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id")),
        sa.Column("expected_cash", sa.Numeric(12, 2), nullable=False),
        sa.Column("counted_cash", sa.Numeric(12, 2), nullable=False),
        sa.Column("difference", sa.Numeric(12, 2), nullable=False),
        sa.Column("note", sa.String(1000), nullable=False, server_default=""),
        sa.Column("channels", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("expected_cash >= 0"),
        sa.CheckConstraint("counted_cash >= 0"),
    )
    op.create_index("ix_cash_closes_day", "cash_closes", ["day"])


def downgrade():
    raise RuntimeError("Cash close history is financial evidence; restore a verified backup.")
