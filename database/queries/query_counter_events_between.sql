-- Detailed counter events between a time range
-- Params:
--   :from_ts (timestamptz)
--   :to_ts (timestamptz)
--   :channel_id (int, nullable)

SELECT
  occurred_at,
  channel_id,
  zone_id,
  zone_name,
  event_type,
  track_id,
  person_id,
  frame_number,
  extra_json
FROM counter_events
WHERE occurred_at BETWEEN :from_ts AND :to_ts
  AND (:channel_id IS NULL OR channel_id = :channel_id)
ORDER BY occurred_at DESC;


