"""Seed the approved service snapshot only; never overwrite edited catalog entries."""

import json
import uuid
from pathlib import Path

from sqlalchemy.dialects.postgresql import insert

from app.database import SessionLocal
from app.models.catalog import ClinicService


def main():
    rows = json.loads(Path(__file__).with_name("service_seed.json").read_text())
    with SessionLocal() as db:
        for row in rows:
            db.execute(
                insert(ClinicService)
                .values(
                    id=uuid.uuid5(uuid.NAMESPACE_URL, "thasonyah-service:" + row["code"]),
                    name=row["name"],
                    price=row["price"],
                    minutes=row["minutes"],
                    active=True,
                    version=1,
                )
                .on_conflict_do_nothing()
            )
        db.commit()
    print("Service seed completed; existing entries preserved. No patients or users created.")


if __name__ == "__main__":
    main()
