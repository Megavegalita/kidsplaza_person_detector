# Database Documentation

This directory contains database-related files for the Person Detector project.

## Structure

```
database/
├── README.md                    # This file
├── schema_phase6.sql            # Database schema definition
└── queries/                     # SQL query files
    ├── README.md               # Query documentation
    ├── check_connection.sql    # Connection verification script
    └── query_tracks.sql        # Track information queries
```

## Schema

The database schema is defined in `schema_phase6.sql`. This file creates all tables and indexes required for Phase 6 data storage.

**To initialize the database:**
```bash
psql -h localhost -p 5432 -U autoeyes -d gender_analysis -f database/schema_phase6.sql
```

## Tables

### `detections`
Stores individual person detections from video frames.

**Key Columns:**
- `timestamp` - Detection timestamp
- `camera_id` - Camera identifier
- `track_id` - Associated track ID (nullable)
- `confidence` - Detection confidence score
- `bbox_x, bbox_y, bbox_width, bbox_height` - Bounding box coordinates
- `gender` - Gender classification (M/F/null)
- `gender_confidence` - Gender classification confidence

### `tracks`
Stores track information aggregated across frames.

**Key Columns:**
- `track_id` - Unique track identifier
- `camera_id` - Camera identifier
- `start_time`, `end_time` - Track duration
- `detection_count` - Number of detections in this track
- `avg_confidence` - Average detection confidence
- `trajectory` - Track trajectory as JSONB

### `track_genders`
Stores the final gender classification for each unique track ID.

**Key Columns:**
- `camera_id`, `track_id` - Composite primary key
- `gender` - Final gender classification (M/F/null)
- `confidence` - Gender classification confidence

### `run_gender_summary`
Stores summary statistics for each video processing run.

**Key Columns:**
- `run_id` - Video processing run identifier
- `camera_id` - Camera identifier
- `unique_total` - Total unique tracks
- `male_tracks` - Number of male tracks
- `female_tracks` - Number of female tracks
- `unknown_tracks` - Number of unknown/undetermined tracks

## Queries

See `queries/README.md` for detailed documentation on available query scripts.

## Connection

- **Host**: `localhost`
- **Port**: `5432`
- **Database**: `gender_analysis`
- **User**: `autoeyes`
- **Config File**: `config/database.json`

## Helper Scripts

### Query Tracks
```bash
./scripts/query_tracks.sh
```

This script automatically:
1. Loads database connection info from `config/database.json`
2. Verifies connection and table existence
3. Runs comprehensive track queries

## Related Code

- `src/modules/database/postgres_manager.py` - PostgreSQL connection and operations
- `src/modules/database/redis_manager.py` - Redis caching
- `src/modules/database/models.py` - Data models for database operations

