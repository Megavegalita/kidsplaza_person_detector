-- ============================================================
-- Query to show all track information in PostgreSQL
-- ============================================================
-- IMPORTANT: Make sure you're connected to database: gender_analysis
-- Connection string: postgresql://autoeyes@localhost:5432/gender_analysis
-- ============================================================

-- Check current database and schema
SELECT current_database() AS current_db, current_schema() AS current_schema;

-- Verify tables exist (should show 4 tables if connected correctly)
SELECT table_schema, table_name 
FROM information_schema.tables 
WHERE table_name IN ('run_gender_summary', 'track_genders', 'detections', 'tracks')
ORDER BY table_name;

-- If above returns 0 rows, you're in the WRONG database!
-- Switch to database: gender_analysis

-- 1. Run Gender Summary
SELECT '=== RUN GENDER SUMMARY ===' AS section;
SELECT * FROM public.run_gender_summary ORDER BY id DESC;

-- 2. All Track Genders (detailed)
SELECT '' AS blank;
SELECT '=== ALL TRACK GENDERS ===' AS section;
SELECT 
    track_id,
    gender,
    confidence,
    created_at,
    updated_at
FROM public.track_genders
ORDER BY track_id;

-- 3. Track Stats with Detection Counts
SELECT '' AS blank;
SELECT '=== TRACK STATS (with detection counts) ===' AS section;
SELECT 
    tg.track_id,
    tg.gender,
    tg.confidence AS track_gender_confidence,
    COUNT(d.id) AS detection_count,
    MIN(d.frame_number) AS first_frame,
    MAX(d.frame_number) AS last_frame,
    MIN(d.timestamp) AS first_seen,
    MAX(d.timestamp) AS last_seen,
    ROUND(AVG(d.confidence)::numeric, 4) AS avg_detection_confidence,
    ROUND(AVG(d.gender_confidence)::numeric, 4) AS avg_gender_confidence
FROM public.track_genders tg
LEFT JOIN public.detections d ON d.track_id = tg.track_id AND d.camera_id = tg.camera_id
GROUP BY tg.track_id, tg.gender, tg.confidence
ORDER BY tg.track_id;

-- 4. Gender Distribution Summary
SELECT '' AS blank;
SELECT '=== GENDER DISTRIBUTION SUMMARY ===' AS section;
SELECT 
    gender,
    COUNT(*) AS track_count,
    ROUND(AVG(confidence)::numeric, 4) AS avg_confidence,
    ROUND(MIN(confidence)::numeric, 4) AS min_confidence,
    ROUND(MAX(confidence)::numeric, 4) AS max_confidence
FROM public.track_genders
GROUP BY gender
ORDER BY track_count DESC;

-- 5. Detection Statistics by Track
SELECT '' AS blank;
SELECT '=== DETECTION STATISTICS BY TRACK ===' AS section;
SELECT 
    track_id,
    COUNT(*) AS total_detections,
    COUNT(CASE WHEN gender = 'M' THEN 1 END) AS male_detections,
    COUNT(CASE WHEN gender = 'F' THEN 1 END) AS female_detections,
    COUNT(CASE WHEN gender IS NULL OR gender = '' THEN 1 END) AS unknown_detections,
    ROUND(AVG(confidence)::numeric, 4) AS avg_detection_confidence,
    ROUND(AVG(gender_confidence)::numeric, 4) AS avg_gender_confidence
FROM public.detections
WHERE track_id IS NOT NULL
GROUP BY track_id
ORDER BY track_id;

