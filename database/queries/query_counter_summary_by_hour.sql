-- Counter summary grouped by hour per channel within a time window
-- Params:
--   :from_ts (timestamptz)
--   :to_ts (timestamptz)
--   :channel_id (int, nullable)

SELECT
  date_trunc('hour', occurred_at) AS hour,
  channel_id,
  SUM(CASE WHEN event_type = 'enter' THEN 1 ELSE 0 END) AS enter_count,
  SUM(CASE WHEN event_type = 'exit' THEN 1 ELSE 0 END) AS exit_count
FROM counter_events
WHERE occurred_at BETWEEN :from_ts AND :to_ts
  AND (:channel_id IS NULL OR channel_id = :channel_id)
GROUP BY hour, channel_id
ORDER BY hour DESC, channel_id;


