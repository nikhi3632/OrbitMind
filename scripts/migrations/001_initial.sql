-- Migration: 001_initial
-- Description: Create telemetry hypertable and indexes

-- Create telemetry table
CREATE TABLE IF NOT EXISTS telemetry (
    time            TIMESTAMPTZ NOT NULL,
    channel_id      TEXT NOT NULL,
    value           DOUBLE PRECISION,
    iss_timestamp   TEXT
);

-- Convert to hypertable (TimescaleDB)
SELECT create_hypertable('telemetry', 'time', if_not_exists => TRUE);

-- Create index for fast lookups by channel
CREATE INDEX IF NOT EXISTS idx_telemetry_channel_time
ON telemetry (channel_id, time DESC);

-- Enable compression for older data
ALTER TABLE telemetry SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'channel_id'
);

-- Compress chunks older than 7 days automatically
SELECT add_compression_policy('telemetry', INTERVAL '7 days', if_not_exists => TRUE);
