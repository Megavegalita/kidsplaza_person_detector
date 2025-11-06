#!/usr/bin/env python3
"""Check database directly for counter_events table and data."""

import json
import sys
from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "database.json"


def load_dsn():
    with open(CONFIG_PATH) as f:
        db_config = json.load(f)
        pg = db_config.get("postgresql", {}) or {}
        dsn = pg.get("dsn") or pg.get("url")
        if not dsn:
            user = pg.get("username") or ""
            pwd = pg.get("password") or ""
            host = pg.get("host") or "localhost"
            port = pg.get("port") or 5432
            dbname = pg.get("database") or "postgres"
            auth = f"{user}:{pwd}@" if pwd else f"{user}@" if user else ""
            dsn = f"postgresql://{auth}{host}:{port}/{dbname}"
        return dsn


def main():
    dsn = load_dsn()
    print(f"Connecting to: {dsn.split('@')[1] if '@' in dsn else dsn}")
    
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            # Check if table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'counter_events'
                );
            """)
            exists = cur.fetchone()[0]
            print(f"\nTable 'counter_events' exists: {exists}")
            
            if not exists:
                print("ERROR: Table counter_events does not exist!")
                sys.exit(1)
            
            # Count total rows
            cur.execute("SELECT COUNT(*) FROM counter_events;")
            total = cur.fetchone()[0]
            print(f"Total rows in counter_events: {total}")
            
            # Count by channel
            cur.execute("""
                SELECT channel_id, COUNT(*) 
                FROM counter_events 
                GROUP BY channel_id 
                ORDER BY channel_id;
            """)
            print("\nRows by channel_id:")
            for row in cur.fetchall():
                print(f"  Channel {row[0]}: {row[1]} rows")
            
            # Recent events (last 10)
            cur.execute("""
                SELECT occurred_at, channel_id, zone_id, event_type, 
                       track_id, person_id, frame_number
                FROM counter_events 
                ORDER BY occurred_at DESC 
                LIMIT 10;
            """)
            rows = cur.fetchall()
            if rows:
                print("\nRecent events (last 10):")
                print("  occurred_at | ch | zone | evt | tid | pid | frame")
                print("  " + "-" * 70)
                for r in rows:
                    print(f"  {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {r[6]}")
            else:
                print("\nNo events found in counter_events table")


if __name__ == "__main__":
    main()

