CREATE TABLE IF NOT EXISTS detections (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMP NOT NULL,
  camera_id INTEGER NOT NULL,
  channel_id INTEGER NOT NULL,
  detection_id VARCHAR(64) NOT NULL,
  track_id INTEGER,
  confidence FLOAT NOT NULL,
  bbox_x INTEGER NOT NULL,
  bbox_y INTEGER NOT NULL,
  bbox_width INTEGER NOT NULL,
  bbox_height INTEGER NOT NULL,
  gender VARCHAR(8),
  gender_confidence FLOAT,
  frame_number INTEGER NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_detections_timestamp ON detections(timestamp);
CREATE INDEX IF NOT EXISTS idx_detections_track_id ON detections(track_id);
CREATE INDEX IF NOT EXISTS idx_detections_camera_id ON detections(camera_id);

CREATE TABLE IF NOT EXISTS tracks (
  id SERIAL PRIMARY KEY,
  track_id INTEGER NOT NULL,
  camera_id INTEGER NOT NULL,
  start_time TIMESTAMP NOT NULL,
  end_time TIMESTAMP,
  detection_count INTEGER NOT NULL,
  avg_confidence FLOAT NOT NULL,
  trajectory JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(track_id, camera_id)
);
CREATE INDEX IF NOT EXISTS idx_tracks_camera_id ON tracks(camera_id);
CREATE INDEX IF NOT EXISTS idx_tracks_track_id ON tracks(track_id);

-- Track genders per unique id
CREATE TABLE IF NOT EXISTS track_genders (
  camera_id INTEGER NOT NULL,
  track_id INTEGER NOT NULL,
  gender VARCHAR(8),
  confidence FLOAT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (camera_id, track_id)
);
CREATE INDEX IF NOT EXISTS idx_track_genders_gender ON track_genders(gender);

-- Per-run unique-id gender summary
CREATE TABLE IF NOT EXISTS run_gender_summary (
  id SERIAL PRIMARY KEY,
  run_id VARCHAR(128) NOT NULL,
  camera_id INTEGER NOT NULL,
  unique_total INTEGER NOT NULL,
  male_tracks INTEGER NOT NULL,
  female_tracks INTEGER NOT NULL,
  unknown_tracks INTEGER NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_run_gender_summary_run ON run_gender_summary(run_id);
