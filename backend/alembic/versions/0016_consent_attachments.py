"""Consent attachment storage."""

import sqlalchemy as sa

from alembic import op

revision = "0016_consent_attachments"
down_revision = "0015_cash_close"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "consent_attachments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("visit_id", sa.Uuid(), sa.ForeignKey("visits.id")),
        sa.Column("filename", sa.String(240), nullable=False),
        sa.Column("content_type", sa.String(120), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("note", sa.String(1000), nullable=False, server_default=""),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.Column("uploaded_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("size_bytes > 0"),
        sa.CheckConstraint("size_bytes <= 5242880"),
    )
    op.create_index("ix_consent_attachments_patient_id", "consent_attachments", ["patient_id"])
    op.create_index("ix_consent_attachments_visit_id", "consent_attachments", ["visit_id"])
    op.create_index("ix_consent_attachments_sha256", "consent_attachments", ["sha256"])


def downgrade():
    raise RuntimeError("Consent attachments may contain clinical evidence; restore a backup.")
