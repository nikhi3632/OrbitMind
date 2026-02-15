#!/usr/bin/env python3
"""
Simple database migration runner.

Runs numbered SQL migration files in order, tracking which have been applied.

Usage:
    python scripts/migrate.py          # Run pending migrations
    python scripts/migrate.py --status # Show migration status
"""

import os
import sys
import argparse
import logging
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

# Setup
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def get_connection():
    """Get database connection."""
    url = os.getenv("TIMESCALE_SERVICE_URL")
    if not url:
        raise ValueError("TIMESCALE_SERVICE_URL not set")
    return psycopg2.connect(url)


def ensure_migrations_table(conn):
    """Create migrations tracking table if it doesn't exist."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
    conn.commit()


def get_applied_migrations(conn) -> set:
    """Get set of already-applied migration versions."""
    with conn.cursor() as cur:
        cur.execute("SELECT version FROM schema_migrations ORDER BY version")
        return {row[0] for row in cur.fetchall()}


def get_pending_migrations(applied: set) -> list:
    """Get list of migration files that haven't been applied yet."""
    if not MIGRATIONS_DIR.exists():
        return []

    migrations = []
    for f in sorted(MIGRATIONS_DIR.glob("*.sql")):
        version = f.stem  # e.g., "001_initial"
        if version not in applied:
            migrations.append((version, f))

    return migrations


def apply_migration(conn, version: str, path: Path):
    """Apply a single migration."""
    logger.info(f"Applying {version}...")

    sql = path.read_text()

    with conn.cursor() as cur:
        cur.execute(sql)
        cur.execute(
            "INSERT INTO schema_migrations (version) VALUES (%s)",
            (version,)
        )

    conn.commit()
    logger.info(f"  Done: {version}")


def run_migrations():
    """Run all pending migrations."""
    conn = get_connection()

    try:
        ensure_migrations_table(conn)
        applied = get_applied_migrations(conn)
        pending = get_pending_migrations(applied)

        if not pending:
            logger.info("No pending migrations.")
            return

        logger.info(f"Found {len(pending)} pending migration(s):\n")

        for version, path in pending:
            apply_migration(conn, version, path)

        logger.info(f"\nAll migrations applied successfully.")

    finally:
        conn.close()


def show_status():
    """Show current migration status."""
    conn = get_connection()

    try:
        ensure_migrations_table(conn)
        applied = get_applied_migrations(conn)
        pending = get_pending_migrations(applied)

        logger.info("Migration Status")
        logger.info("=" * 40)

        if applied:
            logger.info("\nApplied:")
            for v in sorted(applied):
                logger.info(f"  [x] {v}")

        if pending:
            logger.info("\nPending:")
            for version, _ in pending:
                logger.info(f"  [ ] {version}")

        if not applied and not pending:
            logger.info("\nNo migrations found.")

    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Run database migrations")
    parser.add_argument("--status", action="store_true", help="Show migration status")
    args = parser.parse_args()

    if args.status:
        show_status()
    else:
        run_migrations()


if __name__ == "__main__":
    main()
