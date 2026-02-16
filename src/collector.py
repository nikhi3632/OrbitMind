"""ISS Telemetry Collector - streams data from Lightstreamer to TimescaleDB."""

import asyncio
import logging
import time
import threading
from datetime import datetime, timezone
from typing import Optional

from lightstreamer.client import (
    LightstreamerClient,
    Subscription,
    SubscriptionListener,
    ClientListener,
)

from src.config import (
    LIGHTSTREAMER_SERVER,
    LIGHTSTREAMER_ADAPTER,
    CHANNELS,
    DB_BATCH_SIZE,
    DB_FLUSH_INTERVAL,
    STALE_CONNECTION_TIMEOUT,
)
from src.db import TelemetryDB

logger = logging.getLogger(__name__)


class TelemetryListener(SubscriptionListener):
    """Handles incoming telemetry updates from Lightstreamer."""

    def __init__(self, collector: "TelemetryCollector"):
        self.collector = collector

    def onItemUpdate(self, update):
        """Called when a telemetry value is updated."""
        try:
            channel_id = update.getItemName()
            value_str = update.getValue("Value")
            iss_timestamp = update.getValue("TimeStamp")

            if value_str is None or value_str == "":
                return

            try:
                value = float(value_str)
            except ValueError:
                logger.debug(f"Non-numeric value for {channel_id}: {value_str}")
                return

            self.collector.on_telemetry(channel_id, value, iss_timestamp)

        except Exception as e:
            logger.error(f"Error processing update: {e}")

    def onSubscription(self):
        logger.info("Subscription active")

    def onUnsubscription(self):
        logger.info("Subscription inactive")

    def onSubscriptionError(self, code, message):
        logger.error(f"Subscription error {code}: {message}")


class ConnectionListener(ClientListener):
    """Handles Lightstreamer connection state changes."""

    def __init__(self, collector: "TelemetryCollector"):
        self.collector = collector

    def onStatusChange(self, status):
        logger.info(f"Connection status: {status}")
        if status.startswith("CONNECTED"):
            self.collector.on_connected()
        elif status == "STALLED":
            logger.warning("Connection stalled - waiting for keepalive or data")
        elif status.startswith("DISCONNECTED"):
            self.collector.connected = False

    def onServerError(self, code, message):
        logger.error(f"Server error {code}: {message}")


