-- ============================================================
-- Dashboard Summary Query - Comprehensive statistics overview
-- ============================================================
-- This query provides a complete dashboard view of all data
-- ============================================================

-- ============================================================
-- 0. KEY METRICS (Unique Track Counts) - PRIMARY METRICS
-- ============================================================
SELECT '=== KEY METRICS: UNIQUE TRACK COUNTS ===' AS section;

SELECT 
    COUNT(*) AS unique_total,
    COUNT(CASE WHEN gender = 'M' THEN 1 END) AS unique_male,
    COUNT(CASE WHEN gender = 'F' THEN 1 END) AS unique_female,
    COUNT(CASE WHEN gender IS NULL OR gender = '' THEN 1 END) AS unique_unknown,
    ROUND((COUNT(CASE WHEN gender = 'M' THEN 1 END)::numeric / NULLIF(COUNT(*), 0) * 100), 2) AS male_percentage,
    ROUND((COUNT(CASE WHEN gender = 'F' THEN 1 END)::numeric / NULLIF(COUNT(*), 0) * 100), 2) AS female_percentage
FROM public.track_genders;

-- ============================================================
-- 1. OVERVIEW STATISTICS
-- ============================================================
SELECT '' AS blank;
SELECT '=== OVERVIEW STATISTICS ===' AS section;

SELECT 
    COUNT(DISTINCT d.track_id) AS total_unique_tracks,
    COUNT(DISTINCT d.camera_id) AS total_cameras,
    COUNT(*) AS total_detections,
    COUNT(DISTINCT DATE(d.timestamp)) AS total_days,
    MIN(d.timestamp) AS first_detection,
    MAX(d.timestamp) AS last_detection,
    (SELECT COUNT(DISTINCT run_id) FROM public.run_gender_summary) AS total_runs
FROM public.detections d;

-- ============================================================
-- 2. GENDER DISTRIBUTION (Current Session)
-- ============================================================
SELECT '' AS blank;
SELECT '=== GENDER DISTRIBUTION (Latest Run) ===' AS section;

SELECT 
    rgs.run_id,
    rgs.unique_total,
    rgs.male_tracks,
    rgs.female_tracks,
    rgs.unknown_tracks,
    ROUND((rgs.male_tracks::numeric / NULLIF(rgs.unique_total, 0) * 100), 2) AS male_percentage,
    ROUND((rgs.female_tracks::numeric / NULLIF(rgs.unique_total, 0) * 100), 2) AS female_percentage,
    ROUND((rgs.unknown_tracks::numeric / NULLIF(rgs.unique_total, 0) * 100), 2) AS unknown_percentage,
    rgs.created_at AS run_time
FROM public.run_gender_summary rgs
ORDER BY rgs.created_at DESC
LIMIT 5;

-- ============================================================
-- 3. OVERALL GENDER DISTRIBUTION (All Tracks)
-- ============================================================
SELECT '' AS blank;
SELECT '=== OVERALL GENDER DISTRIBUTION (All Tracks) ===' AS section;

SELECT 
    gender,
    COUNT(*) AS track_count,
    ROUND(AVG(confidence)::numeric, 4) AS avg_confidence,
    ROUND(MIN(confidence)::numeric, 4) AS min_confidence,
    ROUND(MAX(confidence)::numeric, 4) AS max_confidence,
    ROUND((COUNT(*)::numeric / NULLIF((SELECT COUNT(*) FROM public.track_genders), 0) * 100), 2) AS percentage
FROM public.track_genders
GROUP BY gender
ORDER BY track_count DESC;

-- ============================================================
-- 4. TRACK STATISTICS
-- ============================================================
SELECT '' AS blank;
SELECT '=== TRACK STATISTICS ===' AS section;

SELECT 
    COUNT(DISTINCT t.track_id) AS total_tracks,
    SUM(t.detection_count) AS total_detections_in_tracks,
    ROUND(AVG(t.detection_count)::numeric, 2) AS avg_detections_per_track,
    ROUND(AVG(t.avg_confidence)::numeric, 4) AS avg_track_confidence,
    MIN(t.start_time) AS earliest_track,
    MAX(t.end_time) AS latest_track_end
FROM public.tracks t;

-- ============================================================
-- 5. DETECTION STATISTICS BY TIME PERIOD
-- ============================================================
SELECT '' AS blank;
SELECT '=== DETECTION STATISTICS BY HOUR (Last 24 Hours) ===' AS section;

SELECT 
    DATE_TRUNC('hour', d.timestamp) AS hour,
    COUNT(*) AS detections_count,
    COUNT(DISTINCT d.track_id) AS unique_tracks,
    ROUND(AVG(d.confidence)::numeric, 4) AS avg_confidence,
    COUNT(CASE WHEN d.gender = 'M' THEN 1 END) AS male_detections,
    COUNT(CASE WHEN d.gender = 'F' THEN 1 END) AS female_detections
FROM public.detections d
WHERE d.timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', d.timestamp)
ORDER BY hour DESC
LIMIT 24;

-- ============================================================
-- 6. TOP TRACKS BY DETECTION COUNT
-- ============================================================
SELECT '' AS blank;
SELECT '=== TOP 10 TRACKS BY DETECTION COUNT ===' AS section;

