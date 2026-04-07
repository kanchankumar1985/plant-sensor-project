-- Migration: Add video_path column to plant_snapshots table
-- This allows storing the video clip filename associated with each snapshot

ALTER TABLE plant_snapshots 
ADD COLUMN IF NOT EXISTS video_path TEXT;

-- Add comment
COMMENT ON COLUMN plant_snapshots.video_path IS 'Filename of video clip recorded with this snapshot (if temperature alert triggered)';
