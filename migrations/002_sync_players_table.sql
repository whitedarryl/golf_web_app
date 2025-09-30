-- Migration to sync players table with scores table
-- This fixes the issue where players exist in scores but not in players table

-- Step 1: Update NULL course_ids in players table to match the latest course
UPDATE players
SET course_id = (SELECT MAX(course_id) FROM courses)
WHERE course_id IS NULL;

-- Step 2: Insert any players from scores table that don't exist in players table
-- For each course, add missing players
INSERT INTO players (first_name, last_name, course_id)
SELECT DISTINCT s.first_name, s.last_name, s.course_id
FROM scores s
WHERE NOT EXISTS (
    SELECT 1 FROM players p
    WHERE p.first_name = s.first_name
    AND p.last_name = s.last_name
    AND p.course_id = s.course_id
)
AND s.first_name IS NOT NULL
AND s.last_name IS NOT NULL;

-- Step 3: Verify the counts
SELECT
    'Players Table' as Source,
    course_id,
    COUNT(*) as count
FROM players
GROUP BY course_id

UNION ALL

SELECT
    'Scores Table' as Source,
    course_id,
    COUNT(*) as count
FROM scores
GROUP BY course_id
ORDER BY course_id, Source;
