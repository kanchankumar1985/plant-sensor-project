CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS sensor_readings (
    time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    device_id TEXT NOT NULL,
    temperature_c DOUBLE PRECISION NOT NULL,
    humidity_pct DOUBLE PRECISION NOT NULL,
    led_state INTEGER DEFAULT 0
);

SELECT create_hypertable('sensor_readings', by_range('time'), if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_sensor_readings_device_time
ON sensor_readings (device_id, time DESC);
