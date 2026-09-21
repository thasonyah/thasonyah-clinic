"""Create a private PostgreSQL custom-format backup via the existing Docker runtime."""

import argparse
import os
import subprocess

from app.config import get_settings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--container", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    url = get_settings().sqlalchemy_url
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as target:
        result = subprocess.run(
            [
                "docker",
                "exec",
                args.container,
                "pg_dump",
                "-U",
                url.username,
                "-d",
                url.database,
                "--format=custom",
                "--no-owner",
                "--no-acl",
            ],
            stdout=target,
            stderr=subprocess.PIPE,
        )
    if result.returncode:
        os.unlink(args.output)
        raise SystemExit(
            "Backup failed; verify container/database access. No usable backup created."
        )
    print("Private PostgreSQL backup created. Verify restore before relying on this file.")


if __name__ == "__main__":
    main()
