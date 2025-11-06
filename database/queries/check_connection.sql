-- ============================================================
-- Connection Check Script - Run this FIRST in your SQL client
-- ============================================================

-- 1. Check current connection
SELECT 
    current_database() AS current_database,
    current_schema() AS current_schema,
    current_user AS current_user;

-- 2. Check if tables exist
SELECT 
    table_schema,
    table_name,
    CASE 
        WHEN table_name IN ('run_gender_summary', 'track_genders', 'detections', 'tracks') 
        THEN '✓ EXISTS' 
        ELSE '✗ MISSING' 
    END AS status
FROM information_schema.tables 
WHERE table_name IN ('run_gender_summary', 'track_genders', 'detections', 'tracks')
ORDER BY table_name;

-- 3. List all databases (to verify you're in the right one)
SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname;

-- 4. If tables don't exist, you need to:
--    a) Switch to database: gender_analysis
--    b) Or run schema_phase6.sql to create tables

