#!/usr/bin/env python3
"""
Check latest snapshot data
"""

import psycopg

DB_CONFIG = {
    'host': 'localhost',
    'port': '5433',
    'dbname': 'plantdb',
    'user': 'plantuser',
    'password': 'plantpass'
}

def check_latest():
    try:
        conn = psycopg.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Get latest snapshot
        cur.execute("""
            SELECT 
                time,
                image_path,
                person_detected,
                person_count,
                analysis_status
            FROM plant_snapshots
            ORDER BY time DESC
            LIMIT 5
        """)
        
        results = cur.fetchall()
        
        print("\n📊 Latest 5 snapshots:")
        print("-" * 80)
        for row in results:
            time, image, person_det, person_cnt, status = row
            print(f"Time: {time}")
            print(f"Image: {image}")
            print(f"Person detected: {person_det}")
            print(f"Person count: {person_cnt}")
            print(f"Analysis status: {status}")
            print("-" * 80)
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_latest()
