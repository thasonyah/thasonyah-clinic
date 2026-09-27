"""Public self booking requests."""

import sqlalchemy as sa

from alembic import op

revision = "0018_public_booking_requests"
down_revision = "0017_patient_zodiac_fields"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "booking_requests",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("request_id", sa.Uuid(), nullable=False, unique=True),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(40), nullable=False),
        sa.Column("line_id", sa.String(120), nullable=False, server_default=""),
        sa.Column("service_id", sa.Uuid(), sa.ForeignKey("clinic_services.id")),
        sa.Column("service_name", sa.String(200), nullable=False),
        sa.Column("preferred_starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("preferred_ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("note", sa.String(1000), nullable=False, server_default=""),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("preferred_ends_at > preferred_starts_at"),
    )
    for column in ["preferred_starts_at", "status", "phone"]:
        op.create_index("ix_booking_requests_" + column, "booking_requests", [column])


def downgrade():
    op.drop_table("booking_requests")
