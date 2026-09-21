"""Optimistic patient corrections and replacement of cancelled prescriptions."""

import sqlalchemy as sa

from alembic import op

revision = "0011_patient_version"
down_revision = "0010_pharmacy"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "patients", sa.Column("version", sa.Integer(), nullable=False, server_default="1")
    )
    op.drop_constraint("prescriptions_visit_id_key", "prescriptions", type_="unique")
    op.create_index(
        "uq_active_prescription_visit",
        "prescriptions",
        ["visit_id"],
        unique=True,
        postgresql_where=sa.text("status != 'cancelled'"),
    )


def downgrade():
    # A rollback cannot collapse replacement prescriptions without losing history.
    op.drop_index("uq_active_prescription_visit", table_name="prescriptions")
    op.create_unique_constraint("prescriptions_visit_id_key", "prescriptions", ["visit_id"])
    op.drop_column("patients", "version")
