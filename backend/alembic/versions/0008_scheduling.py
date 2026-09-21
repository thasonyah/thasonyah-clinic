"""Appointments, queue and shared rooms/beds."""

import sqlalchemy as sa

from alembic import op

revision = "0008_scheduling"
down_revision = "0007_opd"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "resources",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False, unique=True),
        sa.Column("active", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "appointments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("request_id", sa.Uuid(), nullable=False, unique=True),
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("provider_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("resource_id", sa.Uuid(), sa.ForeignKey("resources.id")),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.CheckConstraint("ends_at > starts_at"),
    )
    for col in ["patient_id", "provider_id", "starts_at"]:
        op.create_index("ix_appointments_" + col, "appointments", [col])


def downgrade():
    op.drop_table("appointments")
    op.drop_table("resources")
