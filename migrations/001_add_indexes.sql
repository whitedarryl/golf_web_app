-- Database optimization migration: Add indexes for better query performance
-- Run this script on your golf_clone database

-- =============================================================================
-- Add indexes to courses table
-- =============================================================================

-- Index on course_name and tournament_date for lookups
CREATE INDEX IF NOT EXISTS idx_courses_name_date
ON courses(course_name, tournament_date);

-- Index on tournament_date for date-based queries
CREATE INDEX IF NOT EXISTS idx_courses_date
ON courses(tournament_date);


-- =============================================================================
-- Add indexes to players table
-- =============================================================================

-- Index on course_id for joins and filtering
CREATE INDEX IF NOT EXISTS idx_players_course
ON players(course_id);

-- Composite index on first_name and last_name for name lookups
CREATE INDEX IF NOT EXISTS idx_players_name
ON players(first_name(50), last_name(50));

-- Composite index on course_id and full name for common query pattern
CREATE INDEX IF NOT EXISTS idx_players_course_name
ON players(course_id, first_name(50), last_name(50));


-- =============================================================================
-- Add indexes to scores table
-- =============================================================================

-- Composite index on course_id and player name (most common query pattern)
CREATE INDEX IF NOT EXISTS idx_scores_course_player
ON scores(course_id, first_name(50), last_name(50));

-- Index on total score for leaderboard queries
CREATE INDEX IF NOT EXISTS idx_scores_total
ON scores(total);

-- Index on net_score for net leaderboard queries
CREATE INDEX IF NOT EXISTS idx_scores_net
ON scores(net_score);

-- Composite index on course_id and total for filtered leaderboards
CREATE INDEX IF NOT EXISTS idx_scores_course_total
ON scores(course_id, total);

-- Composite index on course_id and net_score
CREATE INDEX IF NOT EXISTS idx_scores_course_net
ON scores(course_id, net_score);

-- Index for counting submitted scores (WHERE total IS NOT NULL)
CREATE INDEX IF NOT EXISTS idx_scores_submitted
ON scores(course_id, total);


-- =============================================================================
-- Add indexes to course_hole_handicap table
-- =============================================================================

-- Index on course_id for joins
CREATE INDEX IF NOT EXISTS idx_course_hole_course
ON course_hole_handicap(course_id);

-- Composite index on course_id and handicap_rank for ordering
CREATE INDEX IF NOT EXISTS idx_course_hole_rank
ON course_hole_handicap(course_id, handicap_rank);


-- =============================================================================
-- Add indexes to scores_archive table
-- =============================================================================

-- Index on course_id for filtering archived scores
CREATE INDEX IF NOT EXISTS idx_archive_course
ON scores_archive(course_id);

-- Index on date_played for historical queries
CREATE INDEX IF NOT EXISTS idx_archive_date
ON scores_archive(date_played);

-- Composite index on course_name and date_played for archive lookups
CREATE INDEX IF NOT EXISTS idx_archive_course_date
ON scores_archive(course_name(50), date_played);

-- Composite index on player name for historical player queries
CREATE INDEX IF NOT EXISTS idx_archive_player
ON scores_archive(first_name(50), last_name(50));


-- =============================================================================
-- Add indexes to fives table (if exists)
-- =============================================================================

-- Index on course_id for filtering
CREATE INDEX IF NOT EXISTS idx_fives_course
ON fives(course_id);

-- Index on player name for lookups
CREATE INDEX IF NOT EXISTS idx_fives_player
ON fives(first_name(50), last_name(50));


-- =============================================================================
-- Verify indexes were created
-- =============================================================================

SELECT
    TABLE_NAME,
    INDEX_NAME,
    INDEX_TYPE,
    GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) AS COLUMNS
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = 'golf_clone'
AND INDEX_NAME LIKE 'idx_%'
GROUP BY TABLE_NAME, INDEX_NAME, INDEX_TYPE
ORDER BY TABLE_NAME, INDEX_NAME;
