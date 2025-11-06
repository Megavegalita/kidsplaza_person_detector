#!/usr/bin/env python3
"""
Run counter event queries against PostgreSQL and print results.
- Reads DSN from config/database.json
- Prints hourly summary for last 24h (or custom window)
- Prints recent detailed events (last 1h by default)
"""

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
import re

import psycopg2

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "database.json"
QUERIES_DIR = ROOT / "database" / "queries"


def load_dsn() -> Optional[str]:
    try:
        data = json.loads(CONFIG_PATH.read_text())
        # Try flat keys
        dsn = data.get("postgres_dsn") or data.get("db_dsn")
        if dsn:
            return dsn
        # Try nested under postgresql
        pg = data.get("postgresql") or {}
        if isinstance(pg, dict):
            if pg.get("url"):
                return pg.get("url")
            # Compose URL if fields exist
            user = pg.get("username") or ""
            pwd = pg.get("password") or ""
            host = pg.get("host") or "localhost"
            port = pg.get("port") or 5432
            db = pg.get("database") or "postgres"
            auth = f"{user}:{pwd}@" if pwd else f"{user}@" if user else ""
            return f"postgresql://{auth}{host}:{port}/{db}"
        return None
    except Exception:
        return None


def run_query(conn, sql: str, params: dict):
    # Convert :param to %(param)s for psycopg2
    def _repl(m: re.Match) -> str:
        name = m.group(1)
        return f"%({name})s"
    sql_psycopg = re.sub(r":(\w+)", _repl, sql)
    with conn.cursor() as cur:
        cur.execute(sql_psycopg, params)
        cols = [d.name for d in cur.description]
        rows = cur.fetchall()
        return cols, rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Check counter stats")
    parser.add_argument("--dsn", type=str, default=None, help="PostgreSQL DSN")
    parser.add_argument("--hours", type=int, default=24, help="Summary window hours")
    parser.add_argument("--channel-id", type=int, default=None, help="Filter channel id")
    args = parser.parse_args()

    dsn = args.dsn or load_dsn()
    if not dsn:
        print("ERROR: DSN not found in --dsn or config/database.json", file=sys.stderr)
        sys.exit(1)

    now = datetime.now(timezone.utc)
    from_ts = now - timedelta(hours=args.hours)
    to_ts = now
    channel_id = args.channel_id

    sql_hourly = (QUERIES_DIR / "query_counter_summary_by_hour.sql").read_text()
    sql_events = (QUERIES_DIR / "query_counter_events_between.sql").read_text()

    # Map :param to psycopg2 named style
    params = {
        "from_ts": from_ts,
        "to_ts": to_ts,
        "channel_id": channel_id,
    }

    with psycopg2.connect(dsn) as conn:
        print("\n=== Counter Summary by Hour (last", args.hours, "hours) ===")
        cols, rows = run_query(conn, sql_hourly, params)
        if not rows:
            print("(no rows)")
        else:
            print(" | ".join(cols))
            for r in rows:
                print(" | ".join(str(v) for v in r))

        # Recent events - 1 hour window capped inside selected window
        print("\n=== Detailed Events (last 1 hour) ===")
        params_recent = {
            "from_ts": max(from_ts, now - timedelta(hours=1)),
            "to_ts": to_ts,
            "channel_id": channel_id,
        }
        cols2, rows2 = run_query(conn, sql_events, params_recent)
        if not rows2:
            print("(no rows)")
        else:
            print(" | ".join(cols2))
            for r in rows2[:50]:  # limit print
                print(" | ".join(str(v) for v in r))
            if len(rows2) > 50:
                print(f"... ({len(rows2) - 50} more)")


if __name__ == "__main__":
    main()
