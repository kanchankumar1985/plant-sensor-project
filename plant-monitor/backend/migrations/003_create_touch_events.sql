-- Migration: Create touch_events hypertable
-- Description: Store capacitive touch sensor events with timestamp

-- Create touch_events table
CREATE TABLE IF NOT EXISTS touch_events (
    id SERIAL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    device_id TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('TOUCHED', 'NOT_TOUCHED')),
    PRIMARY KEY (timestamp, id)
);

-- Convert to hypertable (partitioned by time)
SELECT create_hypertable('touch_events', 'timestamp', if_not_exists => TRUE);

-- Create index on timestamp for faster queries
CREATE INDEX IF NOT EXISTS idx_touch_events_timestamp ON touch_events (timestamp DESC);

-- Create index on device_id for filtering
CREATE INDEX IF NOT EXISTS idx_touch_events_device_id ON touch_events (device_id, timestamp DESC);

-- Create index on state for filtering
CREATE INDEX IF NOT EXISTS idx_touch_events_state ON touch_events (state, timestamp DESC);

-- Add retention policy: keep data for 90 days
SELECT add_retention_policy('touch_events', INTERVAL '90 days', if_not_exists => TRUE);

-- Grant permissions
GRANT SELECT, INSERT ON touch_events TO plant_monitor_user;
GRANT USAGE, SELECT ON SEQUENCE touch_events_id_seq TO plant_monitor_user;

-- Create view for latest touch state per device
CREATE OR REPLACE VIEW latest_touch_state AS
SELECT DISTINCT ON (device_id)
    device_id,
    timestamp,
    state
FROM touch_events
ORDER BY device_id, timestamp DESC;

GRANT SELECT ON latest_touch_state TO plant_monitor_user;

COMMENT ON TABLE touch_events IS 'Capacitive touch sensor events from TTP223 module';
COMMENT ON COLUMN touch_events.state IS 'Touch state: TOUCHED or NOT_TOUCHED';
