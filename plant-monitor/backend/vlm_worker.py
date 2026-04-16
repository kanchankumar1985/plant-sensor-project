#!/usr/bin/env python3
"""
Asynchronous VLM worker: processes queued image analyses one at a time.
- Picks the oldest queued snapshot
- Marks it processing
- Runs VLM image analysis with resizing/compression
- Applies rules and updates DB with completed/failed
- Inserts a row into image_analysis for reporting

Environment:
- VLM_ENABLED=true/false
- VLM_COOLDOWN_SECONDS=600
- VLM_POLL_INTERVAL=15
- OLLAMA_MODEL, OLLAMA_TIMEOUT
- IMAGES_DIR
"""

import os
import time
import json
import traceback
from datetime import datetime, timezone
import psycopg
from psycopg.types.json import Json
from dotenv import load_dotenv

from vlm.vlm_analyzer import analyze_image_with_vlm
from vlm.analysis_rules import apply_analysis_rules, get_analysis_summary
from vlm.ollama_client import get_ollama_client

# Reuse DB config (mirrors capture_with_vlm)
DB_CONFIG = {
    "host": "localhost",
    "port": "5433",
    "dbname": "plantdb",
    "user": "plantuser",
    "password": "plantpass",
}

load_dotenv()

VLM_ENABLED = os.getenv('VLM_ENABLED', 'true').lower() in ('1','true','yes','y')
VLM_COOLDOWN_SECONDS = int(os.getenv('VLM_COOLDOWN_SECONDS', '600'))
VLM_POLL_INTERVAL = int(os.getenv('VLM_POLL_INTERVAL', '15'))
IMAGES_DIR = os.getenv('IMAGES_DIR', '/Volumes/SD-128GB/PlantMonitor/images')
VLM_ANALYSIS_TYPE = os.getenv('VLM_ANALYSIS_TYPE', '').strip().lower() or None  # e.g., 'person' to force person prompt


def connect_db():
    print(f"[DB] Connecting to database {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']} as {DB_CONFIG['user']} ...")
    conn = psycopg.connect(**DB_CONFIG)
    print("[DB] Connection established")
    return conn


def get_last_completed_at(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT MAX(analyzed_at)
            FROM plant_snapshots
            WHERE analyzed_at IS NOT NULL
            """
        )
        row = cur.fetchone()
        return row[0]


def get_processing_count(conn) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) FROM plant_snapshots
            WHERE analysis_status = 'processing'
            """
        )
        n = int(cur.fetchone()[0])
        print(f"[DB][POLL] Current processing count: {n}")
        return n


