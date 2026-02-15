#!/usr/bin/env python3
"""Show telemetry row counts and time range."""

import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def main():
    conn = psycopg2.connect(os.getenv("TIMESCALE_SERVICE_URL"))
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM telemetry")
    count = cur.fetchone()[0]

    cur.execute("SELECT MIN(time), MAX(time) FROM telemetry")
    times = cur.fetchone()

    print(f"Rows: {count:,}")
    print(f"From: {times[0]}")
    print(f"To:   {times[1]}")

    conn.close()


if __name__ == "__main__":
    main()
