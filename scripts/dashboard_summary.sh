#!/bin/bash
# Script to run dashboard summary query from PostgreSQL
# Usage: ./scripts/dashboard_summary.sh [config_file]

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

echo "============================================================"
echo "DASHBOARD SUMMARY"
echo "============================================================"
echo "Connecting to PostgreSQL:"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo "============================================================"
echo ""

# Verify connection
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
SELECT current_database() AS current_db, current_schema() AS current_schema;
" > /dev/null || {
    echo "Error: Failed to connect to database!"
    exit 1
}

echo "Running dashboard_summary.sql..."
echo ""

# Run the dashboard query file
QUERY_FILE="$PROJECT_ROOT/database/queries/dashboard_summary.sql"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$QUERY_FILE"

echo ""
echo "============================================================"
echo "Dashboard query completed"
echo "============================================================"

