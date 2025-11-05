-- PostgreSQL schema for Kidsplaza Person Detector (channels + events)

-- Enable required extensions (safe if already installed)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Multi-tenant hierarchy
CREATE TABLE IF NOT EXISTS companies (
    company_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL,
    meta_json       JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS stores (
    store_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id      UUID REFERENCES companies(company_id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    address         TEXT,
    meta_json       JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Channels metadata
CREATE TABLE IF NOT EXISTS channels (
    channel_id      INT PRIMARY KEY,
    name            TEXT NOT NULL,
    rtsp_url        TEXT NOT NULL,
    location        TEXT,
    description     TEXT,
    features_json   JSONB,
    company_id      UUID REFERENCES companies(company_id) ON DELETE SET NULL,
    store_id        UUID REFERENCES stores(store_id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Persons (unique per-day person ids as observed; optional)
CREATE TABLE IF NOT EXISTS persons (
    person_id       TEXT PRIMARY KEY,
    first_seen_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    meta_json       JSONB
);

-- Counter events (enter/exit) per zone
CREATE TABLE IF NOT EXISTS counter_events (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    occurred_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    channel_id      INT NOT NULL REFERENCES channels(channel_id) ON DELETE CASCADE,
    zone_id         TEXT NOT NULL,
    zone_name       TEXT,
    event_type      TEXT NOT NULL CHECK (event_type IN ('enter','exit')),
    track_id        BIGINT,
    person_id       TEXT,
    frame_number    BIGINT,
    extra_json      JSONB
);

-- Detections (optional logging of raw detections)
CREATE TABLE IF NOT EXISTS detections (
    id              BIGSERIAL PRIMARY KEY,
    captured_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    channel_id      INT NOT NULL REFERENCES channels(channel_id) ON DELETE CASCADE,
    frame_number    BIGINT,
    track_id        BIGINT,
    confidence      REAL,
    bbox_x          REAL,
    bbox_y          REAL,
    bbox_w          REAL,
    bbox_h          REAL,
    gender          TEXT,
    gender_conf     REAL,
    meta_json       JSONB
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_counter_events_channel_time
    ON counter_events (channel_id, occurred_at DESC);

CREATE INDEX IF NOT EXISTS idx_counter_events_person_time
    ON counter_events (person_id, occurred_at DESC);

CREATE INDEX IF NOT EXISTS idx_detections_channel_time
    ON detections (channel_id, captured_at DESC);

CREATE INDEX IF NOT EXISTS idx_channels_updated_at
    ON channels (updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_channels_company_store
    ON channels (company_id, store_id);


