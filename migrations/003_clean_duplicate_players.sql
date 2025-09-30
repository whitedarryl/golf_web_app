-- Migration to clean up duplicate players with NULL last names
-- This fixes players stored in old format (full name in first_name column)

-- Step 1: Delete players where last_name is NULL or empty
-- These are duplicates from the old system where full names were stored in first_name
DELETE FROM players
WHERE last_name IS NULL OR last_name = '';

-- Step 2: Verify no NULL last names remain
SELECT
    'Players with NULL last_name' as check_type,
    COUNT(*) as count
FROM players
WHERE last_name IS NULL OR last_name = '';

-- Step 3: Verify final counts
SELECT
    course_id,
    COUNT(*) as player_count
FROM players
GROUP BY course_id
ORDER BY course_id;
