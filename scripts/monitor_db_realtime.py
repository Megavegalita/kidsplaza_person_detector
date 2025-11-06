#!/usr/bin/env python3
"""
Real-time monitor for database events - shows new events as they appear.
"""

import json
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.modules.database.postgres_manager import PostgresManager

def main():
    # Load database config
    config_path = Path("config/database.json")
    if not config_path.exists():
        print("❌ config/database.json not found")
        return
    
    with open(config_path) as f:
        db_config = json.load(f)
        pg = db_config.get("postgresql", {})
        db_dsn = pg.get("url") or pg.get("dsn")
        if not db_dsn:
            user = pg.get("username", "")
            pwd = pg.get("password", "")
            host = pg.get("host", "localhost")
            port = pg.get("port", 5432)
            dbname = pg.get("database", "postgres")
            auth = f"{user}:{pwd}@" if pwd else f"{user}@" if user else ""
            db_dsn = f"postgresql://{auth}{host}:{port}/{dbname}"
    
    print("🔌 Connecting to database...")
    try:
        db_manager = PostgresManager(dsn=db_dsn)
        print("✅ Database connected\n")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    print("📊 Monitoring counter_events table (Channel 4)")
    print("   Waiting for events... (Press Ctrl+C to stop)\n")
    
    last_count = 0
    seen_event_ids = set()
    
    try:
        while True:
            with db_manager._conn() as conn:
                with conn.cursor() as cur:
                    # Get total count
                    cur.execute("SELECT COUNT(*) FROM counter_events WHERE channel_id = 4")
                    total_count = cur.fetchone()[0]
                    
                    # Get all events to detect new ones
                    cur.execute("""
                        SELECT id, occurred_at, zone_id, event_type, track_id, person_id, frame_number
                        FROM counter_events
                        WHERE channel_id = 4
                        ORDER BY occurred_at DESC
                        LIMIT 50
                    """)
                    all_events = cur.fetchall()
                    
                    # Get event breakdown
                    cur.execute("""
                        SELECT event_type, COUNT(*) as count
                        FROM counter_events
                        WHERE channel_id = 4
                        GROUP BY event_type
                    """)
                    breakdown = {row[0]: row[1] for row in cur.fetchall()}
            
            # Detect new events
            new_events = []
            for event in all_events:
                event_id = event[0]
                if event_id not in seen_event_ids:
                    new_events.append(event)
                    seen_event_ids.add(event_id)
            
            # Show update if count changed or new events found
            if total_count != last_count or new_events:
                if new_events:
                    print(f"\n🆕 {len(new_events)} new event(s) detected!")
                    for event in reversed(new_events):  # Show oldest first
                        event_id, occurred_at, zone_id, event_type, track_id, person_id, frame_num = event
                        pid_str = person_id[:10] + "..." if person_id and len(person_id) > 10 else (person_id or "None")
                        print(f"  [{occurred_at}] {event_type.upper():5s} | Zone: {zone_id:10s} | Track: {str(track_id):3s} | Person: {pid_str:15s} | Frame: {frame_num}")
                
                print(f"\n📊 Total events: {total_count}")
                if breakdown:
                    print("   Breakdown:")
                    for event_type, count in breakdown.items():
                        print(f"     {event_type}: {count}")
                print()
            
            last_count = total_count
            time.sleep(1)  # Check every 1 second
            
    except KeyboardInterrupt:
        print("\n\n✅ Monitoring stopped")
        print(f"📊 Final count: {total_count} events")

if __name__ == "__main__":
    main()

