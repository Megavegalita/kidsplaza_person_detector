# Database Queries

This directory contains SQL query files for interacting with the PostgreSQL database.

## Files

### `check_connection.sql`
Verifies database connection and checks if required tables exist. **Run this first** if you encounter connection issues.

**Usage:**
```bash
psql -h localhost -p 5432 -U autoeyes -d gender_analysis -f database/queries/check_connection.sql
```

### `query_tracks.sql`
Comprehensive query to display all track information including:
- Run gender summaries
- All track genders (detailed)
- Track stats with detection counts
- Gender distribution summary
- Detection statistics by track

**Usage:**
```bash
psql -h localhost -p 5432 -U autoeyes -d gender_analysis -f database/queries/query_tracks.sql
```

Or use the helper script:
```bash
./scripts/query_tracks.sh
```

### `dashboard_summary.sql`
**Dashboard-style comprehensive summary** with multiple sections:
0. **KEY METRICS** (⭐ PRIMARY) - Unique track counts: unique_total, unique_male, unique_female, unique_unknown
1. **Overview Statistics** - Total tracks, cameras, detections, time range
2. **Gender Distribution** - Latest run and overall statistics
3. **Track Statistics** - Aggregated track metrics
4. **Detection Statistics by Time** - Hourly breakdown (last 24h)
5. **Top Tracks** - Most active tracks by detection count
6. **Camera Statistics** - Per-camera breakdown
7. **Recent Runs Summary** - Last 10 processing runs
8. **Gender Confidence Distribution** - Confidence ranges analysis
9. **Track Duration Statistics** - Duration metrics by gender
10. **Daily Summary** - Last 7 days overview

**Usage:**
```bash
psql -h localhost -p 5432 -U autoeyes -d gender_analysis -f database/queries/dashboard_summary.sql
```

This query provides a complete dashboard view suitable for monitoring and reporting.

## Connection Details

- **Host**: `localhost`
- **Port**: `5432`
- **Database**: `gender_analysis`
- **User**: `autoeyes`
- **Connection String**: `postgresql://autoeyes@localhost:5432/gender_analysis`

## Schema

The database schema is defined in `../schema_phase6.sql`. Run this file to create all required tables:

```bash
psql -h localhost -p 5432 -U autoeyes -d gender_analysis -f database/schema_phase6.sql
```

## Tables

- `detections` - Individual person detections
- `tracks` - Track information
- `track_genders` - Gender labels per unique track ID
- `run_gender_summary` - Summary statistics per video processing run

