"""Count/return/damage corrections with idempotent movement references."""

import sqlalchemy as sa

from alembic import op

revision = "0014_stock_adjustments"
down_revision = "0013_dispense_batches"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("stock_movements", sa.Column("request_id", sa.Uuid(), unique=True))
    op.add_column("stock_movements", sa.Column("balance", sa.Integer()))


def downgrade():
    op.drop_column("stock_movements", "balance")
    op.drop_column("stock_movements", "request_id")
