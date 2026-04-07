-- Migration: Add person detection columns to plant_snapshots table
-- This migration is safe to run multiple times

-- Add id column as primary key if not exists
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'plant_snapshots' AND column_name = 'id'
    ) THEN
        ALTER TABLE plant_snapshots ADD COLUMN id SERIAL PRIMARY KEY;
    END IF;
END $$;

-- Add person_detected column
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'plant_snapshots' AND column_name = 'person_detected'
    ) THEN
        ALTER TABLE plant_snapshots ADD COLUMN person_detected BOOLEAN DEFAULT FALSE;
    END IF;
END $$;

-- Add person_count column
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'plant_snapshots' AND column_name = 'person_count'
    ) THEN
        ALTER TABLE plant_snapshots ADD COLUMN person_count INTEGER DEFAULT 0;
    END IF;
END $$;

-- Add detection_metadata column (JSONB for efficient querying)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'plant_snapshots' AND column_name = 'detection_metadata'
    ) THEN
        ALTER TABLE plant_snapshots ADD COLUMN detection_metadata JSONB;
    END IF;
END $$;

-- Add boxed_image_path column
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'plant_snapshots' AND column_name = 'boxed_image_path'
    ) THEN
        ALTER TABLE plant_snapshots ADD COLUMN boxed_image_path TEXT;
    END IF;
END $$;

-- Create index on person_detected for faster queries
CREATE INDEX IF NOT EXISTS idx_plant_snapshots_person_detected 
ON plant_snapshots(person_detected);

-- Create index on time for faster queries
CREATE INDEX IF NOT EXISTS idx_plant_snapshots_time 
ON plant_snapshots(time DESC);

-- Verify migration
SELECT 
    column_name, 
    data_type, 
    is_nullable 
FROM information_schema.columns 
WHERE table_name = 'plant_snapshots'
ORDER BY ordinal_position;
