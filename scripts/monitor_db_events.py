#!/usr/bin/env python3
"""
Monitor database events in real-time for channel 4.
"""

import json
import time
from pathlib import Path
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
        print("✅ Database connected")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    print("\n📊 Monitoring counter_events table (Channel 4)...")
    print("Press Ctrl+C to stop\n")
    
    last_count = 0
    
    try:
        while True:
            with db_manager._conn() as conn:
                with conn.cursor() as cur:
                    # Get total count
                    cur.execute("SELECT COUNT(*) FROM counter_events WHERE channel_id = 4")
                    total_count = cur.fetchone()[0]
                    
                    # Get recent events (last 10)
                    cur.execute("""
                        SELECT occurred_at, zone_id, event_type, track_id, person_id, frame_number
                        FROM counter_events
                        WHERE channel_id = 4
                        ORDER BY occurred_at DESC
                        LIMIT 10
                    """)
                    recent_events = cur.fetchall()
                    
                    # Get event breakdown
                    cur.execute("""
                        SELECT event_type, COUNT(*) as count
                        FROM counter_events
                        WHERE channel_id = 4
                        GROUP BY event_type
                    """)
                    breakdown = {row[0]: row[1] for row in cur.fetchall()}
            
            # Show update if count changed
            if total_count != last_count:
                new_events = total_count - last_count
                print(f"\n🆕 New events detected: +{new_events} (Total: {total_count})")
                
                if recent_events:
                    print("\n📋 Recent events:")
                    for event in recent_events[:5]:  # Show last 5
                        occurred_at, zone_id, event_type, track_id, person_id, frame_num = event
                        pid_str = person_id[:8] + "..." if person_id and len(person_id) > 8 else (person_id or "None")
                        print(f"  [{occurred_at}] {event_type.upper():5s} | Zone: {zone_id:10s} | Track: {track_id:3s} | Person: {pid_str:12s} | Frame: {frame_num}")
                
                if breakdown:
                    print("\n📊 Event breakdown:")
                    for event_type, count in breakdown.items():
                        print(f"  {event_type}: {count}")
                print()
            
            last_count = total_count
            time.sleep(2)  # Check every 2 seconds
            
    except KeyboardInterrupt:
        print("\n\n✅ Monitoring stopped")
        print(f"📊 Final count: {total_count} events")

if __name__ == "__main__":
    main()

