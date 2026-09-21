"""Append-only receipts/refunds; migrate legacy full payments without inventing actors."""

import sqlalchemy as sa

from alembic import op

revision = "0012_payment_ledger"
down_revision = "0011_patient_version"
branch_labels = None
depends_on = None


def upgrade():
    for name in ["payment_receipts", "payment_refunds"]:
        op.create_table(
            name,
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("number", sa.Integer(), sa.Identity(), nullable=False, unique=True),
            sa.Column("invoice_id", sa.Uuid(), sa.ForeignKey("invoices.id"), nullable=False),
            sa.Column("request_id", sa.Uuid(), nullable=False, unique=True),
            sa.Column("amount", sa.Numeric(12, 2), nullable=False),
            sa.Column("method", sa.String(20), nullable=False),
            sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id")),
            sa.Column("reason", sa.String(1000), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.CheckConstraint("amount > 0"),
        )
        op.create_index("ix_" + name + "_invoice_id", name, ["invoice_id"])
    op.execute("""INSERT INTO payment_receipts
        (id,invoice_id,request_id,amount,method,reason,created_at)
        SELECT id,id,COALESCE(payment_request,id),total,COALESCE(payment_method,'cash'),
               'Migrated legacy receipt; actor not recorded',paid_at
        FROM invoices WHERE paid_at IS NOT NULL AND total > 0""")
    op.execute("""INSERT INTO payment_refunds
        (id,invoice_id,request_id,amount,method,reason,created_at)
        SELECT id,id,COALESCE(refund_request,id),total,COALESCE(payment_method,'cash'),
               COALESCE(refund_reason,'Migrated legacy refund'),refunded_at
        FROM invoices WHERE refunded_at IS NOT NULL AND total > 0""")


def downgrade():
    raise RuntimeError(
        "Payment ledger contains financial history; restore a verified backup instead."
    )
