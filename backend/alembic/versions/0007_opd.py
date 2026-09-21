"""Structured OPD and append-only signed record amendments."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "0007_opd"
down_revision = "0006_audit"
branch_labels = None
depends_on = None


def upgrade():
    for name, length in [("address", 2000), ("allergies", 2000), ("emergency_contact", 500)]:
        op.add_column(
            "patients", sa.Column(name, sa.String(length), nullable=False, server_default="")
        )
    op.add_column("visits", sa.Column("opd", JSONB(), nullable=False, server_default="{}"))
    op.create_table(
        "visit_amendments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("visit_id", sa.Uuid(), sa.ForeignKey("visits.id"), nullable=False),
        sa.Column("author_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reason", sa.String(1000), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_visit_amendments_visit_id", "visit_amendments", ["visit_id"])


def downgrade():
    op.drop_table("visit_amendments")
    op.drop_column("visits", "opd")
    for name in ["emergency_contact", "allergies", "address"]:
        op.drop_column("patients", name)
