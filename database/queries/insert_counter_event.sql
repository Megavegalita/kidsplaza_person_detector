-- Insert a counter event (enter/exit)
INSERT INTO counter_events (
    occurred_at, channel_id, zone_id, zone_name, event_type, track_id, person_id, frame_number, extra_json
) VALUES (
    NOW(), :channel_id, :zone_id, :zone_name, :event_type, :track_id, :person_id, :frame_number, :extra_json::jsonb
)
RETURNING id;



