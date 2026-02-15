"""Database operations for OrbitMind telemetry storage."""

import os
import logging
from datetime import datetime
from typing import Optional
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def get_connection_string() -> str:
    """Get database connection string from environment."""
    url = os.getenv("TIMESCALE_SERVICE_URL")
    if not url:
        raise ValueError("TIMESCALE_SERVICE_URL not set in environment")
    return url


@contextmanager
def get_connection():
    """Context manager for database connections."""
    conn = psycopg2.connect(get_connection_string())
    try:
        yield conn
    finally:
        conn.close()


class TelemetryDB:
    """Database interface for telemetry data."""

    def __init__(self):
        self.conn: Optional[psycopg2.extensions.connection] = None
        self._connect()

    def _connect(self):
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(get_connection_string())
            self.conn.autocommit = False
            logger.info("Connected to TimescaleDB")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def reconnect(self):
        """Reconnect to database."""
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
        self._connect()

    def insert_telemetry(
        self,
        channel_id: str,
        value: float,
        iss_timestamp: str,
        receive_time: Optional[datetime] = None,
    ):
        """Insert a single telemetry row."""
        if receive_time is None:
            receive_time = datetime.utcnow()

        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO telemetry (time, channel_id, value, iss_timestamp)
                VALUES (%s, %s, %s, %s)
                """,
                (receive_time, channel_id, value, iss_timestamp),
            )
        self.conn.commit()

    def insert_telemetry_batch(self, rows: list[tuple]):
        """
        Insert multiple telemetry rows efficiently.

        Args:
            rows: List of (receive_time, channel_id, value, iss_timestamp) tuples
        """
        if not rows:
            return

        with self.conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO telemetry (time, channel_id, value, iss_timestamp)
                VALUES %s
                """,
                rows,
            )
        self.conn.commit()
        logger.debug(f"Inserted batch of {len(rows)} rows")

    def get_latest(self, channel_id: str) -> Optional[tuple]:
        """Get the most recent value for a channel."""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT time, value, iss_timestamp
                FROM telemetry
                WHERE channel_id = %s
                ORDER BY time DESC
                LIMIT 1
                """,
                (channel_id,),
            )
            return cur.fetchone()

    def get_row_count(self) -> int:
        """Get total number of telemetry rows."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM telemetry")
            result = cur.fetchone()
            return result[0] if result else 0

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
