"""Prescriptions and FEFO stock movement ledger."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "0010_pharmacy"
down_revision = "0009_billing"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "medicines",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("unit", sa.String(40), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "stock_lots",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("medicine_id", sa.Uuid(), sa.ForeignKey("medicines.id"), nullable=False),
        sa.Column("lot_number", sa.String(100), nullable=False),
        sa.Column("expires_on", sa.Date(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.UniqueConstraint("medicine_id", "lot_number"),
        sa.CheckConstraint("quantity >= 0"),
    )
    op.create_index("ix_stock_lots_medicine_id", "stock_lots", ["medicine_id"])
    op.create_table(
        "prescriptions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("visit_id", sa.Uuid(), sa.ForeignKey("visits.id"), unique=True, nullable=False),
        sa.Column("provider_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("patient_name", sa.String(200), nullable=False),
        sa.Column("allergies", sa.String(2000), nullable=False),
        sa.Column("items", JSONB(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("dispensed_at", sa.DateTime(timezone=True)),
        sa.Column("dispense_request", sa.Uuid(), unique=True),
    )
    op.create_table(
        "stock_movements",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("lot_id", sa.Uuid(), sa.ForeignKey("stock_lots.id"), nullable=False),
        sa.Column("prescription_id", sa.Uuid(), sa.ForeignKey("prescriptions.id")),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(1000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade():
    for table in ["stock_movements", "prescriptions", "stock_lots", "medicines"]:
        op.drop_table(table)