class TelemetryCollector:
    """
    Main collector class - connects to Lightstreamer and stores telemetry.

    Uses asyncio to keep the event loop alive for the Lightstreamer client.
    """

    def __init__(self):
        self.client: Optional[LightstreamerClient] = None
        self.subscription: Optional[Subscription] = None
        self.db: Optional[TelemetryDB] = None

        # Batch buffer for DB writes (thread-safe)
        self.buffer: list[tuple] = []
        self.buffer_lock = threading.Lock()
        self.last_flush_time = 0.0

        # Connection state
        self.connected = False
        self.running = False
        self.last_data_time = 0.0

        # Stats
        self.total_received = 0
        self.total_inserted = 0

    def start(self):
        """Start the collector - runs forever using asyncio."""
        asyncio.run(self._async_main())

    async def _async_main(self):
        """Async main entry point."""
        logger.info("Starting OrbitMind Telemetry Collector")

        # Initialize database
        self.db = TelemetryDB()

        self.running = True
        self.last_flush_time = time.time()
        self.last_data_time = time.time()

        # Connect to Lightstreamer
        self._connect()

        # Main async loop - keeps event loop alive for Lightstreamer's aiohttp
        last_stats_time = time.time()
        try:
            while self.running:
                await asyncio.sleep(0.1)  # Short sleep to keep event loop responsive

                now = time.time()

                # Periodic flush
                if now - self.last_flush_time >= DB_FLUSH_INTERVAL:
                    with self.buffer_lock:
                        self._flush_buffer()

                # Periodic stats (every 30 seconds)
                if now - last_stats_time >= 30:
                    self._log_stats()
                    last_stats_time = now

                # Check for stale connection
                if now - self.last_data_time >= STALE_CONNECTION_TIMEOUT:
                    logger.warning(f"No data received for {STALE_CONNECTION_TIMEOUT}s, reconnecting...")
                    self._reconnect()

        except asyncio.CancelledError:
            logger.info("Shutdown requested")
        finally:
            self._shutdown()

    def _shutdown(self):
        """Clean shutdown."""
        logger.info("Stopping collector...")
        self.running = False

        # Flush remaining buffer
        with self.buffer_lock:
            self._flush_buffer()

        # Disconnect
        if self.client:
            self.client.disconnect()

        # Close DB
        if self.db:
            self.db.close()

        logger.info(f"Collector stopped. Total received: {self.total_received}, inserted: {self.total_inserted}")

    def stop(self):
        """Stop the collector."""
        self.running = False

    def _connect(self):
        """Connect to Lightstreamer."""
        logger.info(f"Connecting to {LIGHTSTREAMER_SERVER}...")

        self.client = LightstreamerClient(LIGHTSTREAMER_SERVER, LIGHTSTREAMER_ADAPTER)
        self.client.addListener(ConnectionListener(self))

        # Configure connection options for reliability
        options = self.client.connectionOptions
        options.setReverseHeartbeatInterval(30000)  # Client pings server every 30s
        options.setStalledTimeout(5000)  # Enter STALLED after 5s of silence
        options.setReconnectTimeout(10000)  # Reconnect after 10s in STALLED

        # Create subscription
        self.subscription = Subscription(
            mode="MERGE",
            items=CHANNELS,
            fields=["Value", "TimeStamp"],
        )
        self.subscription.setRequestedSnapshot("yes")
        self.subscription.setRequestedMaxFrequency("unlimited")
        self.subscription.addListener(TelemetryListener(self))

        # Subscribe and connect
        self.client.subscribe(self.subscription)
        self.client.connect()

    def _reconnect(self):
        """Disconnect and reconnect to Lightstreamer."""
        self.connected = False

        # Disconnect existing client
        if self.client:
            try:
                self.client.disconnect()
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")

        # Reset and reconnect
        self.last_data_time = time.time()
        self._connect()

    def on_connected(self):
        """Called when connection is established."""
        self.connected = True
        self.last_data_time = time.time()
        logger.info(f"Connected! Subscribed to {len(CHANNELS)} channels")

    def on_telemetry(self, channel_id: str, value: float, iss_timestamp: str):
        """Called when a telemetry update is received (from Lightstreamer thread)."""
        receive_time = datetime.now(timezone.utc)

        with self.buffer_lock:
            self.buffer.append((receive_time, channel_id, value, iss_timestamp))
            self.total_received += 1
            self.last_data_time = time.time()

            # Flush if buffer is full
            if len(self.buffer) >= DB_BATCH_SIZE:
                self._flush_buffer()

    def _flush_buffer(self):
        """Flush buffer to database. Must be called with buffer_lock held."""
        if not self.buffer:
            return

        rows = self.buffer.copy()
        self.buffer.clear()
        self.last_flush_time = time.time()

        try:
            self.db.insert_telemetry_batch(rows)
            self.total_inserted += len(rows)
        except Exception as e:
            logger.error(f"Failed to insert batch: {e}")
            try:
                self.db.reconnect()
                self.db.insert_telemetry_batch(rows)
                self.total_inserted += len(rows)
            except Exception as e2:
                logger.error(f"Retry failed, lost {len(rows)} rows: {e2}")

    def _log_stats(self):
        """Log collector statistics."""
        logger.info(
            f"Stats: received={self.total_received}, "
            f"inserted={self.total_inserted}, "
            f"buffer={len(self.buffer)}, "
            f"connected={self.connected}"
        )
