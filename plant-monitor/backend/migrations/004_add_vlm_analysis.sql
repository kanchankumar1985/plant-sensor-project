-- Migration: Add VLM (Vision-Language Model) analysis support
-- Adds columns and tables for AI reasoning layer

-- Add VLM analysis columns to plant_snapshots table
DO $$ 
BEGIN
    -- VLM analysis summary
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'plant_snapshots' AND column_name = 'vlm_summary'
    ) THEN
        ALTER TABLE plant_snapshots ADD COLUMN vlm_summary TEXT;
        COMMENT ON COLUMN plant_snapshots.vlm_summary IS 'AI-generated summary of the image';
    END IF;

    -- VLM structured analysis (JSONB for efficient querying)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'plant_snapshots' AND column_name = 'vlm_analysis'
    ) THEN
        ALTER TABLE plant_snapshots ADD COLUMN vlm_analysis JSONB;
        COMMENT ON COLUMN plant_snapshots.vlm_analysis IS 'Structured VLM analysis results';
    END IF;

    -- Plant visibility flag
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'plant_snapshots' AND column_name = 'plant_visible'
    ) THEN
        ALTER TABLE plant_snapshots ADD COLUMN plant_visible BOOLEAN DEFAULT TRUE;
    END IF;

    -- Plant occlusion flag
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'plant_snapshots' AND column_name = 'plant_occluded'
    ) THEN
        ALTER TABLE plant_snapshots ADD COLUMN plant_occluded BOOLEAN DEFAULT FALSE;
    END IF;

    -- Plant health assessment
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'plant_snapshots' AND column_name = 'plant_health_guess'
    ) THEN
        ALTER TABLE plant_snapshots ADD COLUMN plant_health_guess TEXT;
        COMMENT ON COLUMN plant_snapshots.plant_health_guess IS 'VLM guess: healthy, yellowing, drooping, wilting, unknown';
    END IF;

    -- Yellowing indicator
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'plant_snapshots' AND column_name = 'yellowing_visible'
    ) THEN
        ALTER TABLE plant_snapshots ADD COLUMN yellowing_visible BOOLEAN DEFAULT FALSE;
    END IF;

    -- Drooping indicator
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'plant_snapshots' AND column_name = 'drooping_visible'
    ) THEN
        ALTER TABLE plant_snapshots ADD COLUMN drooping_visible BOOLEAN DEFAULT FALSE;
    END IF;

    -- Wilting indicator
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'plant_snapshots' AND column_name = 'wilting_visible'
    ) THEN
        ALTER TABLE plant_snapshots ADD COLUMN wilting_visible BOOLEAN DEFAULT FALSE;
    END IF;

    -- Image quality assessment
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'plant_snapshots' AND column_name = 'image_quality'
    ) THEN
        ALTER TABLE plant_snapshots ADD COLUMN image_quality TEXT;
        COMMENT ON COLUMN plant_snapshots.image_quality IS 'good, poor, dark, blurry, unknown';
    END IF;

    -- Analysis status
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'plant_snapshots' AND column_name = 'analysis_status'
    ) THEN
        ALTER TABLE plant_snapshots ADD COLUMN analysis_status TEXT DEFAULT 'pending';
        COMMENT ON COLUMN plant_snapshots.analysis_status IS 'pending, processing, completed, failed';
    END IF;

    -- Analysis error message
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'plant_snapshots' AND column_name = 'analysis_error'
    ) THEN
        ALTER TABLE plant_snapshots ADD COLUMN analysis_error TEXT;
    END IF;

    -- Analysis reliability metadata
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'plant_snapshots' AND column_name = 'analysis_reliability'
    ) THEN
        ALTER TABLE plant_snapshots ADD COLUMN analysis_reliability JSONB;
        COMMENT ON COLUMN plant_snapshots.analysis_reliability IS 'Reliability assessment from rules engine';
    END IF;

    -- VLM model used
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'plant_snapshots' AND column_name = 'vlm_model'
    ) THEN
        ALTER TABLE plant_snapshots ADD COLUMN vlm_model TEXT;
    END IF;

    -- Analysis timestamp
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'plant_snapshots' AND column_name = 'analyzed_at'
    ) THEN
        ALTER TABLE plant_snapshots ADD COLUMN analyzed_at TIMESTAMPTZ;
    END IF;
END $$;

