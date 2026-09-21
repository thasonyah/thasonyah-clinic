"""Persistent service catalog with optimistic concurrency."""

import sqlalchemy as sa

from alembic import op

revision = "0003_catalog"
down_revision = "0002_identity"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "clinic_services",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False, unique=True),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("minutes", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint("price >= 0 AND minutes > 0 AND version > 0"),
    )


def downgrade():
    op.drop_table("clinic_services")
