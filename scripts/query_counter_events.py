#!/usr/bin/env python3
"""
Query and process counter events from database.

Provides various queries and aggregations for counter events data.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "database.json"


def load_dsn() -> str:
    """Load database DSN from config."""
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


def get_total_count(dsn: str) -> Dict[str, int]:
    """Get total count of counter events."""
    with psycopg2.connect(dsn) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(DISTINCT channel_id) as channels,
                    COUNT(DISTINCT zone_id) as zones,
                    COUNT(DISTINCT track_id) as unique_tracks,
                    COUNT(DISTINCT person_id) as unique_persons
                FROM counter_events;
            """)
            return dict(cur.fetchone())


def get_events_by_channel(dsn: str, channel_id: Optional[int] = None) -> List[Dict]:
    """Get counter events grouped by channel."""
    with psycopg2.connect(dsn) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if channel_id:
                cur.execute("""
                    SELECT 
                        channel_id,
                        zone_id,
                        event_type,
                        COUNT(*) as count
                    FROM counter_events
                    WHERE channel_id = %s
                    GROUP BY channel_id, zone_id, event_type
                    ORDER BY channel_id, zone_id, event_type;
                """, (channel_id,))
            else:
                cur.execute("""
                    SELECT 
                        channel_id,
                        zone_id,
                        event_type,
                        COUNT(*) as count
                    FROM counter_events
                    GROUP BY channel_id, zone_id, event_type
                    ORDER BY channel_id, zone_id, event_type;
                """)
            return [dict(row) for row in cur.fetchall()]


def get_events_by_hour(
    dsn: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    channel_id: Optional[int] = None,
) -> List[Dict]:
    """Get counter events aggregated by hour."""
    with psycopg2.connect(dsn) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            conditions = []
            params = []

            if start_time:
                conditions.append("occurred_at >= %s")
                params.append(start_time)
            if end_time:
                conditions.append("occurred_at <= %s")
                params.append(end_time)
            if channel_id:
                conditions.append("channel_id = %s")
                params.append(channel_id)

            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

            cur.execute(f"""
                SELECT 
                    DATE_TRUNC('hour', occurred_at) as hour,
                    channel_id,
                    zone_id,
                    event_type,
                    COUNT(*) as count
                FROM counter_events
                {where_clause}
                GROUP BY DATE_TRUNC('hour', occurred_at), channel_id, zone_id, event_type
                ORDER BY hour DESC, channel_id, zone_id, event_type;
            """, params)
            return [dict(row) for row in cur.fetchall()]


