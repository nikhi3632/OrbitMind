#!/usr/bin/env python3
"""
OrbitMind Telemetry Collector Entry Point

Connects to ISS Lightstreamer feed and stores telemetry to TimescaleDB.
Runs forever until killed.

Usage:
    python scripts/run_collector.py
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.collector import TelemetryCollector


def setup_logging():
    """Configure logging for the collector."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("OrbitMind Telemetry Collector")
    logger.info("=" * 60)

    collector = TelemetryCollector()

    try:
        collector.start()
    except Exception as e:
        logger.error(f"Collector crashed: {e}")
        raise
    finally:
        collector.stop()


if __name__ == "__main__":
    main()
