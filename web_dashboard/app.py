#!/usr/bin/env python3
"""
Web Dashboard for Counter Events Statistics.

Flask web application to display and filter counter events data.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

import psycopg2
from flask import Flask, jsonify, render_template, request
from psycopg2.extras import RealDictCursor

# Add parent directory to path for imports
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CONFIG_PATH = ROOT / "config" / "database.json"
CAMERA_CONFIG_PATH = ROOT / "input" / "cameras_config" / "kidsplaza_thanhxuan.json"

app = Flask(__name__)


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


def load_camera_channels() -> Dict:
    """Load camera channels information from config file."""
    try:
        if not CAMERA_CONFIG_PATH.exists():
            return {"channels": [], "address": ""}
        
        with open(CAMERA_CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        channels = []
        address = config.get("address", "")
        
        for channel in config.get("channels", []):
            channels.append({
                "channel_id": channel.get("channel_id"),
                "name": channel.get("name", ""),
                "description": channel.get("description", ""),
                "location": channel.get("localtion", ""),  # Note: typo in config "localtion"
                "address": address,
            })
        
        return {"channels": channels, "address": address}
    except Exception as e:
        print(f"Error loading camera config: {e}")
        return {"channels": [], "address": ""}


def get_daily_summary(
    channel_ids: Optional[list] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    zone_id: Optional[str] = None,
) -> Dict:
    """Get summary statistics for date range."""
    # Default to today if no dates provided
    if start_date is None:
        start_date = datetime.now()
    if end_date is None:
        end_date = datetime.now()

    # Set time boundaries
    start_datetime = datetime(
        start_date.year, start_date.month, start_date.day, 0, 0, 0
    )
    end_datetime = datetime(
        end_date.year, end_date.month, end_date.day, 23, 59, 59, 999999
    )

    dsn = load_dsn()

    with psycopg2.connect(dsn) as conn:
        timestamp_col = get_timestamp_column(conn)

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Build WHERE clause
            conditions = [f"{timestamp_col} >= %s", f"{timestamp_col} <= %s"]
            params = [start_datetime, end_datetime]

            if channel_ids and len(channel_ids) > 0:
                placeholders = ",".join(["%s"] * len(channel_ids))
                conditions.append(f"channel_id IN ({placeholders})")
                params.extend(channel_ids)

            if zone_id:
                conditions.append("zone_id = %s")
                params.append(zone_id)

            where_clause = "WHERE " + " AND ".join(conditions)

            # Count total enter/exit events
            cur.execute(
                f"""
                SELECT 
                    event_type,
                    COUNT(*) as count
                FROM counter_events
                {where_clause}
                GROUP BY event_type
                ORDER BY event_type
            """,
                params,
            )

            events_today = {}
            for row in cur.fetchall():
                events_today[row["event_type"]] = row["count"]

            total_enter = events_today.get("enter", 0)
            total_exit = events_today.get("exit", 0)

            # Count unique tracks
            enter_conditions = conditions + ["event_type = 'enter'"]
            enter_where = "WHERE " + " AND ".join(enter_conditions)
            enter_params = params + []

            cur.execute(
                f"""
                SELECT COUNT(DISTINCT track_id) as count
                FROM counter_events
                {enter_where}
            """,
                enter_params,
            )
            unique_tracks_entered = cur.fetchone()["count"]

            exit_conditions = conditions + ["event_type = 'exit'"]
            exit_where = "WHERE " + " AND ".join(exit_conditions)
            exit_params = params + []

            cur.execute(
                f"""
                SELECT COUNT(DISTINCT track_id) as count
                FROM counter_events
                {exit_where}
            """,
                exit_params,
            )
            unique_tracks_exited = cur.fetchone()["count"]

            # Count unique tracks by hour (số người vào/ra theo giờ)
            cur.execute(
                f"""
                SELECT 
                    DATE_TRUNC('hour', {timestamp_col}) as hour,
                    event_type,
                    COUNT(DISTINCT track_id) as count
                FROM counter_events
                {where_clause}
                GROUP BY DATE_TRUNC('hour', {timestamp_col}), event_type
                ORDER BY hour, event_type
            """,
                params,
            )

            hourly_data = {}
            for row in cur.fetchall():
                hour = row["hour"].strftime("%H:00")
                if hour not in hourly_data:
                    hourly_data[hour] = {"enter": 0, "exit": 0}
                hourly_data[hour][row["event_type"]] = row["count"]

            # Get available channels and zones
            cur.execute(
                """
                SELECT DISTINCT channel_id, zone_id
                FROM counter_events
                ORDER BY channel_id, zone_id
            """
            )
            available_channels = set()
            available_zones = set()
            for row in cur.fetchall():
                available_channels.add(row["channel_id"])
                available_zones.add(row["zone_id"])

            return {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "channel_ids": channel_ids if channel_ids else None,
                "zone_id": zone_id,
                "total_enter": total_enter,
                "total_exit": total_exit,
                "unique_tracks_entered": unique_tracks_entered,
                "unique_tracks_exited": unique_tracks_exited,
                "net_count": total_enter - total_exit,
                "hourly_data": hourly_data,
                "available_channels": sorted(list(available_channels)),
                "available_zones": sorted(list(available_zones)),
            }


@app.route("/")
def index():
    """Render main dashboard page."""
    today = datetime.now().strftime("%Y-%m-%d")
    return render_template("index.html", today=today)


@app.route("/api/channels")
def api_channels():
    """API endpoint for camera channels information."""
    try:
        channels_info = load_camera_channels()
        return jsonify(channels_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/summary")
def api_summary():
    """API endpoint for summary data."""
    try:
        # Support both single channel_id and multiple channel_ids
        channel_id = request.args.get("channel_id", type=int)
        channel_ids_str = request.args.get("channel_ids")
        
        channel_ids = None
        if channel_ids_str:
            # Parse comma-separated channel IDs
            try:
                channel_ids = [int(cid.strip()) for cid in channel_ids_str.split(",") if cid.strip()]
            except ValueError:
                return jsonify({"error": "Invalid channel_ids format. Use comma-separated integers"}), 400
        elif channel_id:
            # Backward compatibility: single channel_id
            channel_ids = [channel_id]
        
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        zone_id = request.args.get("zone_id")

        start_date = None
        end_date = None

        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            except ValueError:
                return jsonify({"error": "Invalid start_date format. Use YYYY-MM-DD"}), 400

        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            except ValueError:
                return jsonify({"error": "Invalid end_date format. Use YYYY-MM-DD"}), 400

        summary = get_daily_summary(
            channel_ids=channel_ids,
            start_date=start_date,
            end_date=end_date,
            zone_id=zone_id,
        )

        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/recent-events")
def api_recent_events():
    """API endpoint for recent events."""
    try:
        limit = request.args.get("limit", default=50, type=int)
        channel_id = request.args.get("channel_id", type=int)
        channel_ids_str = request.args.get("channel_ids")
        zone_id = request.args.get("zone_id")

        dsn = load_dsn()

        with psycopg2.connect(dsn) as conn:
            timestamp_col = get_timestamp_column(conn)

            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                conditions = []
                params = []

                # Support multiple channel_ids
                channel_ids = None
                if channel_ids_str:
                    try:
                        channel_ids = [int(cid.strip()) for cid in channel_ids_str.split(",") if cid.strip()]
                    except ValueError:
                        pass
                
                if channel_ids and len(channel_ids) > 0:
                    placeholders = ",".join(["%s"] * len(channel_ids))
                    conditions.append(f"channel_id IN ({placeholders})")
                    params.extend(channel_ids)
                elif channel_id:
                    conditions.append("channel_id = %s")
                    params.append(channel_id)

                if zone_id:
                    conditions.append("zone_id = %s")
                    params.append(zone_id)

                where_clause = (
                    "WHERE " + " AND ".join(conditions) if conditions else ""
                )

                cur.execute(
                    f"""
                    SELECT 
                        {timestamp_col} as timestamp,
                        channel_id,
                        zone_id,
                        event_type,
                        track_id,
                        person_id
                    FROM counter_events
                    {where_clause}
                    ORDER BY {timestamp_col} DESC
                    LIMIT %s
                """,
                    params + [limit],
                )

                events = []
                for row in cur.fetchall():
                    events.append(
                        {
                            "timestamp": row["timestamp"].isoformat()
                            if row["timestamp"]
                            else None,
                            "channel_id": row["channel_id"],
                            "zone_id": row["zone_id"],
                            "event_type": row["event_type"],
                            "track_id": row["track_id"],
                            "person_id": row["person_id"],
                        }
                    )

                return jsonify({"events": events})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)

