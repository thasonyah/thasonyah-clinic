"""Snapshot service charges, receipts and full refunds."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "0009_billing"
down_revision = "0008_scheduling"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "invoices",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("number", sa.Integer(), sa.Identity(), unique=True, nullable=False),
        sa.Column("visit_id", sa.Uuid(), sa.ForeignKey("visits.id"), unique=True, nullable=False),
        sa.Column("patient_name", sa.String(200), nullable=False),
        sa.Column("provider_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("items", JSONB(), nullable=False),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True)),
        sa.Column("payment_request", sa.Uuid(), unique=True),
        sa.Column("payment_method", sa.String(20)),
        sa.Column("refunded_at", sa.DateTime(timezone=True)),
        sa.Column("refund_request", sa.Uuid(), unique=True),
        sa.Column("refund_reason", sa.String(1000)),
        sa.CheckConstraint("total >= 0"),
    )


def downgrade():
    op.drop_table("invoices")
