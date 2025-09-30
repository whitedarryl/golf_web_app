# Database Migrations

This directory contains SQL migration scripts for the Golf Web App database.

## Files

- `000_schema.sql` - Complete database schema (for fresh installations)
- `001_add_indexes.sql` - Adds performance indexes to existing tables

## Running Migrations

### For a Fresh Installation

If you're setting up the database for the first time:

```bash
mysql -u root -p golf_clone < migrations/000_schema.sql
```

### For an Existing Database

If you already have data and want to add indexes:

```bash
mysql -u root -p golf_clone < migrations/001_add_indexes.sql
```

## Migration Order

Always run migrations in numerical order:
1. `000_schema.sql` (fresh install only)
2. `001_add_indexes.sql` (can be run on existing database)

## Index Benefits

The indexes added in `001_add_indexes.sql` will improve performance for:

- **Player lookups** by name and course
- **Leaderboard queries** sorted by score
- **Historical data** queries by date
- **Score submissions** and updates
- **Course filtering** across all tables

## Verifying Indexes

To verify indexes were created successfully:

```sql
SELECT
    TABLE_NAME,
    INDEX_NAME,
    GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) AS COLUMNS
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = 'golf_clone' AND INDEX_NAME LIKE 'idx_%'
GROUP BY TABLE_NAME, INDEX_NAME
ORDER BY TABLE_NAME, INDEX_NAME;
```

## Rollback

To remove the indexes added in `001_add_indexes.sql`:

```sql
-- Example for scores table
DROP INDEX idx_scores_course_player ON scores;
DROP INDEX idx_scores_total ON scores;
-- ... continue for all indexes
```

## Creating New Migrations

When creating new migration files:

1. Use sequential numbering: `002_description.sql`, `003_description.sql`, etc.
2. Include comments explaining what the migration does
3. Make migrations idempotent when possible (use `IF NOT EXISTS`)
4. Test on a development database first
5. Update this README with the new migration
