-- Upsert a channel metadata row
INSERT INTO channels (
    channel_id, name, rtsp_url, location, description, features_json, updated_at
) VALUES (
    :channel_id, :name, :rtsp_url, :location, :description, :features_json::jsonb, NOW()
)
ON CONFLICT (channel_id) DO UPDATE SET
    name = EXCLUDED.name,
    rtsp_url = EXCLUDED.rtsp_url,
    location = EXCLUDED.location,
    description = EXCLUDED.description,
    features_json = EXCLUDED.features_json,
    updated_at = NOW();