SELECT 
    tg.track_id,
    tg.gender,
    tg.confidence AS track_gender_confidence,
    COUNT(d.id) AS total_detections,
    ROUND(AVG(d.confidence)::numeric, 4) AS avg_detection_confidence,
    ROUND(AVG(d.gender_confidence)::numeric, 4) AS avg_gender_confidence,
    MIN(d.timestamp) AS first_seen,
    MAX(d.timestamp) AS last_seen,
    MAX(d.timestamp) - MIN(d.timestamp) AS duration
FROM public.track_genders tg
LEFT JOIN public.detections d ON d.track_id = tg.track_id AND d.camera_id = tg.camera_id
GROUP BY tg.track_id, tg.gender, tg.confidence
ORDER BY total_detections DESC
LIMIT 10;

-- ============================================================
-- 7. CAMERA STATISTICS
-- ============================================================
SELECT '' AS blank;
SELECT '=== CAMERA STATISTICS ===' AS section;

SELECT 
    d.camera_id,
    COUNT(DISTINCT d.track_id) AS unique_tracks,
    COUNT(*) AS total_detections,
    COUNT(CASE WHEN d.gender = 'M' THEN 1 END) AS male_detections,
    COUNT(CASE WHEN d.gender = 'F' THEN 1 END) AS female_detections,
    ROUND(AVG(d.confidence)::numeric, 4) AS avg_confidence,
    MIN(d.timestamp) AS first_detection,
    MAX(d.timestamp) AS last_detection
FROM public.detections d
GROUP BY d.camera_id
ORDER BY d.camera_id;

-- ============================================================
-- 8. RECENT RUNS SUMMARY
-- ============================================================
SELECT '' AS blank;
SELECT '=== RECENT RUNS SUMMARY ===' AS section;

SELECT 
    run_id,
    camera_id,
    unique_total,
    male_tracks,
    female_tracks,
    unknown_tracks,
    ROUND((male_tracks::numeric / NULLIF(unique_total, 0) * 100), 2) AS male_pct,
    ROUND((female_tracks::numeric / NULLIF(unique_total, 0) * 100), 2) AS female_pct,
    created_at AS run_time
FROM public.run_gender_summary
ORDER BY created_at DESC
LIMIT 10;

-- ============================================================
-- 9. GENDER CONFIDENCE DISTRIBUTION
-- ============================================================
SELECT '' AS blank;
SELECT '=== GENDER CONFIDENCE DISTRIBUTION ===' AS section;

SELECT 
    CASE 
        WHEN confidence >= 0.9 THEN 'Very High (≥0.9)'
        WHEN confidence >= 0.8 THEN 'High (0.8-0.9)'
        WHEN confidence >= 0.7 THEN 'Medium (0.7-0.8)'
        WHEN confidence >= 0.6 THEN 'Low (0.6-0.7)'
        ELSE 'Very Low (<0.6)'
    END AS confidence_range,
    gender,
    COUNT(*) AS count,
    ROUND(AVG(confidence)::numeric, 4) AS avg_confidence
FROM public.track_genders
WHERE gender IS NOT NULL
GROUP BY 
    CASE 
        WHEN confidence >= 0.9 THEN 'Very High (≥0.9)'
        WHEN confidence >= 0.8 THEN 'High (0.8-0.9)'
        WHEN confidence >= 0.7 THEN 'Medium (0.7-0.8)'
        WHEN confidence >= 0.6 THEN 'Low (0.6-0.7)'
        ELSE 'Very Low (<0.6)'
    END,
    gender
ORDER BY confidence_range, gender;

-- ============================================================
-- 10. TRACK DURATION STATISTICS
-- ============================================================
SELECT '' AS blank;
SELECT '=== TRACK DURATION STATISTICS ===' AS section;

SELECT 
    tg.gender,
    COUNT(DISTINCT tg.track_id) AS track_count,
    ROUND(AVG(t.detection_count)::numeric, 2) AS avg_detections_per_track,
    ROUND(AVG(EXTRACT(EPOCH FROM (t.end_time - t.start_time)))::numeric, 2) AS avg_duration_seconds,
    ROUND(MIN(EXTRACT(EPOCH FROM (t.end_time - t.start_time)))::numeric, 2) AS min_duration_seconds,
    ROUND(MAX(EXTRACT(EPOCH FROM (t.end_time - t.start_time)))::numeric, 2) AS max_duration_seconds
FROM public.track_genders tg
LEFT JOIN public.tracks t ON t.track_id = tg.track_id AND t.camera_id = tg.camera_id
WHERE t.end_time IS NOT NULL
GROUP BY tg.gender
ORDER BY tg.gender;

-- ============================================================
-- 11. DAILY SUMMARY (Last 7 Days)
-- ============================================================
SELECT '' AS blank;
SELECT '=== DAILY SUMMARY (Last 7 Days) ===' AS section;

SELECT 
    DATE(d.timestamp) AS date,
    COUNT(DISTINCT d.track_id) AS unique_tracks,
    COUNT(*) AS total_detections,
    COUNT(CASE WHEN d.gender = 'M' THEN 1 END) AS male_detections,
    COUNT(CASE WHEN d.gender = 'F' THEN 1 END) AS female_detections,
    ROUND(AVG(d.confidence)::numeric, 4) AS avg_detection_confidence
FROM public.detections d
WHERE d.timestamp >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(d.timestamp)
ORDER BY date DESC;