def get_queued_count(conn) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) FROM plant_snapshots
            WHERE analysis_status = 'queued'
            """
        )
        n = int(cur.fetchone()[0])
        print(f"[DB][POLL] Current queued count: {n}")
        return n


def claim_next_job(conn):
    """Atomically claim the oldest queued job by marking it processing and returning its data."""
    with conn.cursor() as cur:
        # Lock the next queued row
        print("[DB][QUERY] Selecting oldest queued job ...")
        cur.execute(
            """
            SELECT time, image_path, detection_metadata
            FROM plant_snapshots
            WHERE analysis_status = 'queued'
            ORDER BY time ASC
            LIMIT 1
            FOR UPDATE SKIP LOCKED
            """
        )
        row = cur.fetchone()
        if not row:
            print("[DB][RESULT] No queued jobs found")
            conn.rollback()
            return None
        snapshot_time, image_filename, detection_metadata = row
        print(f"[DB][RESULT] Claimed job time={snapshot_time}, image={image_filename}")
        # Mark as processing
        print(f"[JOB] Marking job {snapshot_time} as 'processing'")
        cur.execute(
            """
            UPDATE plant_snapshots
            SET analysis_status = 'processing'
            WHERE time = %s
            """,
            (snapshot_time,)
        )
        print("[DB][TXN] Committing job claim ...")
        conn.commit()
        print("[DB][TXN] Commit successful")
        return {
            'time': snapshot_time,
            'image_filename': image_filename,
            'yolo_metadata': json.loads(detection_metadata) if isinstance(detection_metadata, str) else detection_metadata,
        }


def _normalize_person_analysis(analysis, yolo=None):
    try:
        if not isinstance(analysis, dict):
            return analysis
        clothing = analysis.get('clothing') or {}
        person_detected = analysis.get('person_detected')
        if person_detected is None:
            person_detected = analysis.get('person_present')
        if person_detected is None and yolo:
            person_detected = yolo.get('person_detected', False)
        person_count = analysis.get('person_count')
        if person_count is None and yolo:
            person_count = yolo.get('person_count', 0)
        norm = {
            'person_detected': bool(person_detected or False),
            'person_count': int(person_count or 0),
            'position': analysis.get('position', 'unknown') or 'unknown',
            'clothing': {
                'shirt_type': clothing.get('shirt_type', 'unknown') or 'unknown',
                'shirt_color': clothing.get('shirt_color', 'unknown') or 'unknown',
                'shirt_has_text': bool(clothing.get('shirt_has_text', False)),
                'shirt_text': clothing.get('shirt_text', 'unreadable') or 'unreadable',
                'shirt_has_logo': bool(clothing.get('shirt_has_logo', False)),
                'shirt_logo_description': clothing.get('shirt_logo_description', 'none') or 'none',
                'pants_type': clothing.get('pants_type', 'unknown') or 'unknown',
                'pants_color': clothing.get('pants_color', 'unknown') or 'unknown',
            },
            'accessories': analysis.get('accessories') if isinstance(analysis.get('accessories'), list) else [],
            'actions': analysis.get('actions') if isinstance(analysis.get('actions'), list) else [],
            'distance_from_plant': analysis.get('distance_from_plant', 'unknown') or 'unknown',
            'facing_camera': bool(analysis.get('facing_camera', False)),
            'confidence': analysis.get('confidence', 'medium') or 'medium',
            'summary': analysis.get('summary', '') or '',
        }
        print(f"[VLM][NORM] Normalized person analysis: {json.dumps(norm)[:800]}")
        return norm
    except Exception as e:
        print(f"[ERROR][NORM] Failed to normalize person analysis: {e}")
        traceback.print_exc()
        return analysis


def update_snapshot(conn, snapshot_time, vlm_result, enhanced):
    """Update the plant_snapshots row with analysis results and status."""
    vlm_analysis = vlm_result.get('analysis', {}) if vlm_result else None
    vlm_success = vlm_result.get('success', False) if vlm_result else False
    vlm_error = vlm_result.get('error') if vlm_result else None
    vlm_model = vlm_result.get('model') if vlm_result else None
    reliability = enhanced.get('reliability', {}) if enhanced else None
    vlm_summary = get_analysis_summary(enhanced) if enhanced else None

    analysis_status = 'completed' if vlm_success else 'failed' if vlm_error else 'failed'

    print(f"[DB][TXN] Updating snapshot {snapshot_time} with analysis results (status={analysis_status}) ...")
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE plant_snapshots
            SET vlm_summary = %s,
                vlm_analysis = %s,
                plant_visible = %s,
                plant_occluded = %s,
                plant_health_guess = %s,
                yellowing_visible = %s,
                drooping_visible = %s,
                wilting_visible = %s,
                image_quality = %s,
                analysis_status = %s,
                analysis_error = %s,
                analysis_reliability = %s,
                vlm_model = %s,
                analyzed_at = %s
            WHERE time = %s
            """,
            (
                vlm_summary,
                Json(vlm_analysis) if vlm_analysis else None,
                None if not vlm_analysis else vlm_analysis.get('plant_visible', True),
                None if not vlm_analysis else vlm_analysis.get('plant_occluded', False),
                None if not vlm_analysis else vlm_analysis.get('plant_health_guess'),
                None if not vlm_analysis else vlm_analysis.get('yellowing_visible', False),
                None if not vlm_analysis else vlm_analysis.get('drooping_visible', False),
                None if not vlm_analysis else vlm_analysis.get('wilting_visible', False),
                None if not vlm_analysis else vlm_analysis.get('image_quality'),
                analysis_status,
                vlm_error,
                json.dumps(reliability) if reliability else None,
                vlm_model,
                datetime.now(timezone.utc) if vlm_success else None,
                snapshot_time,
            )
        )
        print("[DB][TXN] Committing snapshot update ...")
        conn.commit()
        print("[DB][TXN] Commit successful for snapshot update")

    # Also insert into image_analysis table if present
    try:
        print(f"[DB][TXN] Inserting image_analysis row for snapshot {snapshot_time} ...")
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO image_analysis (
                    time, image_path, snapshot_time, vlm_summary, vlm_analysis,
                    person_present, person_count, plant_visible, plant_occluded, plant_health_guess,
                    yellowing_visible, drooping_visible, wilting_visible, image_quality,
                    analysis_status, analysis_error, vlm_model, analyzed_at
                )
                SELECT NOW(), image_path, time, %s, %s,
                       %s, %s, %s, %s, %s,
                       %s, %s, %s, %s,
                       %s, %s, %s, %s
                FROM plant_snapshots
                WHERE time = %s
                """,
                (
                    vlm_summary,
                    Json(vlm_analysis) if vlm_analysis else None,
                    None if not vlm_analysis else (vlm_analysis.get('person_present', vlm_analysis.get('person_detected', False))),
                    None if not vlm_analysis else vlm_analysis.get('person_count', 0),
                    None if not vlm_analysis else vlm_analysis.get('plant_visible', True),
                    None if not vlm_analysis else vlm_analysis.get('plant_occluded', False),
                    None if not vlm_analysis else vlm_analysis.get('plant_health_guess'),
                    None if not vlm_analysis else vlm_analysis.get('yellowing_visible', False),
                    None if not vlm_analysis else vlm_analysis.get('drooping_visible', False),
                    None if not vlm_analysis else vlm_analysis.get('wilting_visible', False),
                    None if not vlm_analysis else vlm_analysis.get('image_quality'),
                    analysis_status,
                    vlm_error,
                    vlm_model,
                    datetime.now(timezone.utc) if vlm_success else None,
                    snapshot_time,
                )
            )
            try:
                payload_preview = {
                    "vlm_summary": vlm_summary,
                    "person_present": None if not vlm_analysis else (vlm_analysis.get('person_present', vlm_analysis.get('person_detected', False))),
                    "person_count": None if not vlm_analysis else vlm_analysis.get('person_count', 0),
                    "plant_visible": None if not vlm_analysis else vlm_analysis.get('plant_visible', True),
                    "plant_occluded": None if not vlm_analysis else vlm_analysis.get('plant_occluded', False),
                    "plant_health_guess": None if not vlm_analysis else vlm_analysis.get('plant_health_guess'),
                    "yellowing_visible": None if not vlm_analysis else vlm_analysis.get('yellowing_visible', False),
                    "drooping_visible": None if not vlm_analysis else vlm_analysis.get('drooping_visible', False),
                    "wilting_visible": None if not vlm_analysis else vlm_analysis.get('wilting_visible', False),
                    "image_quality": None if not vlm_analysis else vlm_analysis.get('image_quality'),
                    "analysis_status": analysis_status,
                    "analysis_error": vlm_error,
                    "vlm_model": vlm_model,
                }
                print(f"[DB][PAYLOAD] image_analysis values: {json.dumps(payload_preview)[:800]}")
                print(f"[DB][JSON] vlm_analysis blob: {(json.dumps(vlm_analysis) if vlm_analysis else 'null')[:800]}")
            except Exception:
                pass
            print("[DB][TXN] Committing image_analysis insert ...")
            conn.commit()
            print("[DB][TXN] image_analysis insert committed")
    except Exception as e:
        print(f"[ERROR][DB] Failed to insert into image_analysis for {snapshot_time}: {e}")
        traceback.print_exc()
        print("[DB][TXN] Rolling back image_analysis insert ...")
        conn.rollback()


def main_loop():
    # Startup configuration logs
    now_iso = datetime.now(timezone.utc).isoformat()
    print(f"[VLM_WORKER] Starting worker at {now_iso}")
    print(f"[VLM_WORKER][CONFIG] VLM_ENABLED={VLM_ENABLED}, POLL_INTERVAL={VLM_POLL_INTERVAL}s, COOLDOWN={VLM_COOLDOWN_SECONDS}s, IMAGES_DIR={IMAGES_DIR}")
    print(f"[VLM_WORKER][CONFIG] VLM_ANALYSIS_TYPE override={VLM_ANALYSIS_TYPE}")
    try:
        client = get_ollama_client()
        print(f"[VLM_WORKER][CONFIG] Ollama host={client.host}, model={client.model}, timeout={client.timeout}s")
    except Exception as e:
        print(f"[ERROR][CONFIG] Could not initialize Ollama client: {e}")
        traceback.print_exc()

    if not VLM_ENABLED:
        print("[VLM_WORKER] Disabled via VLM_ENABLED=false; exiting")
        return

    # Connect to DB with logs and run one-time diagnostics
    while True:
        try:
            conn = connect_db()
            break
        except Exception as e:
            print(f"[ERROR][DB] Connection failed: {e}")
            traceback.print_exc()
            print("[DB] Retrying in 5s ...")
            time.sleep(5)

    with conn:
        # One-time diagnostics
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT analysis_status, COUNT(*)
                    FROM plant_snapshots
                    WHERE analysis_status IS NOT NULL
                    GROUP BY analysis_status
                    """
                )
                rows = cur.fetchall()
                counts = {r[0]: r[1] for r in rows}
                print(f"[VLM_WORKER][DIAG] Status counts at startup: {counts}")
        except Exception as e:
            print(f"[ERROR][DB] Failed to fetch status counts: {e}")
            traceback.print_exc()

        # Check image_analysis availability
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM image_analysis LIMIT 1")
                _ = cur.fetchone()
                print("[VLM_WORKER][DIAG] image_analysis table is reachable")
        except Exception as e:
            print(f"[ERROR][DB] image_analysis table not reachable: {e}")
            traceback.print_exc()

        print("[VLM_WORKER] Entering polling loop ...")
        cycle = 0
        while True:
            cycle += 1
            try:
                print(f"[HEARTBEAT] Poll cycle #{cycle} at {datetime.now(timezone.utc).isoformat()}")
                print("[POLL] Checking for pending VLM jobs ...")
                # Poll metrics
                _ = get_processing_count(conn)
                queued = get_queued_count(conn)

                # Respect single-processing and cooldown
                if _ > 0:
                    print("[POLL] A job is already processing; sleeping")
                    time.sleep(VLM_POLL_INTERVAL)
                    continue

                # Cooldown removed: run analyses back-to-back without waiting

                # Attempt to claim a job
                job = claim_next_job(conn)
                if not job:
                    print(f"[POLL] No queued jobs found; sleeping {VLM_POLL_INTERVAL}s")
                    time.sleep(VLM_POLL_INTERVAL)
                    continue

                # Build image path and validate
                image_path = os.path.join(IMAGES_DIR, job['image_filename'])
                yolo = job['yolo_metadata'] or {}
                print(f"[JOB] Picked job time={job['time']} image={job['image_filename']} -> {image_path}")

                if not os.path.exists(image_path):
                    print(f"[ERROR][JOB] Image file does not exist: {image_path}")
                    with conn.cursor() as cur:
                        print("[DB][TXN] Marking job as failed due to missing image ...")
                        cur.execute(
                            """
                            UPDATE plant_snapshots
                            SET analysis_status = 'failed', analysis_error = 'image not found'
                            WHERE time = %s
                            """,
                            (job['time'],)
                        )
                        print("[DB][TXN] Committing failure update ...")
                        conn.commit()
                        print("[DB][TXN] Commit successful")
                    continue

                try:
                    print(f"[JOB][VLM] Starting analysis for {image_path}")
                    # Log model/timeout again
                    try:
                        client = get_ollama_client()
                        print(f"[JOB][VLM] Using model={client.model} timeout={client.timeout}s host={client.host}")
                    except Exception:
                        pass
                    atype = "person_detailed"
                    print(f"[JOB][VLM] analysis_type={atype} (forced)")
                    t0 = time.perf_counter()
                    vlm_result = analyze_image_with_vlm(image_path, analysis_type=atype, yolo_metadata=yolo)
                    if not vlm_result:
                        raise RuntimeError("VLM analysis returned no result")
                    dt = time.perf_counter() - t0
                    print(f"[JOB][VLM] Analysis finished in {dt:.2f}s success={vlm_result.get('success')} error={vlm_result.get('error')}")
                    print(f"[JOB][VLM] prompt_name={vlm_result.get('prompt_name')} prompt_preview={(vlm_result.get('prompt_preview') or '')[:200]}")
                    if atype in ("person", "person_detailed") and vlm_result.get('analysis'):
                        vlm_result['analysis'] = _normalize_person_analysis(vlm_result['analysis'], yolo)
                    enhanced = apply_analysis_rules(vlm_result, yolo_metadata=yolo)
                    print("[JOB] Applying rules completed")

                    update_snapshot(conn, job['time'], vlm_result, enhanced)
                    print(f"[JOB] Snapshot updated and image_analysis inserted for {job['time']}")
                    print(f"[JOB] ✅ Completed job {job['time']}")

                except Exception as e:
                    print(f"[ERROR][JOB] Exception during analysis for {job['time']}: {e}")
                    traceback.print_exc()
                    # Mark as failed to avoid being stuck
                    try:
                        with conn.cursor() as cur:
                            print("[DB][TXN] Marking job as failed due to exception ...")
                            cur.execute(
                                """
                                UPDATE plant_snapshots
                                SET analysis_status = 'failed', analysis_error = %s
                                WHERE time = %s
                                """,
                                (str(e), job['time'])
                            )
                            print("[DB][TXN] Committing failure update ...")
                            conn.commit()
                            print("[DB][TXN] Commit successful")
                    except Exception as e2:
                        print(f"[ERROR][DB] Failed to mark job failed: {e2}")
                        traceback.print_exc()

            except Exception as loop_err:
                print(f"[ERROR][LOOP] Worker loop error: {loop_err}")
                traceback.print_exc()
                time.sleep(VLM_POLL_INTERVAL)


if __name__ == "__main__":
    main_loop()
