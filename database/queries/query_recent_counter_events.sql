-- Recent counter events for a channel (last 1 hour)
SELECT occurred_at,
       channel_id,
       zone_id,
       zone_name,
       event_type,
       track_id,
       person_id,
       frame_number,
       extra_json
FROM counter_events
WHERE channel_id = :channel_id
  AND occurred_at >= NOW() - INTERVAL '1 hour'
ORDER BY occurred_at DESC
LIMIT 200;