def get_recent_events(dsn: str, limit: int = 20) -> List[Dict]:
    """Get recent counter events."""
    with psycopg2.connect(dsn) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    occurred_at,
                    channel_id,
                    zone_id,
                    event_type,
                    track_id,
                    person_id,
                    frame_number,
                    extra_json
                FROM counter_events
                ORDER BY occurred_at DESC
                LIMIT %s;
            """, (limit,))
            return [dict(row) for row in cur.fetchall()]


def get_zone_statistics(dsn: str, channel_id: Optional[int] = None) -> List[Dict]:
    """Get statistics per zone."""
    with psycopg2.connect(dsn) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if channel_id:
                cur.execute("""
                    SELECT 
                        channel_id,
                        zone_id,
                        COUNT(*) FILTER (WHERE event_type = 'enter') as enter_count,
                        COUNT(*) FILTER (WHERE event_type = 'exit') as exit_count,
                        COUNT(DISTINCT track_id) as unique_tracks,
                        COUNT(DISTINCT person_id) FILTER (WHERE person_id IS NOT NULL) as unique_persons,
                        MIN(occurred_at) as first_event,
                        MAX(occurred_at) as last_event
                    FROM counter_events
                    WHERE channel_id = %s
                    GROUP BY channel_id, zone_id
                    ORDER BY channel_id, zone_id;
                """, (channel_id,))
            else:
                cur.execute("""
                    SELECT 
                        channel_id,
                        zone_id,
                        COUNT(*) FILTER (WHERE event_type = 'enter') as enter_count,
                        COUNT(*) FILTER (WHERE event_type = 'exit') as exit_count,
                        COUNT(DISTINCT track_id) as unique_tracks,
                        COUNT(DISTINCT person_id) FILTER (WHERE person_id IS NOT NULL) as unique_persons,
                        MIN(occurred_at) as first_event,
                        MAX(occurred_at) as last_event
                    FROM counter_events
                    GROUP BY channel_id, zone_id
                    ORDER BY channel_id, zone_id;
                """)
            return [dict(row) for row in cur.fetchall()]


def main():
    parser = argparse.ArgumentParser(description="Query counter events from database")
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show summary statistics",
    )
    parser.add_argument(
        "--by-channel",
        action="store_true",
        help="Show events grouped by channel",
    )
    parser.add_argument(
        "--channel-id",
        type=int,
        help="Filter by channel ID",
    )
    parser.add_argument(
        "--by-hour",
        action="store_true",
        help="Show events aggregated by hour",
    )
    parser.add_argument(
        "--start-time",
        type=str,
        help="Start time (YYYY-MM-DD HH:MM:SS)",
    )
    parser.add_argument(
        "--end-time",
        type=str,
        help="End time (YYYY-MM-DD HH:MM:SS)",
    )
    parser.add_argument(
        "--recent",
        type=int,
        default=20,
        help="Show recent events (default: 20)",
    )
    parser.add_argument(
        "--zone-stats",
        action="store_true",
        help="Show zone statistics",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    args = parser.parse_args()

    dsn = load_dsn()

    # Default to summary if no specific action
    if not any(
        [
            args.summary,
            args.by_channel,
            args.by_hour,
            args.recent,
            args.zone_stats,
        ]
    ):
        args.summary = True

    if args.summary:
        stats = get_total_count(dsn)
        if args.json:
            print(json.dumps(stats, indent=2, default=str))
        else:
            print("=" * 60)
            print("Counter Events Summary")
            print("=" * 60)
            print(f"Total events: {stats['total']}")
            print(f"Channels: {stats['channels']}")
            print(f"Zones: {stats['zones']}")
            print(f"Unique tracks: {stats['unique_tracks']}")
            print(f"Unique persons: {stats['unique_persons']}")
            print("=" * 60)

    if args.by_channel:
        events = get_events_by_channel(dsn, args.channel_id)
        if args.json:
            print(json.dumps(events, indent=2, default=str))
        else:
            print("\nEvents by Channel/Zone:")
            print("-" * 60)
            for e in events:
                print(
                    f"Channel {e['channel_id']} | Zone {e['zone_id']} | "
                    f"{e['event_type']}: {e['count']}"
                )

    if args.by_hour:
        start_time = (
            datetime.strptime(args.start_time, "%Y-%m-%d %H:%M:%S")
            if args.start_time
            else None
        )
        end_time = (
            datetime.strptime(args.end_time, "%Y-%m-%d %H:%M:%S")
            if args.end_time
            else None
        )
        events = get_events_by_hour(dsn, start_time, end_time, args.channel_id)
        if args.json:
            print(json.dumps(events, indent=2, default=str))
        else:
            print("\nEvents by Hour:")
            print("-" * 60)
            for e in events:
                print(
                    f"{e['hour']} | Channel {e['channel_id']} | "
                    f"Zone {e['zone_id']} | {e['event_type']}: {e['count']}"
                )

    if args.recent:
        events = get_recent_events(dsn, args.recent)
        if args.json:
            print(json.dumps(events, indent=2, default=str))
        else:
            print(f"\nRecent Events (last {args.recent}):")
            print("-" * 80)
            for e in events:
                print(
                    f"{e['occurred_at']} | Ch{e['channel_id']} | "
                    f"Zone {e['zone_id']} | {e['event_type']} | "
                    f"Track {e['track_id']} | Person {e['person_id']}"
                )

    if args.zone_stats:
        stats = get_zone_statistics(dsn, args.channel_id)
        if args.json:
            print(json.dumps(stats, indent=2, default=str))
        else:
            print("\nZone Statistics:")
            print("-" * 80)
            for s in stats:
                print(
                    f"Channel {s['channel_id']} | Zone {s['zone_id']}: "
                    f"ENTER={s['enter_count']}, EXIT={s['exit_count']}, "
                    f"Tracks={s['unique_tracks']}, Persons={s['unique_persons']}"
                )
                print(f"  First: {s['first_event']}, Last: {s['last_event']}")


if __name__ == "__main__":
    main()


