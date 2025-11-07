#!/usr/bin/env python3
"""
Daily counter summary - Count people entering/exiting today.

Provides detailed statistics for counter events for a specific day.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

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


def get_timestamp_column(conn) -> str:
    """Detect timestamp column name."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'counter_events' 
            AND column_name IN ('event_timestamp', 'occurred_at')
            LIMIT 1
        """)
        row = cur.fetchone()
        return row["column_name"] if row else "event_timestamp"


def get_daily_summary(
    dsn: str,
    channel_id: int,
    target_date: Optional[datetime] = None,
) -> Dict:
    """Get daily summary statistics."""
    if target_date is None:
        target_date = datetime.now()

    today_start = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0)
    today_end = datetime(
        target_date.year, target_date.month, target_date.day, 23, 59, 59, 999999
    )

    with psycopg2.connect(dsn) as conn:
        timestamp_col = get_timestamp_column(conn)

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Count total enter/exit events today
            cur.execute(
                f"""
                SELECT 
                    event_type,
                    COUNT(*) as count
                FROM counter_events
                WHERE channel_id = %s
                AND {timestamp_col} >= %s
                AND {timestamp_col} <= %s
                GROUP BY event_type
                ORDER BY event_type
            """,
                (channel_id, today_start, today_end),
            )

            events_today = {}
            for row in cur.fetchall():
                events_today[row["event_type"]] = row["count"]

            total_enter = events_today.get("enter", 0)
            total_exit = events_today.get("exit", 0)

            # Count unique tracks that entered today
            cur.execute(
                f"""
                SELECT COUNT(DISTINCT track_id) as count
                FROM counter_events
                WHERE channel_id = %s
                AND event_type = 'enter'
                AND {timestamp_col} >= %s
                AND {timestamp_col} <= %s
            """,
                (channel_id, today_start, today_end),
            )
            unique_tracks_entered = cur.fetchone()["count"]

            # Count unique tracks that exited today
            cur.execute(
                f"""
                SELECT COUNT(DISTINCT track_id) as count
                FROM counter_events
                WHERE channel_id = %s
                AND event_type = 'exit'
                AND {timestamp_col} >= %s
                AND {timestamp_col} <= %s
            """,
                (channel_id, today_start, today_end),
            )
            unique_tracks_exited = cur.fetchone()["count"]

            # Count by hour
            cur.execute(
                f"""
                SELECT 
                    DATE_TRUNC('hour', {timestamp_col}) as hour,
                    event_type,
                    COUNT(*) as count
                FROM counter_events
                WHERE channel_id = %s
                AND {timestamp_col} >= %s
                AND {timestamp_col} <= %s
                GROUP BY DATE_TRUNC('hour', {timestamp_col}), event_type
                ORDER BY hour, event_type
            """,
                (channel_id, today_start, today_end),
            )

            hourly_data = {}
            for row in cur.fetchall():
                hour = row["hour"].strftime("%H:00")
                if hour not in hourly_data:
                    hourly_data[hour] = {"enter": 0, "exit": 0}
                hourly_data[hour][row["event_type"]] = row["count"]

            return {
                "date": target_date.strftime("%Y-%m-%d"),
                "channel_id": channel_id,
                "total_enter": total_enter,
                "total_exit": total_exit,
                "unique_tracks_entered": unique_tracks_entered,
                "unique_tracks_exited": unique_tracks_exited,
                "net_count": total_enter - total_exit,
                "hourly_data": hourly_data,
            }


def main():
    parser = argparse.ArgumentParser(
        description="Get daily counter summary statistics"
    )
    parser.add_argument(
        "--channel-id",
        type=int,
        default=4,
        help="Channel ID (default: 4)",
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Target date (YYYY-MM-DD), default: today",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    args = parser.parse_args()

    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            print(f"Error: Invalid date format '{args.date}'. Use YYYY-MM-DD")
            sys.exit(1)

    dsn = load_dsn()

    try:
        summary = get_daily_summary(dsn, args.channel_id, target_date)

        if args.json:
            import json as json_module

            print(json_module.dumps(summary, indent=2, default=str))
        else:
            print("=" * 70)
            print(f"THỐNG KÊ NGƯỜI VÀO/RA - CHANNEL {args.channel_id}")
            print("=" * 70)
            print(f"Ngày: {summary['date']}")
            print()

            print("📊 SỐ LƯỢNG EVENTS:")
            print(f"   • Số lượt vào (ENTER): {summary['total_enter']}")
            print(f"   • Số lượt ra (EXIT): {summary['total_exit']}")
            print()

            print("👥 SỐ NGƯỜI (UNIQUE TRACKS):")
            print(f"   • Số người đã vào: {summary['unique_tracks_entered']}")
            print(f"   • Số người đã ra: {summary['unique_tracks_exited']}")
            print()

            if summary["hourly_data"]:
                print("⏰ PHÂN BỐ THEO GIỜ:")
                for hour in sorted(summary["hourly_data"].keys()):
                    enter = summary["hourly_data"][hour]["enter"]
                    exit_count = summary["hourly_data"][hour]["exit"]
                    print(f"   {hour}: Vào={enter:3d} | Ra={exit_count:3d}")
                print()

            print("📈 TỔNG KẾT:")
            print(f"   • Tổng số lượt vào: {summary['total_enter']}")
            print(f"   • Tổng số lượt ra: {summary['total_exit']}")
            print(
                f"   • Số người hiện tại trong khu vực (ước tính): {summary['net_count']}"
            )
            print()

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

