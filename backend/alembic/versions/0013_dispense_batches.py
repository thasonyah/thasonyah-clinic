"""Idempotent partial dispensing and traceable batches."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "0013_dispense_batches"
down_revision = "0012_payment_ledger"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "dispense_batches",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("prescription_id", sa.Uuid(), sa.ForeignKey("prescriptions.id"), nullable=False),
        sa.Column("quantities", JSONB(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.add_column(
        "stock_movements", sa.Column("batch_id", sa.Uuid(), sa.ForeignKey("dispense_batches.id"))
    )
    op.execute("""INSERT INTO dispense_batches (id,prescription_id,quantities,created_at)
        SELECT dispense_request,id,'{}'::jsonb,dispensed_at FROM prescriptions
        WHERE dispense_request IS NOT NULL AND dispensed_at IS NOT NULL""")
    op.execute("""UPDATE stock_movements m SET batch_id=p.dispense_request FROM prescriptions p
        WHERE m.prescription_id=p.id AND p.dispense_request IS NOT NULL""")


def downgrade():
    raise RuntimeError(
        "Dispense batches preserve fulfillment history; restore a verified backup instead."
    )
