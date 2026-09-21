"""Single-clinic patient registry and assigned practitioner visit drafts."""

import sqlalchemy as sa

from alembic import op

revision = "0004_records"
down_revision = "0003_catalog"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "patients",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("birth_date", sa.Date()),
        sa.Column("phone", sa.String(40), nullable=False),
        sa.Column("provider_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
    )
    op.create_index("ix_patients_provider_id", "patients", ["provider_id"])
    op.create_table(
        "visits",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("provider_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("chief_complaint", sa.String(2000), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("signed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_visits_patient_id", "visits", ["patient_id"])


def downgrade():
    op.drop_table("visits")
    op.drop_table("patients")
