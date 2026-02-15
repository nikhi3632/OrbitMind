#!/usr/bin/env python3
"""Drop all tables and re-run migrations."""

import os
import sys

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def drop_tables():
    """Drop all tables."""
    conn = psycopg2.connect(os.getenv("TIMESCALE_SERVICE_URL"))
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS telemetry CASCADE")
    cur.execute("DROP TABLE IF EXISTS schema_migrations CASCADE")
    conn.commit()
    conn.close()
    print("Tables dropped.")


def main():
    confirm = input("WARNING: This will delete all data and recreate tables! Are you sure? [y/N] ")
    if confirm.lower() != "y":
        print("Aborted.")
        sys.exit(1)

    drop_tables()

    # Run migrations
    from migrate import run_migrations
    run_migrations()

    print("Database reset complete.")


if __name__ == "__main__":
    main()
