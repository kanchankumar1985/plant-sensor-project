#!/usr/bin/env python3
"""
Clean VLM Queue - Mark all pending/processing items as completed
"""

import psycopg

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': '5433',
    'dbname': 'plantdb',
    'user': 'plantuser',
    'password': 'plantpass'
}

def clean_queue():
    """Mark all queued/processing items as completed"""
    try:
        conn = psycopg.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Get counts before
        cur.execute("SELECT analysis_status, COUNT(*) FROM plant_snapshots GROUP BY analysis_status")
        before = dict(cur.fetchall())
        print("\n📊 Before cleanup:")
        for status, count in before.items():
            print(f"   {status}: {count}")
        
        # Mark queued and processing as completed
        cur.execute("""
            UPDATE plant_snapshots 
            SET analysis_status = 'completed' 
            WHERE analysis_status IN ('queued', 'processing')
        """)
        
        updated = cur.rowcount
        conn.commit()
        
        # Get counts after
        cur.execute("SELECT analysis_status, COUNT(*) FROM plant_snapshots GROUP BY analysis_status")
        after = dict(cur.fetchall())
        print("\n📊 After cleanup:")
        for status, count in after.items():
            print(f"   {status}: {count}")
        
        print(f"\n✅ Cleaned {updated} items from queue")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    clean_queue()
