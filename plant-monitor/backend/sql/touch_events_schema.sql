-- =====================================================
-- Touch Events Table Schema Validation and Migration
-- =====================================================

-- 1. INSPECT EXISTING TABLE
-- Run this first to see current schema
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'touch_events'
ORDER BY ordinal_position;

-- 2. CHECK IF TABLE EXISTS
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'touch_events'
);

-- =====================================================
-- 3. CREATE TABLE IF NOT EXISTS
-- =====================================================
-- This is safe to run - will only create if missing

CREATE TABLE IF NOT EXISTS touch_events (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    state VARCHAR(20) NOT NULL CHECK (state IN ('TOUCHED', 'NOT_TOUCHED'))
);

-- Create index on timestamp for faster queries
CREATE INDEX IF NOT EXISTS idx_touch_events_timestamp 
ON touch_events (timestamp DESC);

-- =====================================================
-- 4. ADD MISSING COLUMNS (Safe Migration)
-- =====================================================
-- These will only add columns if they don't exist

-- Add timestamp column if missing
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'touch_events' AND column_name = 'timestamp'
    ) THEN
        ALTER TABLE touch_events 
        ADD COLUMN timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW();
    END IF;
END $$;

-- Add state column if missing
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'touch_events' AND column_name = 'state'
    ) THEN
        ALTER TABLE touch_events 
        ADD COLUMN state VARCHAR(20) NOT NULL DEFAULT 'NOT_TOUCHED';
    END IF;
END $$;

-- Add CHECK constraint if missing
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'touch_events_state_check'
    ) THEN
        ALTER TABLE touch_events 
        ADD CONSTRAINT touch_events_state_check 
        CHECK (state IN ('TOUCHED', 'NOT_TOUCHED'));
    END IF;
END $$;

-- =====================================================
-- 5. CONVERT TO HYPERTABLE (TimescaleDB)
-- =====================================================
-- Only run this if TimescaleDB extension is installed
-- This optimizes time-series queries

-- Check if TimescaleDB is available
SELECT * FROM pg_available_extensions WHERE name = 'timescaledb';

-- Create hypertable (safe - will skip if already a hypertable)
SELECT create_hypertable(
    'touch_events', 
    'timestamp',
    if_not_exists => TRUE,
    migrate_data => TRUE
);

-- =====================================================
-- 6. VERIFY FINAL SCHEMA
-- =====================================================

-- Check table structure
\d touch_events

-- Check recent data
SELECT * FROM touch_events ORDER BY timestamp DESC LIMIT 10;

-- Check row count
SELECT COUNT(*) as total_events FROM touch_events;

-- Check state distribution
SELECT state, COUNT(*) as count 
FROM touch_events 
GROUP BY state;

-- =====================================================
-- 7. TEST QUERIES
-- =====================================================

-- Insert test event
INSERT INTO touch_events (timestamp, state) 
VALUES (NOW(), 'TOUCHED')
RETURNING *;

-- Get latest event
SELECT * FROM touch_events 
ORDER BY timestamp DESC 
LIMIT 1;

-- Get events from last hour
SELECT * FROM touch_events 
WHERE timestamp > NOW() - INTERVAL '1 hour'
ORDER BY timestamp DESC;

-- =====================================================
-- 8. CLEANUP (Optional)
-- =====================================================

-- Delete old test data (uncomment if needed)
-- DELETE FROM touch_events WHERE state = 'TOUCHED' AND timestamp < NOW() - INTERVAL '1 day';

-- Drop table completely (DANGER - uncomment only if you want to start fresh)
-- DROP TABLE IF EXISTS touch_events CASCADE;
