"""Users and revocable login sessions."""

import sqlalchemy as sa

from alembic import op

revision = "0002_identity"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "login_sessions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_login_sessions_user_id", "login_sessions", ["user_id"])


def downgrade():
    op.drop_table("login_sessions")
    op.drop_table("users")
