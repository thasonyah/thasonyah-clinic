"""Patient zodiac calculation inputs."""

from alembic import op
import sqlalchemy as sa

revision = "0017_patient_zodiac_fields"
down_revision = "0016_consent_attachments"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("patients", sa.Column("birth_lunar_month", sa.Integer(), nullable=True))
    op.add_column("patients", sa.Column("birth_lunar_phase", sa.String(20), nullable=True))
    op.add_column("patients", sa.Column("gestation_months", sa.Integer(), nullable=True))
    op.create_check_constraint(
        "ck_patients_birth_lunar_month_range",
        "patients",
        "birth_lunar_month IS NULL OR birth_lunar_month BETWEEN 1 AND 12",
    )
    op.create_check_constraint(
        "ck_patients_birth_lunar_phase_values",
        "patients",
        "birth_lunar_phase IS NULL OR birth_lunar_phase IN ('ข้างขึ้น', 'ข้างแรม')",
    )
    op.create_check_constraint(
        "ck_patients_gestation_months_range",
        "patients",
        "gestation_months IS NULL OR gestation_months BETWEEN 1 AND 12",
    )


def downgrade():
    op.drop_constraint("ck_patients_gestation_months_range", "patients", type_="check")
    op.drop_constraint("ck_patients_birth_lunar_phase_values", "patients", type_="check")
    op.drop_constraint("ck_patients_birth_lunar_month_range", "patients", type_="check")
    op.drop_column("patients", "gestation_months")
    op.drop_column("patients", "birth_lunar_phase")
    op.drop_column("patients", "birth_lunar_month")
