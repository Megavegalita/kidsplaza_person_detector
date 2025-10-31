#!/bin/bash
# Script to query track information from PostgreSQL
# Usage: ./scripts/query_tracks.sh [config_file]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load database config
DB_CONFIG="${1:-$PROJECT_ROOT/config/database.json}"

if [ ! -f "$DB_CONFIG" ]; then
    echo "Error: Database config file not found: $DB_CONFIG"
    exit 1
fi

# Extract connection info from config
DB_HOST=$(python3 -c "import json; print(json.load(open('$DB_CONFIG'))['postgresql']['host'])" 2>/dev/null || echo "localhost")
DB_PORT=$(python3 -c "import json; print(json.load(open('$DB_CONFIG'))['postgresql']['port'])" 2>/dev/null || echo "5432")
DB_NAME=$(python3 -c "import json; print(json.load(open('$DB_CONFIG'))['postgresql']['database'])" 2>/dev/null || echo "gender_analysis")
DB_USER=$(python3 -c "import json; print(json.load(open('$DB_CONFIG'))['postgresql']['username'])" 2>/dev/null || echo "autoeyes")
DB_PASSWORD=$(python3 -c "import json; print(json.load(open('$DB_CONFIG'))['postgresql'].get('password', ''))" 2>/dev/null || echo "")

export PGPASSWORD="$DB_PASSWORD"

echo "Connecting to PostgreSQL:"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo ""

# Verify connection and tables exist
echo "Verifying connection and tables..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
SELECT current_database() AS current_db, current_schema() AS current_schema;

SELECT table_schema, table_name 
FROM information_schema.tables 
WHERE table_name IN ('run_gender_summary', 'track_genders', 'detections', 'tracks')
ORDER BY table_name;
" || {
    echo "Error: Failed to connect or tables not found!"
    exit 1
}

echo ""
echo "Running query_tracks.sql..."
echo ""

# Run the main query file
QUERY_FILE="$PROJECT_ROOT/database/queries/query_tracks.sql"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$QUERY_FILE"

