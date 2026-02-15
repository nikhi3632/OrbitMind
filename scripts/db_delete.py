#!/usr/bin/env python3
"""Drop all tables (without re-running migrations)."""

import os
import sys

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def main():
    confirm = input("WARNING: This will delete all tables! Are you sure? [y/N] ")
    if confirm.lower() != "y":
        print("Aborted.")
        sys.exit(1)

    conn = psycopg2.connect(os.getenv("TIMESCALE_SERVICE_URL"))
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS telemetry CASCADE")
    cur.execute("DROP TABLE IF EXISTS schema_migrations CASCADE")
    conn.commit()
    conn.close()

    print("All tables dropped.")


if __name__ == "__main__":
    main()
