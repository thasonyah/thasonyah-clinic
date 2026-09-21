"""Restore into a new disposable DB; never overwrite an existing DB."""

import argparse
import json
import subprocess
import uuid
from pathlib import Path

from app.config import get_settings

TABLES = (
    "users",
    "login_sessions",
    "password_resets",
    "clinic_services",
    "resources",
    "patients",
    "visits",
    "visit_amendments",
    "consent_attachments",
    "appointments",
    "invoices",
    "payment_receipts",
    "payment_refunds",
    "cash_closes",
    "dispense_batches",
    "medicines",
    "stock_lots",
    "stock_movements",
    "prescriptions",
    "audit_events",
    "alembic_version",
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--container", required=True)
    parser.add_argument("--backup", required=True)
    args = parser.parse_args()
    url = get_settings().sqlalchemy_url
    target = "clinic_restore_" + uuid.uuid4().hex[:12] + "_test"
    base = ["docker", "exec", "-i", args.container]

    def run(command, data=None):
        result = subprocess.run(
            base + command, input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if result.returncode:
            raise SystemExit(
                "Restore check failed; inspect target " + target + " in the specified container."
            )
        return result.stdout.decode().strip()

    run(["createdb", "-U", url.username, target])
    run(
        [
            "pg_restore",
            "-U",
            url.username,
            "-d",
            target,
            "--no-owner",
            "--no-acl",
            "--exit-on-error",
        ],
        Path(args.backup).read_bytes(),
    )

    def counts(database):
        return {
            table: int(
                run(
                    [
                        "psql",
                        "-U",
                        url.username,
                        "-d",
                        database,
                        "-Atc",
                        f"SELECT count(*) FROM {table}",
                    ]
                )
            )
            for table in TABLES
        }

    original = counts(url.database)
    restored = counts(target)
    print(
        json.dumps(
            {
                "source": url.database,
                "restored_database": target,
                "counts": restored,
                "row_counts_match": original == restored,
            },
            indent=2,
        )
    )
    if original != restored:
        raise SystemExit(
            "Row counts differ. Source may have changed; inspect before accepting backup."
        )
    print("Restore and table-count comparison passed. Restored DB retained for inspection.")


if __name__ == "__main__":
    main()