-- Create video_analysis table for video event analysis
CREATE TABLE IF NOT EXISTS video_analysis (
    id SERIAL PRIMARY KEY,
    time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    video_path TEXT NOT NULL,
    snapshot_id INTEGER REFERENCES plant_snapshots(id),
    
    -- VLM analysis
    vlm_summary TEXT,
    vlm_analysis JSONB,
    
    -- Event detection
    person_entered BOOLEAN DEFAULT FALSE,
    person_left BOOLEAN DEFAULT FALSE,
    person_stayed BOOLEAN DEFAULT FALSE,
    plant_touched BOOLEAN DEFAULT FALSE,
    plant_blocked BOOLEAN DEFAULT FALSE,
    plant_visible_throughout BOOLEAN DEFAULT TRUE,
    significant_motion BOOLEAN DEFAULT FALSE,
    motion_description TEXT,
    event_type TEXT,
    
    -- Frame analysis
    frames_analyzed INTEGER DEFAULT 0,
    frame_paths TEXT[],
    
    -- Analysis metadata
    analysis_status TEXT DEFAULT 'pending',
    analysis_error TEXT,
    vlm_model TEXT,
    analyzed_at TIMESTAMPTZ
);

-- Convert to hypertable if TimescaleDB is available
SELECT create_hypertable('video_analysis', 'time', if_not_exists => TRUE);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_plant_snapshots_analysis_status 
ON plant_snapshots(analysis_status);

CREATE INDEX IF NOT EXISTS idx_plant_snapshots_plant_health 
ON plant_snapshots(plant_health_guess) WHERE plant_health_guess IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_plant_snapshots_plant_visible 
ON plant_snapshots(plant_visible);

CREATE INDEX IF NOT EXISTS idx_plant_snapshots_yellowing 
ON plant_snapshots(yellowing_visible) WHERE yellowing_visible = TRUE;

CREATE INDEX IF NOT EXISTS idx_plant_snapshots_drooping 
ON plant_snapshots(drooping_visible) WHERE drooping_visible = TRUE;

CREATE INDEX IF NOT EXISTS idx_plant_snapshots_analyzed_at 
ON plant_snapshots(analyzed_at DESC);

CREATE INDEX IF NOT EXISTS idx_video_analysis_time 
ON video_analysis(time DESC);

CREATE INDEX IF NOT EXISTS idx_video_analysis_event_type 
ON video_analysis(event_type);

CREATE INDEX IF NOT EXISTS idx_video_analysis_status 
ON video_analysis(analysis_status);

-- Create view for latest analyzed snapshots
CREATE OR REPLACE VIEW latest_analyzed_snapshots AS
SELECT 
    time,
    image_path,
    boxed_image_path,
    video_path,
    temperature_c,
    humidity_pct,
    led_state,
    person_detected,
    person_count,
    plant_visible,
    plant_occluded,
    plant_health_guess,
    yellowing_visible,
    drooping_visible,
    wilting_visible,
    image_quality,
    vlm_summary,
    vlm_analysis,
    analysis_reliability,
    analysis_status,
    vlm_model,
    analyzed_at
FROM plant_snapshots
WHERE analysis_status = 'completed'
ORDER BY time DESC
LIMIT 100;

-- Create view for plant health alerts
CREATE OR REPLACE VIEW plant_health_alerts AS
SELECT 
    time,
    image_path,
    plant_health_guess,
    yellowing_visible,
    drooping_visible,
    wilting_visible,
    vlm_summary,
    temperature_c,
    humidity_pct
FROM plant_snapshots
WHERE analysis_status = 'completed'
  AND (yellowing_visible = TRUE 
       OR drooping_visible = TRUE 
       OR wilting_visible = TRUE
       OR plant_health_guess IN ('yellowing', 'drooping', 'wilting'))
ORDER BY time DESC;

-- Create view for video events
CREATE OR REPLACE VIEW video_events AS
SELECT 
    time,
    video_path,
    event_type,
    person_entered,
    person_left,
    plant_touched,
    plant_blocked,
    significant_motion,
    motion_description,
    vlm_summary,
    analyzed_at
FROM video_analysis
WHERE analysis_status = 'completed'
ORDER BY time DESC
LIMIT 100;

-- Add comments
COMMENT ON TABLE video_analysis IS 'VLM analysis results for video clips';
COMMENT ON VIEW latest_analyzed_snapshots IS 'Most recent successfully analyzed snapshots';
COMMENT ON VIEW plant_health_alerts IS 'Snapshots with plant health concerns';
COMMENT ON VIEW video_events IS 'Analyzed video events';

-- Verify migration
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'plant_snapshots'
  AND column_name LIKE '%vlm%' 
   OR column_name LIKE '%plant_%'
   OR column_name LIKE '%analysis%'
   OR column_name LIKE '%yellowing%'
   OR column_name LIKE '%drooping%'
   OR column_name LIKE '%wilting%'
   OR column_name LIKE '%image_quality%'
ORDER BY ordinal_position;
